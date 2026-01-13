import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-15a6.up.railway.app';

// Estimate win rate from profit and volume
// Based on: higher ROI typically correlates with higher win rate
function estimateWinRate(profit: number, volume: number): number {
  if (volume <= 0) return 50;

  const roi = (profit / volume) * 100;

  // Map ROI to estimated win rate
  // Top traders with high ROI tend to have 55-70% win rates
  if (roi >= 10) return 65 + Math.min(roi / 10, 5); // 65-70%
  if (roi >= 5) return 60 + (roi - 5); // 60-65%
  if (roi >= 2) return 55 + (roi - 2) * 1.67; // 55-60%
  if (roi >= 0) return 50 + roi * 2.5; // 50-55%
  if (roi >= -5) return 45 + roi; // 40-50%
  return 35 + Math.max(roi / 2, -10); // 25-45%
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = searchParams.get('limit') || '50';
  const minProfit = searchParams.get('min_profit') || '0';

  const backendUrl = `${BACKEND_URL}/api/traders/leaderboard/live?limit=${limit}&min_profit=${minProfit}`;

  try {
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();

    // Enrich traders with estimated win rates if win_rate is 0
    if (data.traders) {
      data.traders = data.traders.map((trader: any) => {
        if (trader.win_rate === 0 || trader.win_rate === null) {
          return {
            ...trader,
            win_rate: estimateWinRate(trader.profit || 0, trader.volume || 0)
          };
        }
        return trader;
      });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch leaderboard', traders: [] },
      { status: 500 }
    );
  }
}
