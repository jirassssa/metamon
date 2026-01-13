"use client";

import { usePrivy, useWallets } from "@privy-io/react-auth";
import { useState, useEffect } from "react";

// Safe wrapper for usePrivy that returns default values if Privy context isn't available
export function useSafePrivy() {
  const [timedOut, setTimedOut] = useState(false);

  // Timeout after 3 seconds if Privy doesn't initialize
  useEffect(() => {
    const timer = setTimeout(() => {
      setTimedOut(true);
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  try {
    const privy = usePrivy();

    // If Privy is taking too long, return ready state anyway
    if (!privy.ready && timedOut) {
      return {
        ...privy,
        ready: true,
        authenticated: false,
        login: () => {
          console.warn("Privy is not configured. Please add your domain to Privy dashboard.");
          window.open("https://dashboard.privy.io", "_blank");
        },
      } as ReturnType<typeof usePrivy>;
    }

    return privy;
  } catch {
    // Return minimal default values if Privy context isn't available
    return {
      ready: true,
      authenticated: false,
      user: null,
      login: () => {
        console.warn("Privy is not configured. Please add your domain to Privy dashboard.");
        alert("Login is not available. Please contact the administrator to configure Privy.");
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
