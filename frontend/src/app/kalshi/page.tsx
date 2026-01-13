"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search,
  TrendingUp,
  Activity,
  Zap,
  RefreshCw,
  BarChart3,
  Filter,
  Users,
} from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { KalshiMarketCard } from "@/components/kalshi/KalshiMarketCard";
import { getKalshiMarkets, type KalshiMarket } from "@/lib/api";

const categoryFilters = [
  { value: "all", label: "All Markets", icon: BarChart3 },
  { value: "sports", label: "Sports", icon: Activity },
  { value: "politics", label: "Politics", icon: Users },
  { value: "economics", label: "Economics", icon: TrendingUp },
];

const sortOptions = [
  { value: "volume_24h", label: "24h Volume" },
  { value: "volume", label: "Total Volume" },
  { value: "open_interest", label: "Open Interest" },
  { value: "close_time", label: "Closing Soon" },
];

function filterMarketsByCategory(markets: KalshiMarket[], category: string): KalshiMarket[] {
  if (category === "all") return markets;

  return markets.filter((market) => {
    const ticker = market.ticker.toUpperCase();
    const title = (market.title || "").toUpperCase();

    switch (category) {
      case "sports":
        return (
          ticker.includes("NBA") ||
          ticker.includes("NFL") ||
          ticker.includes("MLB") ||
          ticker.includes("NHL") ||
          ticker.includes("SPORT") ||
          title.includes("GAME") ||
          title.includes("WIN")
        );
      case "politics":
        return (
          ticker.includes("TRUMP") ||
          ticker.includes("BIDEN") ||
          ticker.includes("ELECT") ||
          ticker.includes("PRES") ||
          ticker.includes("CONGRESS") ||
          title.includes("ELECTION") ||
          title.includes("PRESIDENT")
        );
      case "economics":
        return (
          ticker.includes("ECON") ||
          ticker.includes("FED") ||
          ticker.includes("CPI") ||
          ticker.includes("GDP") ||
          ticker.includes("RATE") ||
          title.includes("INFLATION") ||
          title.includes("RECESSION")
        );
      default:
        return true;
    }
  });
}

function sortMarkets(markets: KalshiMarket[], sortBy: string): KalshiMarket[] {
  const sorted = [...markets];

  switch (sortBy) {
    case "volume_24h":
      return sorted.sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0));
    case "volume":
      return sorted.sort((a, b) => (b.volume || 0) - (a.volume || 0));
    case "open_interest":
      return sorted.sort((a, b) => (b.open_interest || 0) - (a.open_interest || 0));
    case "close_time":
      return sorted.sort(
        (a, b) => new Date(a.close_time).getTime() - new Date(b.close_time).getTime()
      );
    default:
      return sorted;
  }
}

export default function KalshiPage() {
  const [category, setCategory] = useState("all");
  const [sortBy, setSortBy] = useState("volume_24h");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"markets" | "community">("markets");

  const marketsQuery = useQuery({
    queryKey: ["kalshi-markets"],
    queryFn: () => getKalshiMarkets(200, "all", undefined, 0), // show all markets
    staleTime: 60000, // 1 minute
  });

  const isLoading = marketsQuery.isLoading;
  const error = marketsQuery.error;

  // Filter and sort markets
  let displayMarkets = marketsQuery.data?.markets || [];

  // Apply search filter
  if (searchQuery) {
    displayMarkets = displayMarkets.filter(
      (market) =>
        market.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
        market.title?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }

  // Apply category filter
  displayMarkets = filterMarketsByCategory(displayMarkets, category);

  // Apply sorting
  displayMarkets = sortMarkets(displayMarkets, sortBy);

  const handleRefresh = () => {
    marketsQuery.refetch();
  };

  return (
    <div className="container py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold">Kalshi Markets</h1>
          <Badge variant="secondary" className="text-sm">
            CFTC Regulated
          </Badge>
        </div>
        <p className="text-muted-foreground">
          Explore prediction markets on Kalshi - trade on real-world events
        </p>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex flex-wrap gap-2 mb-6"
      >
        <Button
          variant={activeTab === "markets" ? "default" : "outline"}
          onClick={() => setActiveTab("markets")}
          className="flex items-center gap-2"
        >
          <BarChart3 className="h-4 w-4" />
          Market Explorer
        </Button>
        <Button
          variant={activeTab === "community" ? "default" : "outline"}
          onClick={() => setActiveTab("community")}
          className="flex items-center gap-2"
        >
          <Users className="h-4 w-4" />
          Community Leaderboard
          <Badge variant="secondary" className="ml-1 text-xs">
            Soon
          </Badge>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleRefresh}
          className="ml-auto"
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
        </Button>
      </motion.div>

      {activeTab === "markets" && (
        <>
          {/* Info Banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6 p-4 bg-primary/5 rounded-lg border border-primary/20"
          >
            <div className="flex items-center gap-2 text-sm">
              <Zap className="h-4 w-4 text-primary" />
              <span className="font-medium">
                Showing live markets from Kalshi API
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {displayMarkets.length} markets available
            </p>
          </motion.div>

          {/* Filters */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex flex-col sm:flex-row gap-4 mb-6"
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search markets by ticker or title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                {sortOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </motion.div>

          {/* Category Filters */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
            className="flex flex-wrap gap-2 mb-6"
          >
            {categoryFilters.map((filter) => (
              <Button
                key={filter.value}
                variant={category === filter.value ? "default" : "outline"}
                size="sm"
                onClick={() => setCategory(filter.value)}
                className="flex items-center gap-2"
              >
                <filter.icon className="h-4 w-4" />
                {filter.label}
              </Button>
            ))}
          </motion.div>

          {/* Loading State */}
          {isLoading && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="h-48 bg-muted animate-pulse rounded-lg"
                />
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-12">
              <p className="text-destructive mb-4">Failed to load markets</p>
              <p className="text-sm text-muted-foreground mb-4">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
              <Button onClick={handleRefresh}>Retry</Button>
            </div>
          )}

          {/* Markets Grid */}
          {!isLoading && !error && displayMarkets.length > 0 && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {displayMarkets.map((market, index) => (
                <KalshiMarketCard
                  key={market.ticker}
                  market={market}
                  index={index}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && displayMarkets.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">No markets found</p>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search or filters
              </p>
            </div>
          )}

          {/* Stats Summary */}
          {!isLoading && !error && displayMarkets.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-8 text-center text-sm text-muted-foreground"
            >
              <p>
                Showing {displayMarkets.length} of{" "}
                {marketsQuery.data?.markets?.length || 0} markets
              </p>
            </motion.div>
          )}
        </>
      )}

      {activeTab === "community" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <Users className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold mb-2">Community Leaderboard</h2>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Connect your Kalshi account to join the community leaderboard and see
            how you rank against other traders.
          </p>
          <Button disabled>
            Connect Kalshi Account
            <Badge variant="secondary" className="ml-2">
              Coming Soon
            </Badge>
          </Button>
        </motion.div>
      )}
    </div>
  );
}
