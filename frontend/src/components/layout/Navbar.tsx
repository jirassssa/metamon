"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Menu, Moon, Sun, Wallet, LogIn, Loader2 } from "lucide-react";
import { useTheme } from "next-themes";
import { useConnect } from "wagmi";
import { injected } from "wagmi/connectors";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, formatAddress } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/portfolio", label: "Portfolio" },
];

export function Navbar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const { connect } = useConnect();
  const {
    address,
    isConnected,
    isAuthenticated,
    isSigningIn,
    signIn,
    signOut,
  } = useAuth();

  const handleConnect = async () => {
    connect({ connector: injected() });
  };

  // Auto sign-in after wallet connects
  const hasTriedSignIn = useRef(false);
  useEffect(() => {
    // If wallet is connected but not authenticated, auto sign-in
    if (isConnected && address && !isAuthenticated && !isSigningIn && !hasTriedSignIn.current) {
      hasTriedSignIn.current = true;
      signIn();
    }
    // Reset when disconnected
    if (!isConnected) {
      hasTriedSignIn.current = false;
    }
  }, [isConnected, address, isAuthenticated, isSigningIn, signIn]);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container flex h-20 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center">
          <Image
            src="/logo-banner.png"
            alt="MetamonMarket"
            width={715}
            height={349}
            className="h-32 w-auto object-contain"
            priority
            unoptimized
          />
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative px-4 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {item.label}
                {isActive && (
                  <motion.div
                    layoutId="navbar-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                    initial={false}
                    transition={{
                      type: "spring",
                      stiffness: 500,
                      damping: 30,
                    }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right side actions */}
        <div className="flex items-center space-x-2">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" aria-hidden="true" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" aria-hidden="true" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Connect wallet / Account */}
          {isConnected && address ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="gap-2"
                  aria-label={`Wallet ${formatAddress(address)}${isAuthenticated ? ", signed in" : ", not signed in"}`}
                >
                  <Wallet className="h-4 w-4" aria-hidden="true" />
                  {formatAddress(address)}
                  {isAuthenticated && (
                    <span
                      className="w-2 h-2 rounded-full bg-green-500"
                      aria-label="Signed in"
                    />
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {!isAuthenticated && (
                  <>
                    <DropdownMenuItem onClick={signIn} disabled={isSigningIn}>
                      {isSigningIn ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <LogIn className="h-4 w-4 mr-2" />
                      )}
                      {isSigningIn ? "Signing in..." : "Sign In"}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem asChild>
                  <Link href="/portfolio">My Portfolio</Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={signOut}>
                  Disconnect
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button onClick={handleConnect} className="gap-2">
              <Wallet className="h-4 w-4" />
              Connect Wallet
            </Button>
          )}

          {/* Mobile menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon" aria-label="Open navigation menu">
                <Menu className="h-5 w-5" aria-hidden="true" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {navItems.map((item) => (
                <DropdownMenuItem key={item.href} asChild>
                  <Link href={item.href}>{item.label}</Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </nav>
    </header>
  );
}
