"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Bell, Check, X, Loader2, ExternalLink, ArrowUpRight, ArrowDownRight } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCopyTrades, type PendingCopyTrade } from "@/hooks/use-copy-trades";
import { formatCurrency, formatAddress } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

function TradeCard({
  trade,
  onExecute,
  onSkip,
  isExecuting,
}: {
  trade: PendingCopyTrade;
  onExecute: () => void;
  onSkip: () => void;
  isExecuting: boolean;
}) {
  const isBuy = trade.side === "BUY";
  const price = parseFloat(trade.price);
  const size = parseFloat(trade.size);
  const timeAgo = formatDistanceToNow(new Date(trade.created_at), { addSuffix: true });

  // Build Polymarket URL
  const polymarketUrl = trade.event_slug
    ? `https://polymarket.com/event/${trade.event_slug}#${trade.market_slug}`
    : `https://polymarket.com/event/${trade.market_slug}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="border rounded-lg p-4 bg-card"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={isBuy ? "success" : "danger"} className="text-xs">
              {isBuy ? (
                <ArrowUpRight className="h-3 w-3 mr-1" />
              ) : (
                <ArrowDownRight className="h-3 w-3 mr-1" />
              )}
              {trade.side}
            </Badge>
            <span className="text-xs text-muted-foreground">{timeAgo}</span>
          </div>

          <a
            href={polymarketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-sm line-clamp-2 hover:text-primary hover:underline"
          >
            {trade.market_title}
            <ExternalLink className="h-3 w-3 inline ml-1" />
          </a>

          <div className="flex items-center gap-4 mt-2 text-sm">
            <div>
              <span className="text-muted-foreground">Size:</span>{" "}
              <span className="font-semibold">{formatCurrency(size)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Price:</span>{" "}
              <span className="font-semibold">{(price * 100).toFixed(0)}¢</span>
            </div>
          </div>

          <div className="text-xs text-muted-foreground mt-1">
            Copying: {formatAddress(trade.trader_address)}
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onSkip}
            disabled={isExecuting}
          >
            <X className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            onClick={onExecute}
            disabled={isExecuting}
          >
            {isExecuting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export function PendingCopyTrades() {
  const {
    isConnected,
    pendingTrades,
    executingTradeId,
    isApproving,
    isExecuting,
    needsApproval,
    approveUsdcSpending,
    executeTradeOnChain,
    skipTrade,
    refreshPendingTrades,
  } = useCopyTrades();

  if (!isConnected) {
    return null;
  }

  if (pendingTrades.length === 0) {
    return null;
  }

  return (
    <Card className="fixed bottom-4 right-4 w-96 max-h-[60vh] overflow-hidden shadow-xl z-50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Bell className="h-4 w-4 text-primary" />
            Pending Copy Trades
            <Badge variant="secondary" className="ml-2">
              {pendingTrades.length}
            </Badge>
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshPendingTrades}
            className="text-xs"
          >
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 max-h-[50vh] overflow-y-auto">
        {needsApproval && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-sm">
            <p className="font-medium text-amber-600 mb-2">
              USDC Approval Required
            </p>
            <p className="text-xs text-muted-foreground mb-2">
              You need to approve USDC spending before executing copy trades.
            </p>
            <Button
              size="sm"
              onClick={() => approveUsdcSpending("1000000")}
              disabled={isApproving}
            >
              {isApproving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                "Approve USDC"
              )}
            </Button>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {pendingTrades.map((trade) => (
            <TradeCard
              key={trade.id}
              trade={trade}
              onExecute={() => executeTradeOnChain(trade)}
              onSkip={() => skipTrade(trade.id)}
              isExecuting={executingTradeId === trade.id || isExecuting}
            />
          ))}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
