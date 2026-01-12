"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search,
  TrendingUp,
  Activity,
  DollarSign,
  Zap,
  RefreshCw,
  Wallet,
  Loader2,
} from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TraderCard } from "@/components/trader/TraderCard";
import { DiscoveredTraderCard } from "@/components/trader/DiscoveredTraderCard";
import {
  getTraders,
  discoverPolymarketTraders,
  getLiveLeaderboard,
  searchTraders,
  type Trader,
  type DiscoveredTrader,
} from "@/lib/api";

const sortOptions = [
  { value: "roi", label: "ROI", icon: TrendingUp },
  { value: "win_rate", label: "Win Rate", icon: Activity },
  { value: "total_volume", label: "Volume", icon: DollarSign },
];

const dataSourceOptions = [
  {
    value: "live",
    label: "Live Polymarket",
    icon: Zap,
    description: "Real-time data from Polymarket",
  },
  {
    value: "discover",
    label: "High Win Rate",
    icon: TrendingUp,
    description: "Traders with 55%+ win rate",
  },
  {
    value: "cached",
    label: "Cached Data",
    icon: Wallet,
    description: "Previously synced traders",
  },
];

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function LeaderboardPage() {
  const [dataSource, setDataSource] = useState<"live" | "discover" | "cached">(
    "live"
  );
  const [sortBy, setSortBy] = useState("roi");
  const [searchQuery, setSearchQuery] = useState("");
  const [minWinRate, setMinWinRate] = useState(55);
  const [minTrades, setMinTrades] = useState(20);

  // Debounce search query for API calls
  const debouncedSearch = useDebounce(searchQuery, 500);

  // Determine if search should use API (for address searches)
  const isAddressSearch =
    debouncedSearch.startsWith("0x") && debouncedSearch.length >= 4;
  const shouldUseApiSearch = debouncedSearch.length >= 3;

  // Query for cached traders
  const cachedQuery = useQuery({
    queryKey: ["traders", sortBy],
    queryFn: () => getTraders(50, 0, sortBy),
    enabled: dataSource === "cached" && !shouldUseApiSearch,
  });

  // Query for live Polymarket leaderboard
  const liveQuery = useQuery({
    queryKey: ["live-leaderboard"],
    queryFn: () => getLiveLeaderboard(50, 0),
    enabled: dataSource === "live" && !shouldUseApiSearch,
    staleTime: 60000, // 1 minute
  });

  // Query for discovered high-win-rate traders
  const discoverQuery = useQuery({
    queryKey: ["discover-traders", minWinRate, minTrades],
    queryFn: () => discoverPolymarketTraders(minWinRate, minTrades, 30),
    enabled: dataSource === "discover" && !shouldUseApiSearch,
    staleTime: 60000,
  });

  // Query for API search (searches Polymarket for any address)
  const searchQuery_api = useQuery({
    queryKey: ["search-traders", debouncedSearch],
    queryFn: () => searchTraders(debouncedSearch, 30),
    enabled: shouldUseApiSearch,
    staleTime: 30000, // 30 seconds
  });

  const isLoading =
    (shouldUseApiSearch && searchQuery_api.isLoading) ||
    (!shouldUseApiSearch &&
      ((dataSource === "cached" && cachedQuery.isLoading) ||
        (dataSource === "live" && liveQuery.isLoading) ||
        (dataSource === "discover" && discoverQuery.isLoading)));

  const error =
    (shouldUseApiSearch && searchQuery_api.error) ||
    (!shouldUseApiSearch &&
      ((dataSource === "cached" && cachedQuery.error) ||
        (dataSource === "live" && liveQuery.error) ||
        (dataSource === "discover" && discoverQuery.error)));

  // Get filtered/search results
  const getDisplayTraders = (): DiscoveredTrader[] | undefined => {
    // If using API search
    if (shouldUseApiSearch) {
      return searchQuery_api.data?.traders;
    }

    // Otherwise filter locally
    const data =
      dataSource === "live" ? liveQuery.data : discoverQuery.data;
    if (!data) return undefined;

    if (!searchQuery) return data.traders;

    return data.traders.filter(
      (trader) =>
        trader.wallet_address
          .toLowerCase()
          .includes(searchQuery.toLowerCase()) ||
        trader.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const getFilteredCachedTraders = (): Trader[] | undefined => {
    if (dataSource !== "cached" || !cachedQuery.data) return undefined;
    if (!searchQuery) return cachedQuery.data.traders;
    return cachedQuery.data.traders.filter((trader) =>
      trader.wallet_address.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const displayTraders = getDisplayTraders();
  const filteredCachedTraders = getFilteredCachedTraders();

  const handleRefresh = () => {
    if (shouldUseApiSearch) {
      searchQuery_api.refetch();
    } else if (dataSource === "live") {
      liveQuery.refetch();
    } else if (dataSource === "discover") {
      discoverQuery.refetch();
    } else {
      cachedQuery.refetch();
    }
  };

  return (
    <div className="container py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">Top Traders</h1>
        <p className="text-muted-foreground">
          Discover and copy the most successful Polymarket traders
        </p>
      </motion.div>

      {/* Data Source Tabs */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex flex-wrap gap-2 mb-6"
      >
        {dataSourceOptions.map((option) => (
          <Button
            key={option.value}
            variant={
              !shouldUseApiSearch && dataSource === option.value
                ? "default"
                : "outline"
            }
            onClick={() => {
              setDataSource(option.value as typeof dataSource);
              setSearchQuery("");
            }}
            className="flex items-center gap-2"
          >
            <option.icon className="h-4 w-4" />
            {option.label}
          </Button>
        ))}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleRefresh}
          className="ml-auto"
          disabled={isLoading}
        >
          <RefreshCw
            className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
          />
        </Button>
      </motion.div>

      {/* Search Info Banner */}
      {shouldUseApiSearch && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20"
        >
          <div className="flex items-center gap-2 text-sm">
            <Search className="h-4 w-4 text-blue-500" />
            <span className="font-medium">
              Searching Polymarket for &quot;{debouncedSearch}&quot;
            </span>
            {searchQuery_api.isLoading && (
              <Loader2 className="h-4 w-4 animate-spin ml-2" />
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {isAddressSearch
              ? "Looking up wallet address on Polymarket..."
              : "Searching traders by name..."}
          </p>
        </motion.div>
      )}

      {/* Data Source Info */}
      {!shouldUseApiSearch && dataSource !== "cached" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6 p-4 bg-primary/5 rounded-lg border border-primary/20"
        >
          <div className="flex items-center gap-2 text-sm">
            <Zap className="h-4 w-4 text-primary" />
            <span className="font-medium">
              {dataSource === "live"
                ? "Showing live data from Polymarket API"
                : "Showing high win-rate traders (55%+ win rate, 20+ trades)"}
            </span>
          </div>
          {(liveQuery.data || discoverQuery.data) && (
            <p className="text-xs text-muted-foreground mt-1">
              Last updated:{" "}
              {new Date(
                (dataSource === "live"
                  ? liveQuery.data?.last_updated
                  : discoverQuery.data?.last_updated) || ""
              ).toLocaleString()}
            </p>
          )}
        </motion.div>
      )}

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-4 mb-8"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search any wallet address (0x...) or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        {!shouldUseApiSearch && dataSource === "cached" && (
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex items-center gap-2">
                    <option.icon className="h-4 w-4" />
                    {option.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </motion.div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="h-64 bg-muted animate-pulse rounded-lg"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-12">
          <p className="text-destructive mb-4">Failed to load traders</p>
          <p className="text-sm text-muted-foreground mb-4">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <Button onClick={handleRefresh}>Retry</Button>
        </div>
      )}

      {/* Cached Traders Grid */}
      {!shouldUseApiSearch &&
        dataSource === "cached" &&
        filteredCachedTraders && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCachedTraders.map((trader, index) => (
              <TraderCard
                key={trader.wallet_address}
                trader={trader}
                rank={index + 1}
              />
            ))}
          </div>
        )}

      {/* Discovered/Live/Search Traders Grid */}
      {(shouldUseApiSearch || dataSource !== "cached") && displayTraders && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayTraders.map((trader, index) => (
            <DiscoveredTraderCard
              key={trader.wallet_address}
              trader={trader}
              index={index}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading &&
        !error &&
        ((shouldUseApiSearch && displayTraders?.length === 0) ||
          (!shouldUseApiSearch &&
            dataSource === "cached" &&
            filteredCachedTraders?.length === 0) ||
          (!shouldUseApiSearch &&
            dataSource !== "cached" &&
            displayTraders?.length === 0)) && (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No traders found</p>
            {shouldUseApiSearch ? (
              <p className="text-sm text-muted-foreground">
                No trading history found for this address. Make sure it&apos;s a
                valid Polymarket trader.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Try adjusting the filters or check back later for updated data
              </p>
            )}
          </div>
        )}

      {/* Stats Summary */}
      {!isLoading && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 text-center text-sm text-muted-foreground"
        >
          {shouldUseApiSearch && searchQuery_api.data && (
            <p>
              Found {displayTraders?.length || 0} traders matching &quot;
              {debouncedSearch}&quot;
            </p>
          )}
          {!shouldUseApiSearch && dataSource === "cached" && cachedQuery.data && (
            <p>
              Showing {filteredCachedTraders?.length || 0} of{" "}
              {cachedQuery.data.total} cached traders
            </p>
          )}
          {!shouldUseApiSearch && dataSource === "live" && liveQuery.data && (
            <p>
              Showing {displayTraders?.length || 0} of {liveQuery.data.total}{" "}
              live traders from Polymarket
            </p>
          )}
          {!shouldUseApiSearch &&
            dataSource === "discover" &&
            discoverQuery.data && (
              <p>
                Found {displayTraders?.length || 0} traders with high win rates
              </p>
            )}
        </motion.div>
      )}
    </div>
  );
}
