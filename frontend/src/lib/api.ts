const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mobius_access_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && token) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers.Authorization = `Bearer ${getToken()}`;
      const retry = await fetch(`${API_URL}${path}`, { ...options, headers });
      if (!retry.ok) throw new Error(await retry.text());
      return retry.json();
    }
    localStorage.removeItem("mobius_access_token");
    localStorage.removeItem("mobius_refresh_token");
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  if (response.status === 204) return {} as T;
  return response.json();
}

async function refreshToken(): Promise<boolean> {
  const refresh = localStorage.getItem("mobius_refresh_token");
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("mobius_access_token", data.access_token);
    localStorage.setItem("mobius_refresh_token", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export const api = {
  register: (email: string, password: string, display_name: string) =>
    request<AuthTokens & { id: string; email: string; display_name: string }>(
      "/api/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, display_name }) }
    ),

  login: (email: string, password: string) =>
    request<AuthTokens & { id: string; email: string; display_name: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    ),

  me: () => request<{ id: string; email: string; display_name: string }>("/api/v1/auth/me"),

  getDashboard: () => request<DashboardData>("/api/v1/dashboard"),

  listConversations: () =>
    request<{ items: Conversation[]; total: number }>("/api/v1/conversations"),

  createConversation: (title?: string) =>
    request<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ title: title || "New conversation" }),
    }),

  getConversation: (id: string) =>
    request<Conversation & { messages: Message[] }>(`/api/v1/conversations/${id}`),

  sendMessage: (conversationId: string, content: string) =>
    request<{ user_message: Message; assistant_message: Message }>(
      `/api/v1/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) }
    ),

  listMemories: () =>
    request<{ items: Memory[]; total: number }>("/api/v1/memories"),

  createMemory: (content: string, category?: string) =>
    request<Memory>("/api/v1/memories", {
      method: "POST",
      body: JSON.stringify({ content, category: category || "general" }),
    }),

  listIdeas: () => request<{ items: Idea[]; total: number }>("/api/v1/ideas"),

  captureIdea: (content: string) =>
    request<Idea>("/api/v1/ideas/capture", {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  search: (q: string) =>
    request<{ results: SearchResult[] }>(`/api/v1/search?q=${encodeURIComponent(q)}`),

  // Knowledge Base
  listKnowledgeSpaces: () =>
    request<{ items: KnowledgeSpace[] }>("/api/v1/knowledge/spaces"),

  createKnowledgeSpace: (name: string, description?: string) =>
    request<KnowledgeSpace>("/api/v1/knowledge/spaces", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),

  getKnowledgeSpace: (id: string) =>
    request<KnowledgeSpaceDetail>(`/api/v1/knowledge/spaces/${id}`),

  addLocalSource: (spaceId: string, name: string, path: string) =>
    request<KnowledgeSource>(`/api/v1/knowledge/spaces/${spaceId}/sources/local`, {
      method: "POST",
      body: JSON.stringify({ name, path }),
    }),

  addGitHubSource: (spaceId: string, name: string, repo: string, branch?: string) =>
    request<KnowledgeSource>(`/api/v1/knowledge/spaces/${spaceId}/sources/github`, {
      method: "POST",
      body: JSON.stringify({ name, repo, branch: branch || "main" }),
    }),

  ingestSource: (sourceId: string) =>
    request<{ job_id: string; files_processed: number; chunks_created: number }>(
      `/api/v1/knowledge/sources/${sourceId}/ingest`,
      { method: "POST" }
    ),

  getIngestionJob: (jobId: string) =>
    request<IngestionJob>(`/api/v1/knowledge/ingestion/${jobId}`),

  listDocuments: (spaceId: string) =>
    request<{ items: KnowledgeDocument[] }>(`/api/v1/knowledge/spaces/${spaceId}/documents`),

  searchKnowledge: (query: string, spaceId?: string) =>
    request<{ results: KnowledgeSearchResult[] }>("/api/v1/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, space_id: spaceId }),
    }),

  uploadDocument: async (spaceId: string, file: File) => {
    const token = getToken();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/api/v1/knowledge/spaces/${spaceId}/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
    return res.json();
  },

  // Agents
  classifyIntent: (message: string) =>
    request<{ agent: string }>("/api/v1/agents/classify", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  runAgent: (message: string, agent?: string, spaceIds?: string[]) =>
    request<{ content: string; agent: string; context_used: boolean }>("/api/v1/agents/run", {
      method: "POST",
      body: JSON.stringify({ message, agent, space_ids: spaceIds || [] }),
    }),

  addNotionSource: (spaceId: string, name: string, databaseId?: string, token?: string) =>
    request<KnowledgeSource>(`/api/v1/knowledge/spaces/${spaceId}/sources/notion`, {
      method: "POST",
      body: JSON.stringify({ name, database_id: databaseId, token }),
    }),

  addGDriveSource: (spaceId: string, name: string, folderId?: string, accessToken?: string) =>
    request<KnowledgeSource>(`/api/v1/knowledge/spaces/${spaceId}/sources/gdrive`, {
      method: "POST",
      body: JSON.stringify({ name, folder_id: folderId || "root", access_token: accessToken }),
    }),

  // Research
  research: (query: string, mode?: string, spaceIds?: string[]) =>
    request<ResearchFinding>("/api/v1/research", {
      method: "POST",
      body: JSON.stringify({ query, mode: mode || "general", space_ids: spaceIds || [] }),
    }),

  compareTechnologies: (technologies: string[]) =>
    request<ResearchFinding>("/api/v1/research/compare", {
      method: "POST",
      body: JSON.stringify({ technologies }),
    }),

  orchestrate: (query: string, spaceIds?: string[], projectId?: string) =>
    request<{ plan: Array<{ step: number; tool: string; query: string }>; response: string }>(
      "/api/v1/research/orchestrate",
      { method: "POST", body: JSON.stringify({ query, space_ids: spaceIds || [], project_id: projectId }) }
    ),

  // Projects
  listProjects: () => request<{ items: Project[]; total: number }>("/api/v1/projects"),

  createProject: (name: string, description?: string) =>
    request<Project>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),

  getProject: (id: string) => request<ProjectDetail>(`/api/v1/projects/${id}`),

  getKanban: (projectId: string) => request<KanbanBoard>(`/api/v1/projects/${projectId}/kanban`),

  createTask: (projectId: string, title: string, kanbanColumn?: string) =>
    request<Task>(`/api/v1/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ title, kanban_column: kanbanColumn || "backlog" }),
    }),

  moveTask: (taskId: string, kanbanColumn: string) =>
    request<Task>(`/api/v1/projects/tasks/${taskId}/move`, {
      method: "POST",
      body: JSON.stringify({ kanban_column: kanbanColumn }),
    }),

  getProjectAnalytics: (projectId: string) =>
    request<ProjectAnalytics>(`/api/v1/projects/${projectId}/analytics`),

  getProjectRecommendations: () =>
    request<{ recommendations: Array<{ type: string; message: string; action_url: string }> }>(
      "/api/v1/projects/recommendations"
    ),

  createSprint: (projectId: string, name: string, goal?: string) =>
    request<Sprint>(`/api/v1/projects/${projectId}/sprints`, {
      method: "POST",
      body: JSON.stringify({ name, goal }),
    }),

  createMilestone: (projectId: string, title: string, description?: string) =>
    request<Milestone>(`/api/v1/projects/${projectId}/milestones`, {
      method: "POST",
      body: JSON.stringify({ title, description }),
    }),
};

