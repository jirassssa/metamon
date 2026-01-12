"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { TrendingUp, Users, Activity, ExternalLink } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  formatAddress,
  formatCurrency,
  formatPercent,
  formatNumber,
  getRiskColor,
  getPnLColor,
} from "@/lib/utils";
import type { Trader } from "@/lib/api";

interface TraderCardProps {
  trader: Trader;
  rank?: number;
}

export function TraderCard({ trader, rank }: TraderCardProps) {
  const roi = parseFloat(trader.roi);
  const winRate = parseFloat(trader.win_rate);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: rank ? rank * 0.05 : 0 }}
    >
      <Card className="hover:border-primary/50 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5">
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {rank && (
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    rank <= 3
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {rank}
                </div>
              )}
              <div>
                <Link
                  href={`/trader/${trader.wallet_address}`}
                  className="font-semibold hover:text-primary transition-colors"
                >
                  {formatAddress(trader.wallet_address)}
                </Link>
                <Badge
                  variant={
                    trader.risk_score === "Low"
                      ? "success"
                      : trader.risk_score === "Medium"
                      ? "warning"
                      : "danger"
                  }
                  className="ml-2"
                >
                  {trader.risk_score} Risk
                </Badge>
              </div>
            </div>
            <Link href={`/trader/${trader.wallet_address}`}>
              <Button variant="ghost" size="icon">
                <ExternalLink className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="space-y-1">
              <div className="flex items-center text-muted-foreground text-sm">
                <TrendingUp className="h-4 w-4 mr-1" />
                ROI
              </div>
              <div className={`text-xl font-bold ${getPnLColor(roi)}`}>
                {formatPercent(roi)}
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center text-muted-foreground text-sm">
                <Activity className="h-4 w-4 mr-1" />
                Win Rate
              </div>
              <div className="text-xl font-bold">{winRate.toFixed(1)}%</div>
            </div>
          </div>

          {/* Additional Stats */}
          <div className="flex items-center justify-between text-sm text-muted-foreground border-t pt-4">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{formatNumber(trader.followers_count)} followers</span>
            </div>
            <div>
              <span>{formatNumber(trader.total_trades)} trades</span>
            </div>
            <div>
              <span>{formatCurrency(trader.total_volume, 0)} vol</span>
            </div>
          </div>

          {/* Copy Button */}
          <Link href={`/trader/${trader.wallet_address}`} className="block mt-4">
            <Button className="w-full" size="sm">
              Copy Trader
            </Button>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  );
}
