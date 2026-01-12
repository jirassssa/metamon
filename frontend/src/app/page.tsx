"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  Shield,
  Zap,
  Users,
  Crown,
  DollarSign,
  Activity,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getLiveLeaderboard, type DiscoveredTrader } from "@/lib/api";
import { formatAddress, formatCurrency, getPnLColor } from "@/lib/utils";

const features = [
  {
    icon: TrendingUp,
    title: "Follow Top Traders",
    description:
      "Discover and copy the most successful Polymarket traders with proven track records.",
  },
  {
    icon: Shield,
    title: "Risk Management",
    description:
      "Set stop-losses, position limits, and allocation caps to protect your capital.",
  },
  {
    icon: Zap,
    title: "Instant Execution",
    description:
      "Trades are copied in real-time using gasless transactions via Safe wallets.",
  },
  {
    icon: Users,
    title: "Transparent Analytics",
    description:
      "Full visibility into trader performance, win rates, and portfolio composition.",
  },
];

const stats = [
  { value: "$2.5M+", label: "Total Volume Copied" },
  { value: "1,200+", label: "Active Copiers" },
  { value: "89%", label: "Avg Win Rate" },
  { value: "156%", label: "Top Trader ROI" },
];

function TopTraderRow({
  trader,
  rank,
}: {
  trader: DiscoveredTrader;
  rank: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: rank * 0.05 }}
    >
      <Link href={`/trader/${trader.wallet_address}`}>
        <Card className="hover:border-primary/50 transition-all duration-200 cursor-pointer">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              {/* Rank */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                  rank <= 3
                    ? "bg-gradient-to-br from-yellow-400 to-yellow-600"
                    : "bg-muted"
                }`}
              >
                {rank <= 3 ? (
                  <Crown className="h-5 w-5 text-white" />
                ) : (
                  <span className="font-bold text-muted-foreground">
                    {rank}
                  </span>
                )}
              </div>

              {/* Trader Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold truncate">
                    {trader.display_name ||
                      formatAddress(trader.wallet_address)}
                  </span>
                  {trader.win_rate >= 60 && (
                    <Badge variant="success" className="text-xs">
                      Hot
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Activity className="h-3 w-3" />
                    {trader.win_rate.toFixed(1)}% win
                  </span>
                  <span>{trader.trades_count} trades</span>
                </div>
              </div>

              {/* Profit */}
              <div className="text-right flex-shrink-0">
                <div
                  className={`font-bold ${getPnLColor(trader.profit)}`}
                >
                  {formatCurrency(trader.profit)}
                </div>
                <div className="text-xs text-muted-foreground">profit</div>
              </div>

              {/* Arrow */}
              <ExternalLink className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}

export default function HomePage() {
  // Fetch top 10 traders for homepage
  const { data: leaderboardData, isLoading: loadingLeaderboard } = useQuery({
    queryKey: ["homepage-leaderboard"],
    queryFn: () => getLiveLeaderboard(10, 0),
    staleTime: 60000, // 1 minute
  });

  const topTraders = leaderboardData?.traders || [];

  return (
    <div className="relative">
      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/10 rounded-full blur-3xl" />

        <div className="container relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-3xl mx-auto"
          >
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Copy the Best{" "}
              <span className="text-primary">Polymarket</span> Traders
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-8">
              Automatically mirror trades from top performers. Set your risk
              parameters, sit back, and let the pros guide your predictions.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/leaderboard">
                  View Leaderboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/portfolio">My Portfolio</Link>
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16"
          >
            {stats.map((stat, index) => (
              <Card
                key={index}
                className="bg-card/50 backdrop-blur border-border/50"
              >
                <CardContent className="p-6 text-center">
                  <div className="text-2xl md:text-3xl font-bold text-primary">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {stat.label}
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Top 10 Traders Section */}
      <section className="py-16 bg-muted/30">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex items-center justify-between mb-8"
          >
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-2">
                Top 10 Traders
              </h2>
              <p className="text-muted-foreground">
                Live rankings from Polymarket - updated in real-time
              </p>
            </div>
            <Button variant="outline" asChild>
              <Link href="/leaderboard">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </motion.div>

          {/* Loading State */}
          {loadingLeaderboard && (
            <div className="grid md:grid-cols-2 gap-4">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className="h-20 bg-muted animate-pulse rounded-lg"
                />
              ))}
            </div>
          )}

          {/* Traders Grid */}
          {!loadingLeaderboard && topTraders.length > 0 && (
            <div className="grid md:grid-cols-2 gap-4">
              {topTraders.map((trader, index) => (
                <TopTraderRow
                  key={trader.wallet_address}
                  trader={trader}
                  rank={index + 1}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loadingLeaderboard && topTraders.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                Unable to load leaderboard. Please try again later.
              </p>
            </div>
          )}

          {/* Info Banner */}
          {topTraders.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/20 flex items-center justify-between"
            >
              <div className="flex items-center gap-2 text-sm">
                <Zap className="h-4 w-4 text-primary" />
                <span>
                  Data fetched live from Polymarket API
                </span>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/leaderboard">
                  Explore More Traders
                  <ArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </motion.div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Why Copy Trade on Polymarket?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Leverage the expertise of successful traders while maintaining
              full control over your risk exposure.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full hover:border-primary/50 transition-colors">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <h3 className="font-semibold text-lg mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative rounded-2xl overflow-hidden"
          >
            <div className="absolute inset-0 gradient-primary opacity-90" />
            <div className="relative p-8 md:p-16 text-center">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Ready to Start Copy Trading?
              </h2>
              <p className="text-white/80 mb-8 max-w-2xl mx-auto">
                Connect your wallet, choose your traders, and start copying in
                minutes.
              </p>
              <Button size="lg" variant="secondary" asChild>
                <Link href="/leaderboard">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
