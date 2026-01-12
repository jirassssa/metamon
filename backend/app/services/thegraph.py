"""The Graph service for fetching Polymarket on-chain data."""

from decimal import Decimal
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

# The Graph endpoint for Polymarket on Polygon
THEGRAPH_POLYMARKET_URL = "https://api.thegraph.com/subgraphs/name/polymarket/matic-v2"
# Alternative endpoint for newer deployments
THEGRAPH_POLYMARKET_ALT_URL = "https://gateway.thegraph.com/api/subgraphs/id/81Dm16JjuFSrqz813HysXoGvuKET5Ews4LPeyqJzQJFd"


class TheGraphService:
    """Service for querying The Graph subgraph for Polymarket data."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.url = THEGRAPH_POLYMARKET_URL

    async def _query(self, query: str, variables: dict | None = None) -> dict[str, Any]:
        """Execute a GraphQL query against The Graph."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json={"query": query, "variables": variables or {}},
                    headers=headers,
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                if "errors" in result:
                    logger.error("GraphQL errors", errors=result["errors"])
                    return {}

                return result.get("data", {})
        except httpx.HTTPError as e:
            logger.error("The Graph query failed", error=str(e))
            return {}

    async def get_top_traders_by_volume(
        self,
        limit: int = 100,
        min_trades: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get top traders by trading volume from The Graph.

        This queries the Polymarket subgraph for users with highest trading activity.
        """
        query = """
        query GetTopTraders($first: Int!, $minTrades: Int!) {
            users(
                first: $first,
                orderBy: totalVolume,
                orderDirection: desc,
                where: { tradesCount_gte: $minTrades }
            ) {
                id
                tradesCount
                totalVolume
                profit
                lastTradeTimestamp
            }
        }
        """

        data = await self._query(query, {"first": limit, "minTrades": min_trades})
        return data.get("users", [])

    async def get_user_trades(
        self,
        user_address: str,
        first: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get trade history for a specific user.

        Args:
            user_address: Wallet address (lowercase)
            first: Number of trades to fetch

        Returns:
            List of trade data
        """
        query = """
        query GetUserTrades($userId: ID!, $first: Int!) {
            trades(
                first: $first,
                where: { user: $userId },
                orderBy: timestamp,
                orderDirection: desc
            ) {
                id
                user {
                    id
                }
                market {
                    id
                    question
                    outcome
                }
                side
                price
                amount
                outcome
                timestamp
                transactionHash
            }
        }
        """

        data = await self._query(query, {
            "userId": user_address.lower(),
            "first": first
        })
        return data.get("trades", [])

    async def get_user_positions(
        self,
        user_address: str
    ) -> list[dict[str, Any]]:
        """
        Get current positions for a user.

        Args:
            user_address: Wallet address (lowercase)

        Returns:
            List of position data
        """
        query = """
        query GetUserPositions($userId: ID!) {
            positions(
                where: { user: $userId, balance_gt: "0" }
            ) {
                id
                user {
                    id
                }
                market {
                    id
                    question
                    outcome
                    resolved
                    winningOutcome
                }
                outcome
                balance
                averagePrice
            }
        }
        """

        data = await self._query(query, {"userId": user_address.lower()})
        return data.get("positions", [])

    async def get_trader_stats(
        self,
        user_address: str
    ) -> dict[str, Any] | None:
        """
        Get comprehensive stats for a trader.

        Args:
            user_address: Wallet address

        Returns:
            Dict with trader statistics
        """
        query = """
        query GetTraderStats($userId: ID!) {
            user(id: $userId) {
                id
                tradesCount
                totalVolume
                profit
                lastTradeTimestamp
                positions(where: { balance_gt: "0" }) {
                    id
                    outcome
                    balance
                }
            }
        }
        """

        data = await self._query(query, {"userId": user_address.lower()})
        return data.get("user")

    async def get_top_profitable_traders(
        self,
        limit: int = 50,
        min_trades: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get traders with highest profit.

        Args:
            limit: Maximum traders to return
            min_trades: Minimum number of trades

        Returns:
            List of profitable traders
        """
        query = """
        query GetTopProfitableTraders($first: Int!, $minTrades: Int!) {
            users(
                first: $first,
                orderBy: profit,
                orderDirection: desc,
                where: {
                    tradesCount_gte: $minTrades,
                    profit_gt: "0"
                }
            ) {
                id
                tradesCount
                totalVolume
                profit
                lastTradeTimestamp
            }
        }
        """

        data = await self._query(query, {"first": limit, "minTrades": min_trades})
        return data.get("users", [])

    async def calculate_win_rate(self, user_address: str) -> tuple[Decimal, int, int]:
        """
        Calculate win rate for a trader from their resolved positions.

        Args:
            user_address: Wallet address

        Returns:
            Tuple of (win_rate, wins, losses)
        """
        query = """
        query GetResolvedPositions($userId: ID!) {
            positions(
                where: {
                    user: $userId,
                    market_: { resolved: true }
                }
            ) {
                id
                outcome
                balance
                market {
                    id
                    resolved
                    winningOutcome
                }
            }
        }
        """

        data = await self._query(query, {"userId": user_address.lower()})
        positions = data.get("positions", [])

        wins = 0
        losses = 0

        for pos in positions:
            market = pos.get("market", {})
            if market.get("resolved"):
                winning_outcome = market.get("winningOutcome")
                user_outcome = pos.get("outcome")

                if user_outcome == winning_outcome:
                    wins += 1
                else:
                    losses += 1

        total = wins + losses
        if total == 0:
            return Decimal("0"), 0, 0

        win_rate = Decimal(str(round(wins / total * 100, 2)))
        return win_rate, wins, losses


# Singleton instance
thegraph_service = TheGraphService()
