"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Menu, Moon, Sun, User, LogOut, Loader2, Mail, Wallet, ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import { useTheme } from "next-themes";
import { useSafePrivy } from "@/hooks/use-safe-privy";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, formatAddress } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/leaderboard", label: "Polymarket" },
  { href: "/kalshi", label: "Kalshi" },
  { href: "/portfolio", label: "Portfolio" },
];

export function Navbar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const {
    ready,
    authenticated,
    user,
    login,
    logout,
  } = useSafePrivy();

  const userEmail = user?.email?.address;
  const userTwitter = user?.twitter?.username;
  const userWallet = user?.wallet?.address;
  const displayName = userTwitter ? `@${userTwitter}` : userEmail || (userWallet ? formatAddress(userWallet) : "User");

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

          {/* User account */}
          {!ready ? (
            <Button variant="outline" disabled>
              <Loader2 className="h-4 w-4 animate-spin" />
            </Button>
          ) : authenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="gap-2"
                >
                  <User className="h-4 w-4" aria-hidden="true" />
                  {displayName}
                  <span
                    className="w-2 h-2 rounded-full bg-green-500"
                    aria-label="Signed in"
                  />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-2 py-1.5 text-sm">
                  <p className="font-medium">{displayName}</p>
                  {userEmail && (
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {userEmail}
                    </p>
                  )}
                  {userWallet && (
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Wallet className="h-3 w-3" />
                      {formatAddress(userWallet)}
                    </p>
                  )}
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/portfolio" className="flex items-center gap-2">
                    <Wallet className="h-4 w-4" />
                    My Portfolio
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/portfolio?tab=deposit" className="flex items-center gap-2">
                    <ArrowDownToLine className="h-4 w-4" />
                    Deposit
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/portfolio?tab=withdraw" className="flex items-center gap-2">
                    <ArrowUpFromLine className="h-4 w-4" />
                    Withdraw
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-destructive">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button onClick={login} className="gap-2">
              <User className="h-4 w-4" />
              Sign In
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
