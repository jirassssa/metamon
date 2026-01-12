"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import {
  TrendingUp,
  Activity,
  DollarSign,
  BarChart3,
  Crown,
  ExternalLink,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  formatAddress,
  formatCurrency,
  getPnLColor,
} from "@/lib/utils";
import type { DiscoveredTrader } from "@/lib/api";

interface DiscoveredTraderCardProps {
  trader: DiscoveredTrader;
  index: number;
}

function getRiskLevel(winRate: number, profit: number): string {
  if (winRate >= 70 && profit > 10000) return "Low";
  if (winRate >= 55 && profit > 1000) return "Medium";
  return "High";
}

export function DiscoveredTraderCard({
  trader,
  index,
}: DiscoveredTraderCardProps) {
  const riskLevel = getRiskLevel(trader.win_rate, trader.profit);
  const displayRank = trader.rank || index + 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="hover:border-primary/50 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 overflow-hidden">
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {displayRank <= 3 ? (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center">
                  <Crown className="h-5 w-5 text-white" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-lg font-bold text-muted-foreground">
                  {displayRank}
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  {trader.avatar_url && (
                    <Image
                      src={trader.avatar_url}
                      alt=""
                      width={24}
                      height={24}
                      className="rounded-full"
                    />
                  )}
                  <Link
                    href={`/trader/${trader.wallet_address}`}
                    className="font-semibold hover:text-primary transition-colors"
                  >
                    {trader.display_name || formatAddress(trader.wallet_address)}
                  </Link>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant={
                      riskLevel === "Low"
                        ? "success"
                        : riskLevel === "Medium"
                        ? "warning"
                        : "danger"
                    }
                  >
                    {riskLevel} Risk
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    Live Data
                  </Badge>
                </div>
              </div>
            </div>
            <Link href={`/trader/${trader.wallet_address}`}>
              <Button variant="ghost" size="icon">
                <ExternalLink className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Main Stats */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="space-y-1">
              <div className="flex items-center text-muted-foreground text-sm">
                <DollarSign className="h-4 w-4 mr-1" />
                Total Profit
              </div>
              <div className={`text-xl font-bold ${getPnLColor(trader.profit)}`}>
                {formatCurrency(trader.profit)}
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center text-muted-foreground text-sm">
                <Activity className="h-4 w-4 mr-1" />
                Win Rate
              </div>
              <div
                className={`text-xl font-bold ${
                  trader.win_rate >= 60
                    ? "text-green-500"
                    : trader.win_rate >= 50
                    ? "text-yellow-500"
                    : "text-red-500"
                }`}
              >
                {trader.win_rate.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Secondary Stats */}
          <div className="flex items-center justify-between text-sm text-muted-foreground border-t pt-4">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              <span>{formatCurrency(trader.volume, 0)} vol</span>
            </div>
            <div className="flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              <span>{trader.trades_count} trades</span>
            </div>
            <div>
              <span>{trader.positions_count} positions</span>
            </div>
          </div>

          {/* Copy Button */}
          <Link href={`/trader/${trader.wallet_address}`} className="block mt-4">
            <Button className="w-full" size="sm">
              Copy This Trader
            </Button>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  );
}
