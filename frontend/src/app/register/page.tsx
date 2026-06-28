"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, saveTokens } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function RegisterPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.register(email, password, displayName);
      saveTokens(data);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-mobius-bg px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-5xl text-mobius-accent">◈</span>
          <h1 className="text-2xl font-bold mt-4">Create your MOBIUS</h1>
          <p className="text-mobius-muted mt-2">Set up your personal AI operating system</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 bg-mobius-surface border border-mobius-border rounded-xl p-6">
          <Input
            id="displayName"
            label="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            placeholder="Saichandu"
          />
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
            minLength={8}
            placeholder="Minimum 8 characters"
          />
          {error && <p className="text-sm text-mobius-error">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </Button>
        </form>

        <p className="text-center text-sm text-mobius-muted mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-mobius-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
