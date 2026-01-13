"use client";

import { useState, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useSearchParams } from "next/navigation";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  AlertCircle,
  ArrowDownToLine,
  ArrowUpFromLine,
  Copy,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { useSafePrivy } from "@/hooks/use-safe-privy";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { useToast } from "@/hooks/use-toast";

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

function DepositTab({ walletAddress }: { walletAddress: string | undefined }) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  const depositAddress = walletAddress || "0x...";

  const handleCopyAddress = () => {
    if (walletAddress) {
      navigator.clipboard.writeText(walletAddress);
      setCopied(true);
      toast({
        title: "Address Copied",
        description: "Deposit address copied to clipboard",
      });
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowDownToLine className="h-5 w-5" />
            Deposit USDC
          </CardTitle>
          <CardDescription>
            Send USDC (Polygon) to your wallet to start copy trading
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Your Deposit Address (Polygon Network)</Label>
            <div className="flex gap-2">
              <Input
                value={depositAddress}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopyAddress}
                disabled={!walletAddress}
              >
                {copied ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium">Important:</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>- Only send USDC on <strong>Polygon network</strong></li>
              <li>- Minimum deposit: $10 USDC</li>
              <li>- Deposits usually arrive within 1-2 minutes</li>
              <li>- Do not send other tokens to this address</li>
            </ul>
          </div>

          <Button variant="outline" className="w-full" asChild>
            <a
              href={`https://polygonscan.com/address/${walletAddress}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              View on PolygonScan
              <ExternalLink className="h-4 w-4 ml-2" />
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function WithdrawTab({ walletAddress, balance }: { walletAddress: string | undefined; balance: string }) {
  const { toast } = useToast();
  const [amount, setAmount] = useState("");
  const [withdrawAddress, setWithdrawAddress] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleWithdraw = async () => {
    if (!amount || !withdrawAddress) {
      toast({
        title: "Missing Information",
        description: "Please enter amount and withdrawal address",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);
    // TODO: Implement actual withdrawal via backend API
    setTimeout(() => {
      toast({
        title: "Withdrawal Initiated",
        description: `Withdrawing ${amount} USDC to ${formatAddress(withdrawAddress)}`,
      });
      setIsProcessing(false);
      setAmount("");
      setWithdrawAddress("");
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowUpFromLine className="h-5 w-5" />
            Withdraw USDC
          </CardTitle>
          <CardDescription>
            Withdraw your USDC to any Polygon wallet
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground">Available Balance</p>
            <p className="text-2xl font-bold">{balance} USDC</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="withdraw-amount">Amount (USDC)</Label>
            <Input
              id="withdraw-amount"
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="withdraw-address">Withdrawal Address</Label>
            <Input
              id="withdraw-address"
              placeholder="0x..."
              value={withdrawAddress}
              onChange={(e) => setWithdrawAddress(e.target.value)}
              className="font-mono"
            />
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium">Withdrawal Info:</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>- Network: Polygon</li>
              <li>- Minimum withdrawal: $10 USDC</li>
              <li>- Processing time: 1-5 minutes</li>
              <li>- Network fee: ~$0.01</li>
            </ul>
          </div>

          <Button
            className="w-full"
            onClick={handleWithdraw}
            disabled={isProcessing || !amount || !withdrawAddress}
          >
            {isProcessing ? "Processing..." : "Withdraw"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function PortfolioContent() {
  const searchParams = useSearchParams();
  const defaultTab = searchParams.get("tab") || "overview";

  const { ready, authenticated, user, login } = useSafePrivy();
  const walletAddress = user?.wallet?.address;

  // Mock token for now - in real app, get from Privy auth
  const token = authenticated ? "mock-token" : null;

  const { data: portfolio, isLoading: portfolioLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => getPortfolio(token!),
    enabled: authenticated && !!token,
  });

  const { data: copies } = useQuery({
    queryKey: ["copies"],
    queryFn: () => getCopies(token!),
    enabled: authenticated && !!token,
  });

  const { data: positions } = useQuery({
    queryKey: ["portfolio-positions"],
    queryFn: () => getPortfolioPositions(token!),
    enabled: authenticated && !!token,
  });

  if (!ready) {
    return (
      <div className="container py-16">
        <div className="animate-pulse space-y-8">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="container py-16">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h1 className="text-2xl font-bold mb-2">Sign In Required</h1>
          <p className="text-muted-foreground mb-6">
            Please sign in to access your portfolio and start copy trading.
          </p>
          <Button onClick={login} size="lg">
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  const totalPnl = portfolio ? parseFloat(portfolio.total_pnl) : 0;
  const balance = portfolio?.total_value || "0";

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
          Manage your funds and track copy trading performance
        </p>
      </motion.div>

      {/* Tabs */}
      <Tabs defaultValue={defaultTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="deposit">Deposit</TabsTrigger>
          <TabsTrigger value="withdraw">Withdraw</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Stats Cards */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-4"
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Value</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {portfolio ? formatCurrency(portfolio.total_value) : "$0.00"}
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
                  {portfolio ? formatCurrency(portfolio.total_pnl) : "$0.00"}
                </div>
                <p className="text-xs text-muted-foreground">
                  {portfolio ? formatPercent(portfolio.total_pnl_percentage) : "0%"}
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
                  {portfolio?.open_positions ?? 0}
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
                  {copies?.total ?? 0}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Active Copies */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Active Copies</h2>
              <Button variant="outline" size="sm" asChild>
                <Link href="/leaderboard">Find Traders</Link>
              </Button>
            </div>

            {!copies?.copies || copies.copies.length === 0 ? (
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
                {copies.copies.map((copy) => (
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

            {!positions?.positions || positions.positions.filter((p) => p.status === "open").length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No open positions</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {positions.positions
                  .filter((p) => p.status === "open")
                  .map((position) => (
                    <PositionCard key={position.id} position={position} />
                  ))}
              </div>
            )}
          </motion.div>
        </TabsContent>

        {/* Deposit Tab */}
        <TabsContent value="deposit">
          <DepositTab walletAddress={walletAddress} />
        </TabsContent>

        {/* Withdraw Tab */}
        <TabsContent value="withdraw">
          <WithdrawTab walletAddress={walletAddress} balance={balance} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function PortfolioPage() {
  return (
    <Suspense fallback={
      <div className="container py-16">
        <div className="animate-pulse space-y-8">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    }>
      <PortfolioContent />
    </Suspense>
  );
}
