import type { Metadata } from "next";
import { Inter } from "next/font/google";
import nextDynamic from "next/dynamic";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui/toaster";
import { ErrorBoundary } from "@/components/error-boundary";

// Force dynamic rendering to ensure environment variables are available
export const dynamic = "force-dynamic";

// Dynamic imports for components that use Privy hooks (client-only)
const Navbar = nextDynamic(
  () => import("@/components/layout/Navbar").then((mod) => ({ default: mod.Navbar })),
  { ssr: false }
);
const PendingCopyTrades = nextDynamic(
  () => import("@/components/copy/PendingCopyTrades").then((mod) => ({ default: mod.PendingCopyTrades })),
  { ssr: false }
);

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MetamonMarket | Polymarket Copy Trading",
  description: "Copy the best Polymarket traders automatically",
  icons: {
    icon: "/icon.png",
    apple: "/icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1">
              <ErrorBoundary>{children}</ErrorBoundary>
            </main>
          </div>
          <Toaster />
          <PendingCopyTrades />
        </Providers>
      </body>
    </html>
  );
}
