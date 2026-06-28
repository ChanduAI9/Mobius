"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Brain,
  Lightbulb,
  Search,
  Settings,
  LogOut,
  BookOpen,
  FolderKanban,
} from "lucide-react";
import clsx from "clsx";
import { clearTokens } from "@/lib/api";

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/memories", icon: Brain, label: "Memories" },
  { href: "/ideas", icon: Lightbulb, label: "Ideas" },
  { href: "/knowledge", icon: BookOpen, label: "Knowledge" },
  { href: "/projects", icon: FolderKanban, label: "Projects" },
  { href: "/search", icon: Search, label: "Search" },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    clearTokens();
    window.location.href = "/login";
  };

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-mobius-border bg-mobius-surface">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-mobius-border">
        <span className="text-2xl text-mobius-accent">◈</span>
        <span className="text-lg font-bold tracking-tight">MOBIUS</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              pathname === href
                ? "bg-mobius-elevated text-mobius-accent"
                : "text-mobius-muted hover:text-mobius-text hover:bg-mobius-elevated"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="border-t border-mobius-border px-3 py-4 space-y-1">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-mobius-muted hover:text-mobius-text hover:bg-mobius-elevated"
        >
          <Settings size={18} />
          Settings
        </Link>
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-mobius-muted hover:text-mobius-error hover:bg-mobius-elevated"
        >
          <LogOut size={18} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
