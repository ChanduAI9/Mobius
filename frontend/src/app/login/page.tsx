"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, saveTokens } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.login(email, password);
      saveTokens(data);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-mobius-bg px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-5xl text-mobius-accent">◈</span>
          <h1 className="text-2xl font-bold mt-4">Welcome to MOBIUS</h1>
          <p className="text-mobius-muted mt-2">Your personal AI operating system</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 bg-mobius-surface border border-mobius-border rounded-xl p-6">
          <Input
            id="email"
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
          />
          {error && <p className="text-sm text-mobius-error">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <p className="text-center text-sm text-mobius-muted mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-mobius-accent hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
