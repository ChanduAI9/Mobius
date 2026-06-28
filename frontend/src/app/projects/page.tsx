"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api, Project, ProjectDetail, KanbanBoard, Task, ProjectAnalytics } from "@/lib/api";
import { FolderKanban, Plus, BarChart3, Target, Zap } from "lucide-react";
import clsx from "clsx";

const COLUMN_LABELS: Record<string, string> = {
  backlog: "Backlog",
  todo: "To Do",
  in_progress: "In Progress",
  review: "Review",
  done: "Done",
};

const COLUMN_COLORS: Record<string, string> = {
  backlog: "border-mobius-muted",
  todo: "border-blue-500",
  in_progress: "border-mobius-warning",
  review: "border-purple-500",
  done: "border-mobius-success",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<ProjectDetail | null>(null);
  const [kanban, setKanban] = useState<KanbanBoard | null>(null);
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<Array<{ message: string; action_url: string }>>([]);
  const [newProjectName, setNewProjectName] = useState("");
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newSprintName, setNewSprintName] = useState("");
  const [newSprintGoal, setNewSprintGoal] = useState("");
  const [newMilestoneTitle, setNewMilestoneTitle] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<"kanban" | "roadmap" | "analytics">("kanban");

  const loadProjects = () => {
    api.listProjects().then((r) => setProjects(r.items));
    api.getProjectRecommendations().then((r) => setRecommendations(r.recommendations));
  };

  useEffect(loadProjects, []);

  const selectProject = async (id: string) => {
    const [project, board, stats] = await Promise.all([
      api.getProject(id),
      api.getKanban(id),
      api.getProjectAnalytics(id),
    ]);
    setSelected(project);
    setKanban(board);
    setAnalytics(stats);
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    await api.createProject(newProjectName.trim());
    setNewProjectName("");
    setShowCreate(false);
    loadProjects();
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !newTaskTitle.trim()) return;
    await api.createTask(selected.id, newTaskTitle.trim());
    setNewTaskTitle("");
    await selectProject(selected.id);
  };

  const handleMoveTask = async (taskId: string, column: string) => {
    await api.moveTask(taskId, column);
    if (selected) await selectProject(selected.id);
  };

  const handleCreateSprint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !newSprintName.trim()) return;
    await api.createSprint(selected.id, newSprintName.trim(), newSprintGoal.trim() || undefined);
    setNewSprintName("");
    setNewSprintGoal("");
    await selectProject(selected.id);
  };

  const handleCreateMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !newMilestoneTitle.trim()) return;
    await api.createMilestone(selected.id, newMilestoneTitle.trim());
    setNewMilestoneTitle("");
    await selectProject(selected.id);
  };

  return (
    <AppShell>
      <div className="flex h-screen">
        <div className="w-64 border-r border-mobius-border bg-mobius-surface p-4 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold flex items-center gap-2">
              <FolderKanban size={18} className="text-mobius-accent" /> Projects
            </h2>
            <Button size="sm" onClick={() => setShowCreate(!showCreate)}>+</Button>
          </div>
          {showCreate && (
            <form onSubmit={handleCreateProject} className="mb-4 space-y-2">
              <Input value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)} placeholder="Project name" />
              <Button type="submit" size="sm" className="w-full">Create</Button>
            </form>
          )}
          <div className="flex-1 overflow-y-auto space-y-1">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => selectProject(p.id)}
                className={clsx(
                  "w-full text-left rounded-lg px-3 py-2 text-sm transition-colors",
                  selected?.id === p.id ? "bg-mobius-elevated text-mobius-accent" : "text-mobius-muted hover:bg-mobius-elevated"
                )}
              >
                <div className="font-medium">{p.name}</div>
                <div className="text-xs">{p.tasks_total ?? 0} tasks · {Math.round((p.completion_rate ?? 0) * 100)}%</div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <FolderKanban size={48} className="text-mobius-accent mb-4" />
              <h2 className="text-xl font-semibold mb-2">Project Management</h2>
              <p className="text-mobius-muted max-w-md">Kanban boards, sprints, milestones, and AI-powered recommendations.</p>
              {recommendations.length > 0 && (
                <div className="mt-6 space-y-2 max-w-md w-full">
                  {recommendations.map((r, i) => (
                    <div key={i} className="p-3 rounded-lg bg-mobius-surface border border-mobius-border text-sm flex items-start gap-2">
                      <Zap size={14} className="text-mobius-accent mt-0.5" />
                      {r.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="max-w-6xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold">{selected.name}</h1>
                  <p className="text-mobius-muted text-sm">{selected.description}</p>
                </div>
                <div className="flex gap-2">
                  {(["kanban", "roadmap", "analytics"] as const).map((t) => (
                    <Button key={t} size="sm" variant={tab === t ? "primary" : "secondary"} onClick={() => setTab(t)}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>

              {tab === "kanban" && kanban && (
                <>
                  <form onSubmit={handleCreateTask} className="flex gap-2">
                    <Input value={newTaskTitle} onChange={(e) => setNewTaskTitle(e.target.value)} placeholder="New task..." />
                    <Button type="submit" size="sm">Add</Button>
                  </form>
                  <div className="grid grid-cols-5 gap-3 min-h-[400px]">
                    {kanban.columns.map((col) => (
                      <div key={col} className={clsx("rounded-xl border-t-2 bg-mobius-surface p-3", COLUMN_COLORS[col])}>
                        <h3 className="text-xs font-semibold uppercase text-mobius-muted mb-3">
                          {COLUMN_LABELS[col]} ({kanban.board[col]?.length ?? 0})
                        </h3>
                        <div className="space-y-2">
                          {(kanban.board[col] || []).map((task: Task) => (
                            <div key={task.id} className="p-2.5 rounded-lg bg-mobius-bg text-sm border border-mobius-border">
                              <p className="font-medium mb-2">{task.title}</p>
                              <div className="flex gap-1 flex-wrap">
                                {kanban.columns.filter((c) => c !== col).slice(0, 3).map((c) => (
                                  <button
                                    key={c}
                                    onClick={() => handleMoveTask(task.id, c)}
                                    className="text-xs px-1.5 py-0.5 rounded bg-mobius-elevated text-mobius-muted hover:text-mobius-accent"
                                  >
                                    → {COLUMN_LABELS[c]}
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {tab === "roadmap" && (
                <div className="grid grid-cols-2 gap-6">
                  <Card>
                    <CardTitle className="flex items-center gap-2"><Target size={14} /> Milestones</CardTitle>
                    <form onSubmit={handleCreateMilestone} className="flex gap-2 mb-4">
                      <Input value={newMilestoneTitle} onChange={(e) => setNewMilestoneTitle(e.target.value)} placeholder="New milestone..." />
                      <Button type="submit" size="sm">Add</Button>
                    </form>
                    {selected.milestones?.length ? selected.milestones.map((m) => (
                      <div key={m.id} className="py-2 border-b border-mobius-border last:border-0 text-sm">
                        <span className="font-medium">{m.title}</span>
                        <span className="text-mobius-muted ml-2 text-xs uppercase">{m.status}</span>
                      </div>
                    )) : <p className="text-sm text-mobius-muted">No milestones yet.</p>}
                  </Card>
                  <Card>
                    <CardTitle>Sprints</CardTitle>
                    <form onSubmit={handleCreateSprint} className="space-y-2 mb-4">
                      <div className="flex gap-2">
                        <Input value={newSprintName} onChange={(e) => setNewSprintName(e.target.value)} placeholder="Sprint name..." />
                        <Button type="submit" size="sm">Add</Button>
                      </div>
                      <Input value={newSprintGoal} onChange={(e) => setNewSprintGoal(e.target.value)} placeholder="Sprint goal (optional)" />
                    </form>
                    {selected.sprints?.length ? selected.sprints.map((s) => (
                      <div key={s.id} className="py-2 border-b border-mobius-border last:border-0 text-sm">
                        <span className="font-medium">{s.name}</span>
                        {s.goal && <p className="text-mobius-muted text-xs mt-1">{s.goal}</p>}
                      </div>
                    )) : <p className="text-sm text-mobius-muted">No sprints planned.</p>}
                  </Card>
                </div>
              )}

              {tab === "analytics" && analytics && (
                <div className="grid grid-cols-3 gap-4">
                  <Card elevated>
                    <CardTitle className="flex items-center gap-2"><BarChart3 size={14} /> Completion</CardTitle>
                    <p className="text-3xl font-bold text-mobius-accent">{Math.round(analytics.completion_rate * 100)}%</p>
                    <p className="text-sm text-mobius-muted">{analytics.tasks_total} total tasks</p>
                  </Card>
                  {Object.entries(analytics.tasks_by_column || {}).map(([col, count]) => (
                    <Card key={col}>
                      <CardTitle>{COLUMN_LABELS[col] || col}</CardTitle>
                      <p className="text-2xl font-bold">{count}</p>
                    </Card>
                  ))}
                  {analytics.recommendations?.length > 0 && (
                    <Card className="col-span-3">
                      <CardTitle>AI Recommendations</CardTitle>
                      <ul className="space-y-1 text-sm">
                        {analytics.recommendations.map((r, i) => (
                          <li key={i} className="text-mobius-muted">• {r}</li>
                        ))}
                      </ul>
                    </Card>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
