"""Copy trading configuration router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.copy_config import CopyConfig
from app.schemas.copy_config import (
    CopyConfigCreate,
    CopyConfigUpdate,
    CopyConfigResponse,
    CopyConfigListResponse,
)
from app.schemas.position import PositionListResponse
from app.middleware.auth import get_current_user
from app.services.copy_service import copy_service

router = APIRouter(prefix="/api/copies", tags=["copy-trading"])


@router.get("", response_model=CopyConfigListResponse)
async def list_copies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all copy configurations for the current user.
    """
    configs = await copy_service.get_user_copies_with_traders(db, current_user.id)

    return CopyConfigListResponse(
        copies=[
            copy_service.build_copy_response(config, trader)
            for config, trader in configs
        ],
        total=len(configs),
    )


@router.post("", response_model=CopyConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_copy(
    data: CopyConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new copy configuration to start copying a trader.

    The configuration specifies:
    - trader_address: The trader to copy
    - allocation: Total USDC to allocate
    - max_position_size: Maximum size per trade
    - copy_ratio: Percentage of trader's position to mirror
    - stop_loss_percentage: Automatic stop loss
    - take_profit_percentage: Automatic take profit
    """
    # Check if already copying this trader
    if await copy_service.check_existing_copy(db, current_user.id, data.trader_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already copying this trader"
        )

    # Create copy configuration
    copy_config = CopyConfig(
        user_id=current_user.id,
        trader_address=data.trader_address.lower(),
        allocation=data.allocation,
        remaining_allocation=data.allocation,
        max_position_size=data.max_position_size,
        copy_ratio=data.copy_ratio,
        stop_loss_percentage=data.stop_loss_percentage,
        take_profit_percentage=data.take_profit_percentage,
        auto_copy_new=data.auto_copy_new,
        mirror_close=data.mirror_close,
        notify_on_copy=data.notify_on_copy,
    )
    db.add(copy_config)
    await db.commit()
    await db.refresh(copy_config)

    # Get trader info
    trader = await copy_service.get_trader_by_address(db, data.trader_address)

    return copy_service.build_copy_response(copy_config, trader)


@router.get("/{copy_id}", response_model=CopyConfigResponse)
async def get_copy(
    copy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific copy configuration by ID.
    """
    result = await copy_service.get_copy_with_trader(db, copy_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy configuration not found"
        )

    config, trader = result
    return copy_service.build_copy_response(config, trader)


@router.put("/{copy_id}", response_model=CopyConfigResponse)
async def update_copy(
    copy_id: UUID,
    data: CopyConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a copy configuration.

    Only the provided fields will be updated.
    """
    copy_config = await copy_service.get_copy_by_id(db, copy_id, current_user.id)

    if not copy_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy configuration not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle allocation change - adjust remaining allocation proportionally
    if "allocation" in update_data:
        copy_config.remaining_allocation = copy_service.calculate_remaining_allocation_on_update(
            current_allocation=copy_config.allocation,
            current_remaining=copy_config.remaining_allocation,
            new_allocation=update_data["allocation"]
        )

    for field, value in update_data.items():
        setattr(copy_config, field, value)

    await db.commit()
    await db.refresh(copy_config)

    # Get trader info
    trader = await copy_service.get_trader_by_address(db, copy_config.trader_address)

    return copy_service.build_copy_response(copy_config, trader)


@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_copy(
    copy_id: UUID,
    close_positions: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a copy configuration and stop copying the trader.

    Args:
        copy_id: The copy configuration ID
        close_positions: If true, also close all open positions (default: false)

    Note: By default, existing positions are left open.
    Use close_positions=true to also close all positions from this copy.
    """
    copy_config = await copy_service.get_copy_by_id(db, copy_id, current_user.id)

    if not copy_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy configuration not found"
        )

    # Optionally close open positions using service layer
    if close_positions:
        await copy_service.close_positions_for_copy(db, copy_id)

    await db.delete(copy_config)
    await db.commit()

    return None


@router.get("/{copy_id}/trades", response_model=PositionListResponse)
async def get_copy_trades(
    copy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all positions created from this copy configuration.
    """
    # Verify ownership
    copy_config = await copy_service.get_copy_by_id(db, copy_id, current_user.id)

    if not copy_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy configuration not found"
        )

    # Get positions
    positions = await copy_service.get_copy_positions(db, copy_id)

    return PositionListResponse(
        positions=[
            copy_service.build_position_response(p)
            for p in positions
        ],
        total=len(positions),
    )
