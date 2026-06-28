"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, SearchResult } from "@/lib/api";
import { Search as SearchIcon } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.search(query.trim());
      setResults(res.results);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  };

  const typeColors: Record<string, string> = {
    memory: "text-mobius-accent",
    idea: "text-mobius-warning",
    conversation: "text-mobius-success",
  };

  return (
    <AppShell>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Search</h1>

        <form onSubmit={handleSearch} className="relative mb-8">
          <SearchIcon size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-mobius-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memories, ideas, conversations..."
            className="w-full rounded-xl border border-mobius-border bg-mobius-surface pl-11 pr-4 py-3 text-sm focus:border-mobius-accent focus:outline-none focus:ring-1 focus:ring-mobius-accent"
          />
        </form>

        {loading && <p className="text-mobius-muted">Searching...</p>}

        {searched && !loading && (
          <div className="space-y-3">
            {results.map((r) => (
              <Card key={`${r.type}-${r.id}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-semibold uppercase ${typeColors[r.type] || "text-mobius-muted"}`}>
                    {r.type}
                  </span>
                  <span className="text-xs text-mobius-muted">{Math.round(r.score * 100)}% match</span>
                </div>
                <h3 className="font-medium text-sm mb-1">{r.title}</h3>
                <p className="text-sm text-mobius-muted">{r.snippet}</p>
              </Card>
            ))}
            {!results.length && (
              <p className="text-mobius-muted text-center py-8">No results found for &quot;{query}&quot;</p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
