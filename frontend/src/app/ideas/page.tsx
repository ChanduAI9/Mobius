"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api, Idea } from "@/lib/api";

export default function IdeasPage() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [newIdea, setNewIdea] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [capturing, setCapturing] = useState(false);

  const load = () => {
    api.listIdeas().then((res) => setIdeas(res.items)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCapture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIdea.trim()) return;
    setCapturing(true);
    try {
      await api.captureIdea(newIdea.trim());
      setNewIdea("");
      setShowForm(false);
      load();
    } finally {
      setCapturing(false);
    }
  };

  return (
    <AppShell>
      <div className="p-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Ideas</h1>
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ Capture Idea"}
          </Button>
        </div>

        {showForm && (
          <form onSubmit={handleCapture} className="mb-6 space-y-3">
            <textarea
              value={newIdea}
              onChange={(e) => setNewIdea(e.target.value)}
              placeholder="Describe your idea..."
              rows={4}
              className="w-full rounded-lg border border-mobius-border bg-mobius-surface px-4 py-2.5 text-sm focus:border-mobius-accent focus:outline-none"
            />
            <Button type="submit" size="sm" disabled={capturing}>
              {capturing ? "Analyzing..." : "Capture & Analyze"}
            </Button>
          </form>
        )}

        {loading ? (
          <p className="text-mobius-muted">Loading...</p>
        ) : (
          <div className="space-y-4">
            {ideas.map((idea) => (
              <Card key={idea.id} elevated>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-lg">💡</span>
                  <span className="text-xs text-mobius-muted uppercase">{idea.status}</span>
                </div>
                <h2 className="font-semibold mb-2">{idea.summary || idea.raw_input.slice(0, 100)}</h2>
                <p className="text-sm text-mobius-muted mb-4">{idea.raw_input.slice(0, 200)}</p>

                <div className="grid grid-cols-3 gap-3 mb-4 text-xs">
                  <div>
                    <span className="text-mobius-muted block">Business Value</span>
                    <span>{idea.business_value?.slice(0, 50) || "—"}</span>
                  </div>
                  <div>
                    <span className="text-mobius-muted block">Effort</span>
                    <span>{idea.implementation_effort || "—"}</span>
                  </div>
                  <div>
                    <span className="text-mobius-muted block">Feasibility</span>
                    <span>
                      {idea.analysis?.feasibility
                        ? `${Math.round(Number(idea.analysis.feasibility) * 100)}%`
                        : "—"}
                    </span>
                  </div>
                </div>

                {idea.weaknesses && (
                  <p className="text-sm text-mobius-muted mb-2">
                    <strong>Weaknesses:</strong> {idea.weaknesses.slice(0, 150)}
                  </p>
                )}

                {idea.tasks && idea.tasks.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-mobius-border">
                    <span className="text-xs text-mobius-muted uppercase">Suggested Tasks</span>
                    <ul className="mt-1 space-y-1">
                      {idea.tasks.map((t) => (
                        <li key={t.id} className="text-sm">
                          • {t.title}{" "}
                          <span className="text-xs text-mobius-accent">({t.priority})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            ))}
            {!ideas.length && (
              <p className="text-mobius-muted text-center py-12">
                No ideas captured yet. Say &quot;I have an idea&quot; in chat or capture one above.
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