export interface DashboardData {
  focus: { title: string; reason: string; action_url: string };
  recent_memories: Array<{ id: string; content: string; category: string; importance: number }>;
  recent_ideas: Array<{ id: string; summary: string; status: string }>;
  upcoming_tasks: Array<{ id: string; title: string; priority: string }>;
  recommendations: Array<{ type: string; message: string; action_url: string }>;
  stats: { conversations_today: number; memories_total: number; ideas_total: number };
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  message_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface Memory {
  id: string;
  content: string;
  category: string;
  tier: string;
  importance: number;
  tags: string[];
  created_at: string;
}

export interface Idea {
  id: string;
  raw_input: string;
  summary: string | null;
  business_value: string | null;
  implementation_effort: string | null;
  weaknesses: string | null;
  improvements: string | null;
  analysis: Record<string, unknown>;
  status: string;
  tasks?: Array<{ id: string; title: string; priority: string }>;
}

export interface SearchResult {
  type: string;
  id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface KnowledgeSpace {
  id: string;
  name: string;
  description: string | null;
  document_count?: number;
  chunk_count?: number;
  status: string;
  created_at: string;
}

export interface KnowledgeSpaceDetail extends KnowledgeSpace {
  sources: KnowledgeSource[];
}

export interface KnowledgeSource {
  id: string;
  space_id: string;
  source_type: string;
  name: string;
  config: Record<string, string>;
  status: string;
  watch_enabled: boolean;
  last_synced_at: string | null;
}

export interface KnowledgeDocument {
  id: string;
  filename: string;
  file_path: string;
  mime_type: string;
  chunk_count: number;
  file_size: number;
  updated_at: string;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  filename: string;
  file_path: string;
  content: string;
  score: number;
}

export interface IngestionJob {
  id: string;
  status: string;
  progress: number;
  files_processed: number;
  chunks_created: number;
  error: string | null;
}

export interface ResearchFinding {
  title: string;
  summary: string;
  content: string;
  citations: Array<{ index: number; title: string; url: string; snippet: string }>;
  category: string;
  tags: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  tasks_total?: number;
  completion_rate?: number;
  tasks_by_column?: Record<string, number>;
}

export interface ProjectDetail extends Project {
  sprints: Sprint[];
  milestones: Milestone[];
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  kanban_column: string;
  priority: string;
  status: string;
}

export interface KanbanBoard {
  columns: string[];
  board: Record<string, Task[]>;
}

export interface Sprint {
  id: string;
  name: string;
  goal: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
}

export interface Milestone {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_date: string | null;
}

export interface ProjectAnalytics {
  tasks_total: number;
  tasks_by_column: Record<string, number>;
  completion_rate: number;
  recommendations: string[];
}

export function saveTokens(tokens: AuthTokens) {
  localStorage.setItem("mobius_access_token", tokens.access_token);
  localStorage.setItem("mobius_refresh_token", tokens.refresh_token);
}

export function clearTokens() {
  localStorage.removeItem("mobius_access_token");
  localStorage.removeItem("mobius_refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function getWebSocketUrl(conversationId: string): string {
  const token = getToken();
  const wsBase = API_URL.replace("http", "ws");
  return `${wsBase}/ws/conversations/${conversationId}?token=${token}`;
}
