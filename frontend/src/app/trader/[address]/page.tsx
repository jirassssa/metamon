"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  DollarSign,
  Copy,
  ExternalLink,
  Shield,
} from "lucide-react";
import { useSafePrivy } from "@/hooks/use-safe-privy";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyModal } from "@/components/copy/CopyModal";
import { TradeHistory } from "@/components/trader/TradeHistory";
import { getTrader, type TraderDetail } from "@/lib/api";
import {
  formatAddress,
  formatCurrency,
  formatPercent,
  formatNumber,
  getPnLColor,
} from "@/lib/utils";

function StatCard({
  title,
  value,
  subValue,
  icon: Icon,
  valueColor,
}: {
  title: string;
  value: string;
  subValue?: string;
  icon: React.ComponentType<{ className?: string }>;
  valueColor?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${valueColor || ""}`}>{value}</div>
        {subValue && (
          <p className="text-xs text-muted-foreground">{subValue}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function TraderProfilePage() {
  const params = useParams();
  const address = params.address as string;
  const { authenticated: isConnected } = useSafePrivy();
  const [isCopyModalOpen, setIsCopyModalOpen] = useState(false);

  const { data: trader, isLoading, error } = useQuery({
    queryKey: ["trader", address],
    queryFn: () => getTrader(address),
    enabled: !!address,
  });

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-32 skeleton rounded-lg" />
          <div className="grid md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 skeleton rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !trader) {
    return (
      <div className="container py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">Trader Not Found</h1>
        <p className="text-muted-foreground">
          The trader you&apos;re looking for doesn&apos;t exist or has been
          removed.
        </p>
      </div>
    );
  }

  const roi = parseFloat(trader.performance.roi) || 0;
  const winRate = parseFloat(trader.performance.win_rate) || 0;
  const totalTrades = trader.performance.total_trades || 0;
  const totalVolume = trader.performance.total_volume || "0";
  const riskScore = trader.risk.risk_score || "Unknown";

  // Create a compatible trader object for CopyModal
  const traderForCopy = {
    wallet_address: trader.wallet_address,
    total_trades: totalTrades,
    win_rate: trader.performance.win_rate,
    roi: trader.performance.roi,
    total_volume: totalVolume,
    portfolio_value: "0",
    followers_count: trader.followers_count,
    risk_score: riskScore,
    created_at: trader.last_synced || "",
    updated_at: trader.last_synced || "",
  };

  return (
    <div className="container py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary/50 flex items-center justify-center text-white text-2xl font-bold">
              {address.slice(2, 4).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold">
                  {formatAddress(trader.wallet_address)}
                </h1>
                <a
                  href={`https://polygonscan.com/address/${trader.wallet_address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-primary"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant={
                    riskScore === "Low"
                      ? "success"
                      : riskScore === "Medium"
                      ? "warning"
                      : "danger"
                  }
                >
                  <Shield className="h-3 w-3 mr-1" />
                  {riskScore} Risk
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {formatNumber(trader.followers_count)} followers
                </span>
              </div>
            </div>
          </div>

          <Button
            size="lg"
            onClick={() => setIsCopyModalOpen(true)}
            disabled={!isConnected}
          >
            <Copy className="h-4 w-4 mr-2" />
            {isConnected ? "Copy Trader" : "Connect Wallet to Copy"}
          </Button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <StatCard
          title="Total ROI"
          value={formatPercent(roi)}
          icon={roi >= 0 ? TrendingUp : TrendingDown}
          valueColor={getPnLColor(roi)}
        />
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          icon={Activity}
        />
        <StatCard
          title="Total Trades"
          value={formatNumber(totalTrades)}
          icon={Activity}
        />
        <StatCard
          title="Total Volume"
          value={formatCurrency(totalVolume, 0)}
          icon={DollarSign}
        />
      </motion.div>

      {/* Risk Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid md:grid-cols-2 gap-4 mb-8"
      >
        <Card>
          <CardHeader>
            <CardTitle>Risk Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Max Drawdown</span>
                <span>{trader.risk.max_drawdown || "0"}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Profit Factor</span>
                <span>{trader.performance.profit_factor || "N/A"}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Followers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Users className="h-8 w-8 text-primary" />
              <div>
                <div className="text-3xl font-bold">
                  {formatNumber(trader.followers_count)}
                </div>
                <p className="text-sm text-muted-foreground">
                  Users copying this trader
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Trade History */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-8"
      >
        <TradeHistory walletAddress={trader.wallet_address} />
      </motion.div>

      {/* Copy Modal */}
      {trader && (
        <CopyModal
          trader={traderForCopy}
          isOpen={isCopyModalOpen}
          onClose={() => setIsCopyModalOpen(false)}
        />
      )}
    </div>
  );
}
