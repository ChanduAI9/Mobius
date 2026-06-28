"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isAuthenticated } from "@/lib/api";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center bg-mobius-bg">
        <div className="flex items-center gap-3">
          <span className="text-3xl text-mobius-accent animate-pulse-accent">◈</span>
          <span className="text-mobius-muted">Loading MOBIUS...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-mobius-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
