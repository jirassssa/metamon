"use client";

import { useCallback, useEffect } from "react";
import { useSafePrivy, useSafeWallets } from "@/hooks/use-safe-privy";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api";
import { useToast } from "./use-toast";

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
  const { ready, authenticated, user, logout: privyLogout } = useSafePrivy();
  const { wallets } = useSafeWallets();
  const { token, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const { toast } = useToast();

  // Get the first wallet address
  const wallet = wallets[0];
  const address = wallet?.address || user?.wallet?.address;
  const isConnected = authenticated && !!address;

  // Sync Privy auth with backend
  const syncAuth = useCallback(async () => {
    if (!authenticated || !address) return;

    try {
      // Try to authenticate with backend using Privy user info
      const authResponse = await api.post<AuthResponse>("/api/auth/privy", {
        wallet_address: address,
        privy_user_id: user?.id,
        email: user?.email?.address,
      });

      setAuth(authResponse.token, address);
    } catch {
      // If backend auth fails, still allow user to use app with Privy auth
      // Just won't have backend token for protected routes
    }
  }, [authenticated, address, user, setAuth]);

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
      privyLogout();
      toast({
        title: "Signed out",
        description: "You have been signed out successfully.",
      });
    }
  }, [token, clearAuth, privyLogout, toast]);

  // Clear auth when Privy disconnects
  useEffect(() => {
    if (ready && !authenticated && isAuthenticated) {
      clearAuth();
    }
  }, [ready, authenticated, isAuthenticated, clearAuth]);

  // Sync auth when Privy authenticates
  useEffect(() => {
    if (authenticated && address && !isAuthenticated) {
      syncAuth();
    }
  }, [authenticated, address, isAuthenticated, syncAuth]);

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
    isAuthenticated: authenticated,
    isSigningIn: !ready,
    token,
    signIn: syncAuth, // With Privy, signIn is automatic
    signOut,
  };
}
