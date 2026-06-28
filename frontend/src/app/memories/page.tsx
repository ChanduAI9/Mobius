"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api, Memory } from "@/lib/api";

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [newContent, setNewContent] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.listMemories().then((res) => setMemories(res.items)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    await api.createMemory(newContent.trim());
    setNewContent("");
    setShowForm(false);
    load();
  };

  return (
    <AppShell>
      <div className="p-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Memories</h1>
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ Add Memory"}
          </Button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="mb-6">
            <Input
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="What should MOBIUS remember?"
            />
            <Button type="submit" size="sm" className="mt-3">
              Save Memory
            </Button>
          </form>
        )}

        {loading ? (
          <p className="text-mobius-muted">Loading...</p>
        ) : (
          <div className="space-y-3">
            {memories.map((m) => (
              <Card key={m.id}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-mobius-accent">
                    ⭐ {m.importance.toFixed(1)}
                  </span>
                  <span className="text-xs text-mobius-muted uppercase">
                    {m.tier} · {m.category}
                  </span>
                </div>
                <p className="text-sm">{m.content}</p>
                {m.tags.length > 0 && (
                  <div className="flex gap-2 mt-2">
                    {m.tags.map((tag) => (
                      <span key={tag} className="text-xs text-mobius-muted">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </Card>
            ))}
            {!memories.length && (
              <p className="text-mobius-muted text-center py-12">
                No memories yet. MOBIUS learns from your conversations automatically.
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
