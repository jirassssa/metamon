"use client";

import { createContext, useContext, ReactNode } from "react";
import { useWebSocket } from "@/hooks/use-websocket";

interface WebSocketContextValue {
  isConnected: boolean;
  reconnectAttempts: number;
  reconnect: () => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const ws = useWebSocket();

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocketContext must be used within WebSocketProvider");
  }
  return context;
}
