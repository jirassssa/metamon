"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  AlertCircle,
} from "lucide-react";
import { useAccount } from "wagmi";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import {
  getCopies,
  getPortfolio,
  getPortfolioPositions,
  type Position,
} from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  formatAddress,
  getPnLColor,
} from "@/lib/utils";
import Link from "next/link";

function PositionCard({ position }: { position: Position }) {
  const pnl = parseFloat(position.pnl);
  const pnlPercentage = parseFloat(position.pnl_percentage);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <p className="font-medium truncate max-w-[200px]">
              {position.market_name}
            </p>
            <p className="text-sm text-muted-foreground">
              Copied from {formatAddress(position.trader_address)}
            </p>
          </div>
          <Badge
            variant={position.status === "open" ? "default" : "secondary"}
          >
            {position.status}
          </Badge>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <p className="text-muted-foreground">Side</p>
            <p
              className={`font-semibold ${
                position.side === "YES" ? "text-green-500" : "text-red-500"
              }`}
            >
              {position.side}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Size</p>
            <p className="font-semibold">{formatCurrency(position.size)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">P&L</p>
            <p className={`font-semibold ${getPnLColor(pnl)}`}>
              {formatCurrency(pnl)} ({formatPercent(pnlPercentage)})
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function PortfolioPage() {
  const { isConnected } = useAccount();
  const { token, isAuthenticated } = useAuthStore();

  const { data: portfolio, isLoading: portfolioLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => getPortfolio(token!),
    enabled: isAuthenticated && !!token,
  });

  const { data: copies } = useQuery({
    queryKey: ["copies"],
    queryFn: () => getCopies(token!),
    enabled: isAuthenticated && !!token,
  });

  const { data: positions } = useQuery({
    queryKey: ["portfolio-positions"],
    queryFn: () => getPortfolioPositions(token!),
    enabled: isAuthenticated && !!token,
  });

  if (!isConnected) {
    return (
      <div className="container py-16">
        <div className="text-center">
          <Wallet className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h1 className="text-2xl font-bold mb-2">Connect Your Wallet</h1>
          <p className="text-muted-foreground mb-6">
            Connect your wallet to view your portfolio and copy trading
            positions.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="container py-16">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h1 className="text-2xl font-bold mb-2">Sign In Required</h1>
          <p className="text-muted-foreground mb-6">
            Please sign in with your wallet to access your portfolio.
          </p>
        </div>
      </div>
    );
  }

  const totalPnl = portfolio ? parseFloat(portfolio.total_pnl) : 0;

  if (portfolioLoading) {
    return (
      <div className="container py-8" aria-busy="true" aria-label="Loading portfolio">
        <div className="animate-pulse space-y-8">
          <div>
            <div className="h-8 w-48 bg-muted rounded mb-2" />
            <div className="h-4 w-72 bg-muted rounded" />
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded-lg" />
            ))}
          </div>
          <div className="h-64 bg-muted rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">My Portfolio</h1>
        <p className="text-muted-foreground">
          Track your copy trading performance and positions
        </p>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {portfolio ? formatCurrency(portfolio.total_value) : "--"}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            {totalPnl >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getPnLColor(totalPnl)}`}>
              {portfolio ? formatCurrency(portfolio.total_pnl) : "--"}
            </div>
            <p className="text-xs text-muted-foreground">
              {portfolio ? formatPercent(portfolio.total_pnl_percentage) : "--"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {portfolio?.open_positions ?? "--"}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Copies</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {copies?.total ?? "--"}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Active Copies */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Active Copies</h2>
          <Button variant="outline" size="sm" asChild>
            <Link href="/leaderboard">Find Traders</Link>
          </Button>
        </div>

        {copies?.copies.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                You&apos;re not copying any traders yet
              </p>
              <Button asChild>
                <Link href="/leaderboard">Browse Traders</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {copies?.copies.map((copy) => (
              <Card key={copy.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Link
                      href={`/trader/${copy.trader_address}`}
                      className="font-semibold hover:text-primary"
                    >
                      {formatAddress(copy.trader_address)}
                    </Link>
                    <Badge variant={copy.is_active ? "success" : "secondary"}>
                      {copy.is_active ? "Active" : "Paused"}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Allocation</span>
                      <span>{formatCurrency(copy.allocation)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Remaining</span>
                      <span>{formatCurrency(copy.remaining_allocation)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Copy Ratio</span>
                      <span>{copy.copy_ratio}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total P&L</span>
                      <span
                        className={getPnLColor(parseFloat(copy.total_pnl))}
                      >
                        {formatCurrency(copy.total_pnl)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </motion.div>

      {/* Open Positions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold mb-4">Open Positions</h2>

        {positions?.positions.filter((p) => p.status === "open").length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No open positions</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {positions?.positions
              .filter((p) => p.status === "open")
              .map((position) => (
                <PositionCard key={position.id} position={position} />
              ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
