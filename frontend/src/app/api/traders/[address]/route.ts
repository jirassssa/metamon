import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-15a6.up.railway.app';

export async function GET(
  request: NextRequest,
  { params }: { params: { address: string } }
) {
  const { address } = params;

  try {
    const response = await fetch(`${BACKEND_URL}/api/traders/${address}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      // If trader not found in our DB, try to fetch from Polymarket leaderboard
      if (response.status === 404) {
        // Fetch from leaderboard to get basic info
        const leaderboardResponse = await fetch(
          `${BACKEND_URL}/api/traders/leaderboard/live?limit=100`,
          { cache: 'no-store' }
        );

        if (leaderboardResponse.ok) {
          const leaderboardData = await leaderboardResponse.json();
          const trader = leaderboardData.traders?.find(
            (t: any) => t.wallet_address.toLowerCase() === address.toLowerCase()
          );

          if (trader) {
            // Convert leaderboard data to TraderDetail format
            return NextResponse.json({
              id: trader.wallet_address,
              wallet_address: trader.wallet_address,
              display_name: trader.display_name,
              first_trade_date: null,
              last_synced: leaderboardData.last_updated,
              performance: {
                total_trades: trader.trades_count || 0,
                win_rate: String(trader.win_rate || 0),
                roi: String(((trader.profit / Math.max(trader.volume, 1)) * 100).toFixed(2)),
                total_volume: String(trader.volume || 0),
                profit_factor: null,
              },
              risk: {
                risk_score: trader.win_rate >= 60 ? "Low" : trader.win_rate >= 40 ? "Medium" : "High",
                max_drawdown: null,
                sharpe_ratio: null,
                profit_factor: null,
              },
              followers_count: 0,
              profit: trader.profit,
              volume: trader.volume,
              positions_count: trader.positions_count,
            });
          }
        }
      }
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch trader' },
      { status: 500 }
    );
  }
}
