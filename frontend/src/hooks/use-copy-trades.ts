"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useAccount, useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { parseUnits, encodeFunctionData } from "viem";
import { useAuthStore } from "@/stores/auth-store";
import { useToast } from "./use-toast";

// Polymarket CLOB Contract on Polygon
const CLOB_CONTRACT = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045" as const;

// USDC Contract on Polygon
const USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174" as const;

// ERC20 ABI for approval
const ERC20_ABI = [
  {
    name: "approve",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ name: "", type: "bool" }],
  },
  {
    name: "allowance",
    type: "function",
    stateMutability: "view",
    inputs: [
      { name: "owner", type: "address" },
      { name: "spender", type: "address" },
    ],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;

// Simplified CLOB ABI for placing orders
const CLOB_ABI = [
  {
    name: "fillOrder",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [
      { name: "order", type: "tuple", components: [
        { name: "salt", type: "uint256" },
        { name: "maker", type: "address" },
        { name: "signer", type: "address" },
        { name: "taker", type: "address" },
        { name: "tokenId", type: "uint256" },
        { name: "makerAmount", type: "uint256" },
        { name: "takerAmount", type: "uint256" },
        { name: "expiration", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "feeRateBps", type: "uint256" },
        { name: "side", type: "uint8" },
        { name: "signatureType", type: "uint8" },
      ]},
      { name: "fillAmount", type: "uint256" },
    ],
    outputs: [],
  },
] as const;

export interface PendingCopyTrade {
  id: string;
  user_id: string;
  copy_config_id: string;
  trader_address: string;
  market_id: string;
  market_title: string;
  market_slug: string;
  event_slug: string;
  side: string;
  size: string;
  price: string;
  original_trade_id: string;
  timestamp: number;
  created_at: string;
  status: string;
}

type CopyTradeEventType =
  | "connected"
  | "heartbeat"
  | "pong"
  | "pending_trades"
  | "new_copy_trade"
  | "trade_status";

interface CopyTradeMessage {
  type: CopyTradeEventType;
  trades?: PendingCopyTrade[];
  trade?: PendingCopyTrade;
  trade_id?: string;
  status?: string;
  tx_hash?: string;
  data?: {
    message?: string;
  };
}

interface UseCopyTradesOptions {
  onNewTrade?: (trade: PendingCopyTrade) => void;
  onTradeExecuted?: (tradeId: string, txHash?: string) => void;
  onTradeSkipped?: (tradeId: string) => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "ws") || "ws://localhost:8000";

export function useCopyTrades(options: UseCopyTradesOptions = {}) {
  const { token, isAuthenticated } = useAuthStore();
  const { address, isConnected: isWalletConnected } = useAccount();
  const { toast } = useToast();

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const [isConnected, setIsConnected] = useState(false);
  const [pendingTrades, setPendingTrades] = useState<PendingCopyTrade[]>([]);
  const [executingTradeId, setExecutingTradeId] = useState<string | null>(null);
  const [needsApproval, setNeedsApproval] = useState(false);

  // Contract write hooks
  const { writeContract: approveUsdc, data: approveHash, isPending: isApproving } = useWriteContract();
  const { writeContract: executeTrade, data: tradeHash, isPending: isExecuting } = useWriteContract();

  // Wait for approval transaction
  const { isLoading: isWaitingApproval, isSuccess: approvalSuccess } = useWaitForTransactionReceipt({
    hash: approveHash,
  });

  // Wait for trade transaction
  const { isLoading: isWaitingTrade, isSuccess: tradeSuccess } = useWaitForTransactionReceipt({
    hash: tradeHash,
  });

  // Handle approval success
  useEffect(() => {
    if (approvalSuccess && needsApproval) {
      setNeedsApproval(false);
      toast({
        title: "USDC Approved",
        description: "You can now execute copy trades",
      });
    }
  }, [approvalSuccess, needsApproval, toast]);

  // Handle trade execution success
  useEffect(() => {
    if (tradeSuccess && executingTradeId && tradeHash) {
      // Notify backend
      sendMessage({ type: "execute_trade", trade_id: executingTradeId, tx_hash: tradeHash });
      toast({
        title: "Trade Executed",
        description: "Copy trade successfully executed on-chain",
      });
      optionsRef.current.onTradeExecuted?.(executingTradeId, tradeHash);
      setExecutingTradeId(null);

      // Remove from pending
      setPendingTrades(prev => prev.filter(t => t.id !== executingTradeId));
    }
  }, [tradeSuccess, executingTradeId, tradeHash, toast]);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const connect = useCallback(() => {
    if (!token || !isAuthenticated) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/api/ws/copy-trades?token=${token}`);

      ws.onopen = () => {
        setIsConnected(true);

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const message: CopyTradeMessage = JSON.parse(event.data);

          switch (message.type) {
            case "connected":
              break;

            case "heartbeat":
            case "pong":
              break;

            case "pending_trades":
              if (message.trades) {
                setPendingTrades(message.trades.filter(t => t.status === "pending"));
              }
              break;

            case "new_copy_trade":
              if (message.trade) {
                setPendingTrades(prev => [...prev, message.trade!]);
                optionsRef.current.onNewTrade?.(message.trade);
                toast({
                  title: "New Copy Trade",
                  description: `${message.trade.side} ${message.trade.market_title} - $${message.trade.size}`,
                });
              }
              break;

            case "trade_status":
              if (message.status === "executed") {
                setPendingTrades(prev => prev.filter(t => t.id !== message.trade_id));
              } else if (message.status === "skipped") {
                setPendingTrades(prev => prev.filter(t => t.id !== message.trade_id));
                optionsRef.current.onTradeSkipped?.(message.trade_id!);
              }
              break;
          }
        } catch {
          // Ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        clearInterval(pingIntervalRef.current);

        // Attempt reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // Connection failures handled by onclose
    }
  }, [token, isAuthenticated, toast]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Connect when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, token, connect, disconnect]);

  // Approve USDC spending
  const approveUsdcSpending = useCallback(async (amount: string) => {
    if (!isWalletConnected || !address) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your wallet first",
        variant: "destructive",
      });
      return;
    }

    try {
      // Approve max amount for convenience
      const approveAmount = parseUnits("1000000", 6); // 1M USDC

      approveUsdc({
        address: USDC_CONTRACT,
        abi: ERC20_ABI,
        functionName: "approve",
        args: [CLOB_CONTRACT, approveAmount],
      });

      setNeedsApproval(true);
    } catch (error) {
      toast({
        title: "Approval failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  }, [isWalletConnected, address, approveUsdc, toast]);

  // Execute a copy trade
  const executeTradeOnChain = useCallback(async (trade: PendingCopyTrade) => {
    if (!isWalletConnected || !address) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your wallet first",
        variant: "destructive",
      });
      return;
    }

    try {
      setExecutingTradeId(trade.id);

      // Note: In production, you would need to:
      // 1. Fetch the actual order from Polymarket's order book
      // 2. Sign and submit the order to the CLOB contract
      // For now, we simulate by marking as executed via the backend

      // This is a simplified version - real implementation needs:
      // - Order matching with Polymarket's relayer
      // - Proper order signing
      // - Gas estimation

      toast({
        title: "Executing trade...",
        description: `${trade.side} ${trade.market_title}`,
      });

      // Mark as executed in backend (for demo purposes)
      // In production, this would be called after actual tx confirmation
      sendMessage({ type: "execute_trade", trade_id: trade.id, tx_hash: "demo-tx" });

      // Remove from pending
      setPendingTrades(prev => prev.filter(t => t.id !== trade.id));
      setExecutingTradeId(null);

      toast({
        title: "Trade recorded",
        description: "Copy trade has been recorded. Full on-chain execution requires Polymarket relayer integration.",
      });

    } catch (error) {
      toast({
        title: "Trade execution failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
      setExecutingTradeId(null);
    }
  }, [isWalletConnected, address, sendMessage, toast]);

  // Skip a pending trade
  const skipTrade = useCallback((tradeId: string) => {
    sendMessage({ type: "skip_trade", trade_id: tradeId });
    setPendingTrades(prev => prev.filter(t => t.id !== tradeId));
  }, [sendMessage]);

  // Refresh pending trades
  const refreshPendingTrades = useCallback(() => {
    sendMessage({ type: "get_pending" });
  }, [sendMessage]);

  return {
    isConnected,
    pendingTrades,
    executingTradeId,
    isApproving: isApproving || isWaitingApproval,
    isExecuting: isExecuting || isWaitingTrade,
    needsApproval,
    approveUsdcSpending,
    executeTradeOnChain,
    skipTrade,
    refreshPendingTrades,
    disconnect,
  };
}
