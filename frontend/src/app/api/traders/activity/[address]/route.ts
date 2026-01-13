import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-15a6.up.railway.app';

export async function GET(
  request: NextRequest,
  { params }: { params: { address: string } }
) {
  const { address } = params;
  const searchParams = request.nextUrl.searchParams;
  const limit = searchParams.get('limit') || '50';

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/traders/activity/${encodeURIComponent(address)}?limit=${limit}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      }
    );

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch activity', activities: [], total: 0, wallet_address: address },
      { status: 500 }
    );
  }
}
