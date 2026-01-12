"use client";

import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { ArrowUpRight, ArrowDownRight, ExternalLink } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getTraderActivity, type TradeActivity } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface TradeHistoryProps {
  walletAddress: string;
}

function TradeRow({ trade }: { trade: TradeActivity }) {
  const date = new Date(trade.timestamp * 1000);
  const timeAgo = formatDistanceToNow(date, { addSuffix: true });

  // Determine if it's YES or NO based on outcome
  const isYes = trade.outcome?.toLowerCase().includes("yes") ||
                trade.outcome?.toLowerCase().includes("over") ||
                trade.outcome?.toLowerCase() === "yes";
  const betDirection = isYes ? "YES" : "NO";

  // Build correct Polymarket URL using eventSlug (not market slug)
  // Format: /event/{eventSlug}#{marketSlug} for deep-linking
  const eventSlug = trade.event_slug || trade.market_slug;
  const polymarketUrl = trade.event_slug
    ? `https://polymarket.com/event/${trade.event_slug}#${trade.market_slug}`
    : `https://polymarket.com/event/${trade.market_slug}`;

  return (
    <a
      href={polymarketUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-between py-3 border-b last:border-0 hover:bg-muted/50 transition-colors px-2 -mx-2 rounded"
    >
      <div className="flex items-center gap-3">
        {trade.icon && (
          <img
            src={trade.icon}
            alt=""
            className="w-10 h-10 rounded-full object-cover"
          />
        )}
        <div>
          <div className="font-medium text-sm line-clamp-1 hover:text-primary">
            {trade.market_title}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
            <span>{timeAgo}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          {/* Show YES/NO with BUY/SELL */}
          <div className="flex items-center gap-2 justify-end">
            <Badge
              variant={isYes ? "success" : "danger"}
              className="text-xs font-bold"
            >
              {trade.outcome || betDirection}
            </Badge>
            <span
              className={`font-medium text-sm ${
                trade.side === "BUY" ? "text-green-500" : "text-red-500"
              }`}
            >
              {trade.side === "BUY" ? (
                <ArrowUpRight className="h-4 w-4 inline" />
              ) : (
                <ArrowDownRight className="h-4 w-4 inline" />
              )}
              {trade.side}
            </span>
          </div>
          {/* Show amount and price */}
          <div className="text-sm font-semibold mt-1">
            {formatCurrency(trade.usdc_size)}
            <span className="text-muted-foreground font-normal ml-1">
              @ {(trade.price * 100).toFixed(0)}¢
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            {trade.size.toFixed(1)} shares
          </div>
        </div>
        <ExternalLink className="h-4 w-4 text-muted-foreground" />
      </div>
    </a>
  );
}

export function TradeHistory({ walletAddress }: TradeHistoryProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["traderActivity", walletAddress],
    queryFn: () => getTraderActivity(walletAddress, 20),
    enabled: !!walletAddress,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 skeleton rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            Unable to load trading history
          </p>
        </CardContent>
      </Card>
    );
  }

  if (data.activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No recent trading activity
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Trades ({data.total})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="divide-y">
          {data.activities.map((trade, index) => (
            <TradeRow key={`${trade.id}-${index}`} trade={trade} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
