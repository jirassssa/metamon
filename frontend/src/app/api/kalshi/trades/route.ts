import { NextRequest, NextResponse } from 'next/server';

const KALSHI_API_BASE = 'https://api.elections.kalshi.com/trade-api/v2';

export interface KalshiTrade {
  trade_id: string;
  ticker: string;
  price: number;
  count: number;
  yes_price: number;
  no_price: number;
  yes_price_dollars: string;
  no_price_dollars: string;
  taker_side: 'yes' | 'no';
  created_time: string;
}

export interface KalshiTradesResponse {
  trades: KalshiTrade[];
  cursor: string;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = searchParams.get('limit') || '100';
  const cursor = searchParams.get('cursor') || '';
  const ticker = searchParams.get('ticker') || '';

  try {
    const params = new URLSearchParams({ limit });

    if (cursor) params.append('cursor', cursor);
    if (ticker) params.append('ticker', ticker);

    const response = await fetch(
      `${KALSHI_API_BASE}/markets/trades?${params.toString()}`,
      {
        headers: {
          'Accept': 'application/json',
        },
        cache: 'no-store',
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Kalshi trades error:', response.status, errorText);
      throw new Error(`Kalshi API error: ${response.status}`);
    }

    const data: KalshiTradesResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Kalshi trades fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch trades', trades: [] },
      { status: 500 }
    );
  }
}
