"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState, useEffect, Component, ReactNode } from "react";
import { PrivyProvider } from "@privy-io/react-auth";
import { WebSocketProvider } from "@/components/providers/WebSocketProvider";

const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID || "cmkbub70x08mrl20dzjl5u6y1";

// Error boundary to catch Privy initialization errors
class PrivyErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode; fallback: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Inner providers without Privy (fallback)
function InnerProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem
        disableTransitionOnChange
      >
        <WebSocketProvider>{children}</WebSocketProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Don't render Privy until mounted to avoid SSR issues
  if (!mounted) {
    return <InnerProviders>{children}</InnerProviders>;
  }

  return (
    <PrivyErrorBoundary fallback={<InnerProviders>{children}</InnerProviders>}>
      <PrivyProvider
        appId={PRIVY_APP_ID}
        config={{
          loginMethods: ["email", "twitter"],
          appearance: {
            theme: "dark",
            accentColor: "#7c3aed",
            logo: "/icon.png",
            showWalletLoginFirst: false,
          },
          embeddedWallets: {
            ethereum: {
              createOnLogin: "users-without-wallets",
            },
          },
        }}
      >
        <InnerProviders>{children}</InnerProviders>
      </PrivyProvider>
    </PrivyErrorBoundary>
  );
}
