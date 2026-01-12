import { useCallback, useEffect, useState } from "react";
import { useAccount, useSignMessage, useDisconnect } from "wagmi";
import { SiweMessage } from "siwe";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api";
import { useToast } from "./use-toast";

interface NonceResponse {
  nonce: string;
}

interface AuthResponse {
  token: string;
  user: {
    id: string;
    wallet_address: string;
    safe_address: string | null;
    created_at: string;
  };
}

export function useAuth() {
  const { address, isConnected, chain } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const { disconnect } = useDisconnect();
  const { token, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const { toast } = useToast();
  const [isSigningIn, setIsSigningIn] = useState(false);

  // Auto sign-in when wallet connects
  const signIn = useCallback(async () => {
    if (!address || !chain) return;

    setIsSigningIn(true);
    try {
      // Get nonce from backend
      const { nonce } = await api.get<NonceResponse>("/api/auth/nonce");

      // Create SIWE message with time bounds
      const message = new SiweMessage({
        domain: window.location.host,
        address,
        statement: "Sign in to MetamonMarket",
        uri: window.location.origin,
        version: "1",
        chainId: chain.id,
        nonce,
        issuedAt: new Date().toISOString(),
      });

      const messageStr = message.prepareMessage();

      // Sign message
      const signature = await signMessageAsync({ message: messageStr });

      // Verify with backend
      const authResponse = await api.post<AuthResponse>(
        "/api/auth/verify",
        { message: messageStr, signature }
      );

      // Store auth state
      setAuth(authResponse.token, address);

      toast({
        title: "Signed in successfully",
        description: "You can now copy traders and manage your portfolio.",
      });
    } catch (error) {
      // Error is shown to user via toast - no console logging in production
      toast({
        title: "Sign in failed",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsSigningIn(false);
    }
  }, [address, chain, signMessageAsync, setAuth, toast]);

  // Sign out
  const signOut = useCallback(async () => {
    try {
      if (token) {
        await api.post("/api/auth/logout", undefined, token);
      }
    } catch {
      // Ignore logout errors
    } finally {
      clearAuth();
      disconnect();
      toast({
        title: "Signed out",
        description: "You have been signed out successfully.",
      });
    }
  }, [token, clearAuth, disconnect, toast]);

  // Clear auth when wallet disconnects
  useEffect(() => {
    if (!isConnected && isAuthenticated) {
      clearAuth();
    }
  }, [isConnected, isAuthenticated, clearAuth]);

  // Validate token on mount
  useEffect(() => {
    async function validateToken() {
      if (!token || !isAuthenticated) return;

      try {
        await api.get("/api/auth/me", token);
      } catch {
        // Token is invalid, clear auth
        clearAuth();
      }
    }

    validateToken();
  }, [token, isAuthenticated, clearAuth]);

  return {
    address,
    isConnected,
    isAuthenticated,
    isSigningIn,
    token,
    signIn,
    signOut,
  };
}
