"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api, DashboardData } from "@/lib/api";
import { MessageSquare, Lightbulb, Brain, Mic, Zap } from "lucide-react";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [userName, setUserName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getDashboard(), api.me()])
      .then(([dashboard, user]) => {
        setData(dashboard);
        setUserName(user.display_name);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <span className="text-mobius-muted">Loading dashboard...</span>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-8 max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold">
            {greeting()}, {userName}
          </h1>
          <p className="text-mobius-muted mt-1">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
            {data && ` · ${data.stats.conversations_today} conversations today`}
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card elevated>
            <CardTitle>Today&apos;s Focus</CardTitle>
            {data?.focus && (
              <>
                <h2 className="text-xl font-semibold mb-2">{data.focus.title}</h2>
                <p className="text-mobius-muted text-sm mb-4">{data.focus.reason}</p>
                <Link href={data.focus.action_url}>
                  <Button size="sm">Continue</Button>
                </Link>
              </>
            )}
          </Card>

          <Card elevated>
            <CardTitle>AI Recommendations</CardTitle>
            <div className="space-y-3">
              {data?.recommendations.length ? (
                data.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-mobius-bg">
                    <Zap size={16} className="text-mobius-accent mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm">{rec.message}</p>
                      <Link href={rec.action_url} className="text-xs text-mobius-accent hover:underline">
                        View →
                      </Link>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-mobius-muted text-sm">All caught up. Great work!</p>
              )}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardTitle>Recent Memories</CardTitle>
            <ul className="space-y-2">
              {data?.recent_memories.map((m) => (
                <li key={m.id} className="text-sm flex items-start gap-2">
                  <Brain size={14} className="text-mobius-accent mt-0.5 shrink-0" />
                  <span className="text-mobius-muted">{m.content}</span>
                </li>
              ))}
              {!data?.recent_memories.length && (
                <li className="text-mobius-muted text-sm">No memories yet. Start a conversation!</li>
              )}
            </ul>
          </Card>

          <Card>
            <CardTitle>Recent Ideas</CardTitle>
            <ul className="space-y-2">
              {data?.recent_ideas.map((idea) => (
                <li key={idea.id} className="text-sm flex items-start gap-2">
                  <Lightbulb size={14} className="text-mobius-warning mt-0.5 shrink-0" />
                  <span>{idea.summary}</span>
                </li>
              ))}
              {!data?.recent_ideas.length && (
                <li className="text-mobius-muted text-sm">
                  Say &quot;I have an idea&quot; in chat to capture one.
                </li>
              )}
            </ul>
          </Card>
        </div>

        <Card>
          <CardTitle>Quick Actions</CardTitle>
          <div className="flex flex-wrap gap-3">
            <Link href="/chat">
              <Button variant="secondary" size="sm">
                <MessageSquare size={16} className="mr-2" /> New Chat
              </Button>
            </Link>
            <Link href="/ideas">
              <Button variant="secondary" size="sm">
                <Lightbulb size={16} className="mr-2" /> Capture Idea
              </Button>
            </Link>
            <Link href="/chat">
              <Button variant="secondary" size="sm">
                <Mic size={16} className="mr-2" /> Voice
              </Button>
            </Link>
            <Link href="/memories">
              <Button variant="secondary" size="sm">
                <Brain size={16} className="mr-2" /> Add Memory
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
