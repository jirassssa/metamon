"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Flame,
  Activity,
  Clock,
  ExternalLink,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getKalshiMarkets, type KalshiMarket } from "@/lib/api";

function formatTimeLeft(closeTime: string): string {
  const close = new Date(closeTime);
  const now = new Date();
  const diff = close.getTime() - now.getTime();

  if (diff < 0) return "Closed";

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d`;
  if (hours > 0) return `${hours}h`;

  const minutes = Math.floor(diff / (1000 * 60));
  return `${minutes}m`;
}

function TrendingMarketItem({
  market,
  rank,
}: {
  market: KalshiMarket;
  rank: number;
}) {
  const yesPrice = parseFloat(market.yes_bid_dollars || "0") * 100;
  const noPrice = parseFloat(market.no_bid_dollars || "0") * 100;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: rank * 0.05 }}
      className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0">
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{market.title}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
          <span className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            {market.volume_24h?.toLocaleString() || 0} vol
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatTimeLeft(market.close_time)}
          </span>
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <div className="text-center">
          <div className="text-xs text-green-500 font-medium">YES</div>
          <div className="text-sm font-bold text-green-500">{yesPrice.toFixed(0)}c</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-red-500 font-medium">NO</div>
          <div className="text-sm font-bold text-red-500">{noPrice.toFixed(0)}c</div>
        </div>
      </div>
      <a
        href={`https://kalshi.com/markets/${market.ticker}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <ExternalLink className="h-4 w-4" />
        </Button>
      </a>
    </motion.div>
  );
}

export function TrendingMarkets() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["kalshi-trending"],
    queryFn: () => getKalshiMarkets(100, "open"),
    staleTime: 60000,
  });

  // Get top 10 by volume
  const trendingMarkets =
    data?.markets
      ?.filter((m) => m.volume_24h > 0)
      .sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0))
      .slice(0, 10) || [];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            Trending Markets
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-24 mt-1" />
                </div>
                <Skeleton className="h-8 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || trendingMarkets.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            Trending Markets
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm text-center py-4">
            No trending markets available
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Flame className="h-5 w-5 text-orange-500" />
          Trending Markets
          <Badge variant="secondary" className="ml-2">
            Top 10
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {trendingMarkets.map((market, index) => (
            <TrendingMarketItem
              key={market.ticker}
              market={market}
              rank={index + 1}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
