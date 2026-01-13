import { NextRequest, NextResponse } from 'next/server';

const KALSHI_API_BASE = 'https://api.elections.kalshi.com/trade-api/v2';

export interface KalshiMarket {
  ticker: string;
  event_ticker: string;
  market_type: string;
  title: string;
  subtitle?: string;
  yes_bid: number;
  yes_ask: number;
  no_bid: number;
  no_ask: number;
  yes_bid_dollars: string;
  yes_ask_dollars: string;
  no_bid_dollars: string;
  no_ask_dollars: string;
  last_price: number;
  last_price_dollars: string;
  volume: number;
  volume_24h: number;
  open_interest: number;
  status: string;
  close_time: string;
  settlement_value_dollars?: string;
  category?: string;
}

interface KalshiEvent {
  event_ticker: string;
  title: string;
  category: string;
}

export interface KalshiMarketsResponse {
  markets: KalshiMarket[];
  cursor: string;
  total?: number;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = parseInt(searchParams.get('limit') || '50');
  const minVolume = parseInt(searchParams.get('min_volume') || '0');
  const event_ticker = searchParams.get('event_ticker') || '';

  try {
    // If specific event requested, fetch directly
    if (event_ticker) {
      const response = await fetch(
        `${KALSHI_API_BASE}/markets?event_ticker=${event_ticker}`,
        {
          headers: { 'Accept': 'application/json' },
          cache: 'no-store',
        }
      );
      if (!response.ok) throw new Error(`Kalshi API error: ${response.status}`);
      const data = await response.json();
      return NextResponse.json(data);
    }

    // Fetch events first to get non-MVE prediction markets
    const eventsResponse = await fetch(
      `${KALSHI_API_BASE}/events?limit=200`,
      {
        headers: { 'Accept': 'application/json' },
        cache: 'no-store',
      }
    );

    if (!eventsResponse.ok) {
      throw new Error(`Kalshi Events API error: ${eventsResponse.status}`);
    }

    const eventsData = await eventsResponse.json();
    const events: KalshiEvent[] = eventsData.events || [];

    // Filter out MVE events (sports parlays)
    const nonMveEvents = events.filter(event => {
      const ticker = event.event_ticker.toUpperCase();
      return !ticker.includes('MVE') &&
             !ticker.includes('MULTIGAME') &&
             !ticker.includes('SINGLEGAME') &&
             !ticker.includes('EXTENDED');
    });

    // Fetch markets for each non-MVE event in parallel (limit to first 30 events)
    const eventsToFetch = nonMveEvents.slice(0, 30);
    const marketPromises = eventsToFetch.map(event =>
      fetch(`${KALSHI_API_BASE}/markets?event_ticker=${event.event_ticker}`, {
        headers: { 'Accept': 'application/json' },
        cache: 'no-store',
      }).then(res => res.ok ? res.json() : { markets: [] })
    );

    const marketResults = await Promise.all(marketPromises);

    // Combine all markets
    let allMarkets: KalshiMarket[] = [];
    marketResults.forEach((result, index) => {
      if (result.markets) {
        // Add category from event
        const category = eventsToFetch[index].category;
        result.markets.forEach((market: KalshiMarket) => {
          market.category = category;
        });
        allMarkets = allMarkets.concat(result.markets);
      }
    });

    // Apply minimum volume filter
    if (minVolume > 0) {
      allMarkets = allMarkets.filter(market => (market.volume || 0) >= minVolume);
    }

    // Filter out settled/finalized markets (both yes and no prices are 0)
    allMarkets = allMarkets.filter(market => {
      const yesBid = market.yes_bid || 0;
      const noBid = market.no_bid || 0;
      // Keep markets that have active pricing
      return yesBid > 0 || noBid > 0 || market.status === 'open';
    });

    // Sort by volume (most active first)
    allMarkets.sort((a, b) => (b.volume || 0) - (a.volume || 0));

    // Apply limit
    allMarkets = allMarkets.slice(0, limit);

    return NextResponse.json({
      markets: allMarkets,
      cursor: '',
      total: allMarkets.length
    });
  } catch (error) {
    console.error('Kalshi markets fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch Kalshi markets', markets: [] },
      { status: 500 }
    );
  }
}
