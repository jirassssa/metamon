import { useEffect, useRef, useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { useToast } from "./use-toast";

type WebSocketEventType =
  | "connected"
  | "heartbeat"
  | "position_update"
  | "position_opened"
  | "position_closed"
  | "copy_updated";

interface WebSocketMessage {
  type: WebSocketEventType;
  data: Record<string, unknown>;
}

interface UseWebSocketOptions {
  onPositionUpdate?: (data: Record<string, unknown>) => void;
  onPositionOpened?: (data: Record<string, unknown>) => void;
  onPositionClosed?: (data: Record<string, unknown>) => void;
  onCopyUpdated?: (data: Record<string, unknown>) => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "ws") || "ws://localhost:8000";

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { token, isAuthenticated } = useAuthStore();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Store options in ref to avoid dependency issues
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!token || !isAuthenticated) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/api/ws/positions?token=${token}`);

      ws.onopen = () => {
        setIsConnected(true);
        setReconnectAttempts(0);

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case "connected":
              break;

            case "heartbeat":
              break;

            case "position_update":
              optionsRef.current.onPositionUpdate?.(message.data);
              // Invalidate position queries to refresh data
              queryClient.invalidateQueries({ queryKey: ["portfolio-positions"] });
              break;

            case "position_opened":
              optionsRef.current.onPositionOpened?.(message.data);
              toast({
                title: "Position Opened",
                description: `New position copied: ${message.data.market_name}`,
              });
              queryClient.invalidateQueries({ queryKey: ["portfolio-positions"] });
              queryClient.invalidateQueries({ queryKey: ["portfolio"] });
              break;

            case "position_closed":
              optionsRef.current.onPositionClosed?.(message.data);
              toast({
                title: "Position Closed",
                description: `Position closed: ${message.data.market_name}`,
              });
              queryClient.invalidateQueries({ queryKey: ["portfolio-positions"] });
              queryClient.invalidateQueries({ queryKey: ["portfolio"] });
              break;

            case "copy_updated":
              optionsRef.current.onCopyUpdated?.(message.data);
              queryClient.invalidateQueries({ queryKey: ["copies"] });
              break;

            default:
              break;
          }
        } catch {
          // Ignore non-JSON messages (like "pong")
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        clearInterval(pingIntervalRef.current);

        // Attempt reconnect with exponential backoff + jitter
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts) * 1000 + Math.random() * 1000;
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // Connection failures handled by onclose with reconnect logic
    }
  }, [token, isAuthenticated, reconnectAttempts, queryClient, toast]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setReconnectAttempts(0);
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

  return {
    isConnected,
    reconnectAttempts,
    disconnect,
    reconnect: connect,
  };
}
