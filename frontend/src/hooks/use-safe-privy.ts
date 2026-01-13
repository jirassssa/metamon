"use client";

import { usePrivy, useWallets } from "@privy-io/react-auth";

// Safe wrapper for usePrivy that returns default values if Privy context isn't available
export function useSafePrivy() {
  try {
    const privy = usePrivy();
    return privy;
  } catch {
    // Return minimal default values if Privy context isn't available
    return {
      ready: true,
      authenticated: false,
      user: null,
      login: () => {
        alert("Login is not available. Please try again later.");
      },
      logout: () => {},
    } as unknown as ReturnType<typeof usePrivy>;
  }
}

// Safe wrapper for useWallets
export function useSafeWallets() {
  try {
    const wallets = useWallets();
    return wallets;
  } catch {
    return {
      wallets: [],
      ready: true,
    } as ReturnType<typeof useWallets>;
  }
}
