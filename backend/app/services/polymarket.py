"""Polymarket API client service."""

import asyncio
import hmac
import hashlib
import time
from decimal import Decimal
from typing import Any

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

# Polymarket Gamma API leaderboard endpoint
GAMMA_LEADERBOARD_URL = "https://gamma-api.polymarket.com/leaderboard"


class PolymarketService:
    """Service for interacting with Polymarket APIs."""

    def __init__(self):
        self.clob_host = settings.polymarket_host
        self.gamma_host = "https://gamma-api.polymarket.com"
        self.data_api_host = "https://data-api.polymarket.com"
        self.api_key = settings.polymarket_api_key
        self.api_secret = settings.polymarket_api_secret
        self.api_passphrase = settings.polymarket_api_passphrase

    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        path: str,
        body: str = ""
    ) -> str:
        """Generate HMAC signature for authenticated requests."""
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_auth_headers(self, method: str, path: str, body: str = "") -> dict:
        """Get headers for authenticated API requests."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path, body)

        return {
            "POLY_API_KEY": self.api_key,
            "POLY_SIGNATURE": signature,
            "POLY_TIMESTAMP": timestamp,
            "POLY_PASSPHRASE": self.api_passphrase,
            "Content-Type": "application/json",
        }

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get list of markets from Gamma API.

        Args:
            limit: Number of markets to return
            offset: Offset for pagination
            active: Filter for active markets only

        Returns:
            List of market data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gamma_host}/markets",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "active": str(active).lower(),
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch markets", error=str(e))
            return []

    async def get_market(self, market_id: str) -> dict[str, Any] | None:
        """
        Get a specific market by ID.

        Args:
            market_id: The market's condition ID

        Returns:
            Market data or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gamma_host}/markets/{market_id}",
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch market", market_id=market_id, error=str(e))
            return None

    async def get_trader_positions(
        self,
        wallet_address: str
    ) -> list[dict[str, Any]]:
        """
        Get positions for a specific trader.

        Args:
            wallet_address: The trader's wallet address

        Returns:
            List of position data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gamma_host}/positions",
                    params={"user": wallet_address.lower()},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch trader positions",
                wallet=wallet_address,
                error=str(e)
            )
            return []

    async def get_trader_history(
        self,
        wallet_address: str,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get trade history for a specific trader.

        Args:
            wallet_address: The trader's wallet address
            limit: Maximum number of trades to return

        Returns:
            List of trade data
        """
        try:
            path = f"/data/trades"
            headers = self._get_auth_headers("GET", path)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.clob_host}{path}",
                    params={
                        "maker_address": wallet_address.lower(),
                        "limit": limit,
                    },
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch trader history",
                wallet=wallet_address,
                error=str(e)
            )
            return []

    async def get_orderbook(
        self,
        token_id: str
    ) -> dict[str, Any] | None:
        """
        Get orderbook for a specific token.

        Args:
            token_id: The token ID

        Returns:
            Orderbook data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.clob_host}/book",
                    params={"token_id": token_id},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch orderbook", token_id=token_id, error=str(e))
            return None

    async def get_price(
        self,
        token_id: str
    ) -> Decimal | None:
        """
        Get current midpoint price for a token.

        Args:
            token_id: The token ID

        Returns:
            Current price or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.clob_host}/midpoint",
                    params={"token_id": token_id},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return Decimal(str(data.get("mid", 0)))
        except httpx.HTTPError as e:
            logger.error("Failed to fetch price", token_id=token_id, error=str(e))
            return None

    async def get_market_price(
        self,
        market_id: str
    ) -> dict[str, Any] | None:
        """
        Get current YES and NO prices for a market.

        Args:
            market_id: The market's condition ID

        Returns:
            Dict with yes_price and no_price, or None if unavailable
        """
        try:
            market = await self.get_market(market_id)
            if not market:
                return None

            # Extract prices from market data
            # Gamma API returns outcomePrices as a list [yes_price, no_price]
            outcome_prices = market.get("outcomePrices", [])
            if len(outcome_prices) >= 2:
                return {
                    "yes_price": float(outcome_prices[0]),
                    "no_price": float(outcome_prices[1]),
                    "market_id": market_id,
                }

            # Fallback: try to get from tokens
            tokens = market.get("tokens", [])
            if len(tokens) >= 2:
                return {
                    "yes_price": float(tokens[0].get("price", 0)),
                    "no_price": float(tokens[1].get("price", 0)),
                    "market_id": market_id,
                }

            return None
        except Exception as e:
            logger.error("Failed to fetch market price", market_id=market_id, error=str(e))
            return None

    async def get_leaderboard(
        self,
        limit: int = 50,
        time_period: str = "ALL",
        order_by: str = "PNL"
    ) -> list[dict[str, Any]]:
        """
        Get top traders leaderboard from Polymarket Data API.

        Args:
            limit: Number of traders to return (max 50)
            time_period: DAY, WEEK, MONTH, or ALL
            order_by: PNL or VOL

        Returns:
            List of trader data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.data_api_host}/v1/leaderboard",
                    params={
                        "limit": min(limit, 50),
                        "timePeriod": time_period,
                        "orderBy": order_by,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch leaderboard", error=str(e))
            return []

    async def get_top_traders_with_stats(
        self,
        limit: int = 50,
        min_profit: float = 0,
        time_period: str = "MONTH",
        min_pnl_positive: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get top traders with calculated statistics from Polymarket Data API.

        Args:
            limit: Number of traders to return
            min_profit: Minimum profit filter
            time_period: DAY, WEEK, MONTH, or ALL (default MONTH for 30-day activity)
            min_pnl_positive: Only show traders with positive PnL

        Returns:
            List of traders with stats
        """
        try:
            async with httpx.AsyncClient() as client:
                # Fetch leaderboard from data-api with MONTH period for recent activity
                response = await client.get(
                    f"{self.data_api_host}/v1/leaderboard",
                    params={
                        "limit": min(limit * 2, 50),  # Fetch more to filter
                        "timePeriod": time_period,
                        "orderBy": "PNL",
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                leaderboard = response.json()

                traders = []
                for entry in leaderboard:
                    pnl = float(entry.get("pnl", 0))

                    # Filter by minimum profit
                    if pnl < min_profit:
                        continue

                    # Filter for positive PnL only (proxy for "winning" traders)
                    if min_pnl_positive and pnl <= 0:
                        continue

                    traders.append({
                        "wallet_address": entry.get("proxyWallet", "").lower(),
                        "display_name": entry.get("userName"),
                        "profit": pnl,
                        "volume": float(entry.get("vol", 0)),
                        "trades_count": 0,  # Not provided in leaderboard API
                        "win_rate": 0,  # Not provided - use PnL as proxy
                        "positions_count": 0,
                        "rank": int(entry.get("rank", 0)) if entry.get("rank") else None,
                        "avatar_url": entry.get("profileImage"),
                    })

                    if len(traders) >= limit:
                        break

                return traders
        except httpx.HTTPError as e:
            logger.error("Failed to fetch top traders", error=str(e))
            return []

    async def discover_profitable_traders(
        self,
        min_win_rate: float = 55.0,
        min_trades: int = 20,
        limit: int = 30
    ) -> list[dict[str, Any]]:
        """
        Discover profitable traders from Polymarket based on criteria.

        Returns top traders by profit from the leaderboard.
        Note: win_rate and trades_count filtering is not available
        from the public API, so returns top profit traders.

        Args:
            min_win_rate: Minimum win rate percentage (not used - API limitation)
            min_trades: Minimum number of trades (not used - API limitation)
            limit: Maximum traders to return

        Returns:
            List of top profitable traders
        """
        try:
            # Fetch top traders sorted by profit
            raw_traders = await self.get_top_traders_with_stats(
                limit=min(limit, 50),
                min_profit=100  # Minimum $100 profit
            )

            # Sort by profit (already sorted by API, but ensure)
            raw_traders.sort(key=lambda x: x["profit"], reverse=True)

            return raw_traders[:limit]
        except Exception as e:
            logger.error("Failed to discover traders", error=str(e))
            return []

    async def lookup_trader_by_address(
        self,
        wallet_address: str
    ) -> dict[str, Any] | None:
        """
        Look up a specific trader by their wallet address using the Data API.

        Args:
            wallet_address: The trader's wallet address

        Returns:
            Dict with trader stats or None if not found
        """
        try:
            wallet = wallet_address.lower()

            async with httpx.AsyncClient() as client:
                # Use data-api with user filter
                response = await client.get(
                    f"{self.data_api_host}/v1/leaderboard",
                    params={
                        "user": wallet,
                        "timePeriod": "ALL",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    logger.info("No data found for wallet", wallet=wallet)
                    return None

                entry = data[0]
                return {
                    "wallet_address": entry.get("proxyWallet", wallet).lower(),
                    "display_name": entry.get("userName"),
                    "profit": float(entry.get("pnl", 0)),
                    "volume": float(entry.get("vol", 0)),
                    "trades_count": 0,  # Not available from this API
                    "win_rate": 0,  # Not available from this API
                    "positions_count": 0,
                    "rank": int(entry.get("rank", 0)) if entry.get("rank") else None,
                    "avatar_url": entry.get("profileImage"),
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error("Failed to lookup trader", wallet=wallet_address, error=str(e))
            return None
        except Exception as e:
            logger.error("Failed to lookup trader", wallet=wallet_address, error=str(e))
            return None

    async def get_trader_activity(
        self,
        wallet_address: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get trading activity/history for a specific trader.

        Args:
            wallet_address: The trader's wallet address
            limit: Maximum number of activities to return

        Returns:
            List of activity/trade data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.data_api_host}/activity",
                    params={
                        "user": wallet_address.lower(),
                        "limit": limit,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                activities = response.json()

                # Format activities for frontend
                formatted = []
                for act in activities:
                    if act.get("type") == "TRADE":
                        formatted.append({
                            "id": act.get("transactionHash", ""),
                            "timestamp": act.get("timestamp", 0),
                            "type": act.get("type", ""),
                            "side": act.get("side", ""),
                            "size": float(act.get("size", 0)),
                            "usdc_size": float(act.get("usdcSize", 0)),
                            "price": float(act.get("price", 0)),
                            "market_title": act.get("title", ""),
                            "market_slug": act.get("slug", ""),
                            "event_slug": act.get("eventSlug", ""),
                            "outcome": act.get("outcome", ""),
                            "icon": act.get("icon", ""),
                        })

                return formatted
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch trader activity",
                wallet=wallet_address,
                error=str(e)
            )
            return []

    async def search_traders(
        self,
        query: str,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search traders by wallet address prefix or display name.

        If query looks like an Ethereum address (starts with 0x),
        performs a direct lookup. Otherwise searches the leaderboard
        for matching display names.

        Args:
            query: Search query (address or name)
            limit: Maximum results to return

        Returns:
            List of matching traders
        """
        try:
            results = []

            # If query looks like an address, do direct lookup
            if query.startswith("0x") or query.startswith("0X"):
                # Could be a full address or partial
                if len(query) == 42:
                    # Full address - direct lookup
                    trader = await self.lookup_trader_by_address(query)
                    if trader:
                        results.append(trader)
                else:
                    # Partial address - search leaderboard
                    leaderboard = await self.get_top_traders_with_stats(
                        limit=200,
                        min_profit=0
                    )
                    query_lower = query.lower()
                    results = [
                        t for t in leaderboard
                        if t["wallet_address"].startswith(query_lower)
                    ][:limit]
            else:
                # Search by display name in leaderboard
                leaderboard = await self.get_top_traders_with_stats(
                    limit=200,
                    min_profit=0
                )
                query_lower = query.lower()
                results = [
                    t for t in leaderboard
                    if t.get("display_name") and
                    query_lower in t["display_name"].lower()
                ][:limit]

            return results
        except Exception as e:
            logger.error("Failed to search traders", query=query, error=str(e))
            return []


# Singleton instance
polymarket_service = PolymarketService()
