"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  BarChart3,
  ExternalLink,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import type { KalshiMarket } from "@/lib/api";

interface KalshiMarketCardProps {
  market: KalshiMarket;
  index: number;
}

function getMarketCategory(market: KalshiMarket): string {
  // Use API-provided category first
  if (market.category) {
    // Shorten long category names
    const cat = market.category;
    if (cat === "Climate and Weather") return "Climate";
    if (cat === "Science and Technology") return "Tech";
    return cat;
  }

  // Fallback to ticker-based detection
  const ticker = market.ticker;
  if (ticker.includes("NBA") || ticker.includes("NFL") || ticker.includes("MLB")) return "Sports";
  if (ticker.includes("ECON") || ticker.includes("FED") || ticker.includes("CPI")) return "Economics";
  if (ticker.includes("TRUMP") || ticker.includes("BIDEN") || ticker.includes("ELECT")) return "Politics";
  if (ticker.includes("WEATHER") || ticker.includes("TEMP")) return "Weather";
  if (ticker.includes("CRYPTO") || ticker.includes("BTC") || ticker.includes("ETH")) return "Crypto";
  return "General";
}

function formatTimeLeft(closeTime: string): string {
  const close = new Date(closeTime);
  const now = new Date();
  const diff = close.getTime() - now.getTime();

  if (diff < 0) return "Closed";

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h`;

  const minutes = Math.floor(diff / (1000 * 60));
  return `${minutes}m`;
}

export function KalshiMarketCard({ market, index }: KalshiMarketCardProps) {
  const yesPrice = parseFloat(market.yes_bid_dollars || "0") * 100;
  const noPrice = parseFloat(market.no_bid_dollars || "0") * 100;
  const category = getMarketCategory(market);
  const timeLeft = formatTimeLeft(market.close_time);

  // Extract readable title from market
  const displayTitle = market.title || market.ticker;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
    >
      <Card className="hover:border-primary/50 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 overflow-hidden h-full">
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="secondary" className="text-xs shrink-0">
                  {category}
                </Badge>
                <Badge
                  variant={market.status === "open" ? "success" : "warning"}
                  className="text-xs shrink-0"
                >
                  {market.status === "open" ? "Live" : market.status}
                </Badge>
              </div>
              <h3 className="font-semibold text-sm leading-tight line-clamp-2 mb-1">
                {displayTitle}
              </h3>
              <div className="flex items-center text-xs text-muted-foreground">
                <Clock className="h-3 w-3 mr-1" />
                <span>{timeLeft}</span>
              </div>
            </div>
            <a
              href={`https://kalshi.com/markets/${market.ticker}`}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 ml-2"
            >
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <ExternalLink className="h-4 w-4" />
              </Button>
            </a>
          </div>

          {/* Price Display */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-green-500/10 rounded-lg p-3 text-center">
              <div className="flex items-center justify-center gap-1 text-green-500 mb-1">
                <ArrowUpRight className="h-4 w-4" />
                <span className="text-xs font-medium">YES</span>
              </div>
              <div className="text-xl font-bold text-green-500">
                {yesPrice.toFixed(0)}c
              </div>
            </div>
            <div className="bg-red-500/10 rounded-lg p-3 text-center">
              <div className="flex items-center justify-center gap-1 text-red-500 mb-1">
                <ArrowDownRight className="h-4 w-4" />
                <span className="text-xs font-medium">NO</span>
              </div>
              <div className="text-xl font-bold text-red-500">
                {noPrice.toFixed(0)}c
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-3">
            <div className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              <span>Vol: {market.volume?.toLocaleString() || 0}</span>
            </div>
            <div className="flex items-center gap-1">
              <BarChart3 className="h-3 w-3" />
              <span>24h: {market.volume_24h?.toLocaleString() || 0}</span>
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              <span>OI: {market.open_interest?.toLocaleString() || 0}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
