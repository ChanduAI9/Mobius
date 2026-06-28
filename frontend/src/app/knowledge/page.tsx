"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  api,
  KnowledgeSpace,
  KnowledgeSpaceDetail,
  KnowledgeDocument,
  IngestionJob,
} from "@/lib/api";
import { BookOpen, FolderOpen, Github, Upload, RefreshCw, Search, FileText, HardDrive } from "lucide-react";

export default function KnowledgePage() {
  const [spaces, setSpaces] = useState<KnowledgeSpace[]>([]);
  const [selectedSpace, setSelectedSpace] = useState<KnowledgeSpaceDetail | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState("");
  const [showAddSource, setShowAddSource] = useState(false);
  const [sourceType, setSourceType] = useState<"local" | "github" | "notion" | "gdrive">("local");
  const [sourceName, setSourceName] = useState("");
  const [sourcePath, setSourcePath] = useState("");
  const [sourceRepo, setSourceRepo] = useState("");
  const [sourceNotionDb, setSourceNotionDb] = useState("");
  const [sourceNotionToken, setSourceNotionToken] = useState("");
  const [sourceGDriveFolder, setSourceGDriveFolder] = useState("");
  const [sourceGDriveToken, setSourceGDriveToken] = useState("");
  const [ingesting, setIngesting] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ filename: string; content: string; score: number }>>([]);

  const loadSpaces = () => {
    api.listKnowledgeSpaces().then((res) => setSpaces(res.items)).finally(() => setLoading(false));
  };

  useEffect(loadSpaces, []);

  const selectSpace = async (id: string) => {
    const space = await api.getKnowledgeSpace(id);
    setSelectedSpace(space);
    const docs = await api.listDocuments(id);
    setDocuments(docs.items);
  };

  const handleCreateSpace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSpaceName.trim()) return;
    await api.createKnowledgeSpace(newSpaceName.trim());
    setNewSpaceName("");
    setShowCreate(false);
    loadSpaces();
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSpace || !sourceName.trim()) return;
    if (sourceType === "local" && sourcePath.trim()) {
      await api.addLocalSource(selectedSpace.id, sourceName.trim(), sourcePath.trim());
    } else if (sourceType === "github" && sourceRepo.trim()) {
      await api.addGitHubSource(selectedSpace.id, sourceName.trim(), sourceRepo.trim());
    } else if (sourceType === "notion") {
      await api.addNotionSource(
        selectedSpace.id,
        sourceName.trim(),
        sourceNotionDb.trim() || undefined,
        sourceNotionToken.trim() || undefined
      );
    } else if (sourceType === "gdrive") {
      await api.addGDriveSource(
        selectedSpace.id,
        sourceName.trim(),
        sourceGDriveFolder.trim() || undefined,
        sourceGDriveToken.trim() || undefined
      );
    }
    setShowAddSource(false);
    setSourceName("");
    setSourcePath("");
    setSourceRepo("");
    setSourceNotionDb("");
    setSourceNotionToken("");
    setSourceGDriveFolder("");
    setSourceGDriveToken("");
    await selectSpace(selectedSpace.id);
  };

  const handleIngest = async (sourceId: string) => {
    setIngesting(sourceId);
    try {
      const result = await api.ingestSource(sourceId);
      if (selectedSpace) await selectSpace(selectedSpace.id);
    } finally {
      setIngesting(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedSpace || !e.target.files?.[0]) return;
    await api.uploadDocument(selectedSpace.id, e.target.files[0]);
    await selectSpace(selectedSpace.id);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const res = await api.searchKnowledge(searchQuery.trim(), selectedSpace?.id);
    setSearchResults(res.results);
  };

  return (
    <AppShell>
      <div className="flex h-screen">
        <div className="w-72 border-r border-mobius-border bg-mobius-surface p-4 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold flex items-center gap-2">
              <BookOpen size={18} className="text-mobius-accent" /> Knowledge
            </h2>
            <Button size="sm" onClick={() => setShowCreate(!showCreate)}>+</Button>
          </div>

          {showCreate && (
            <form onSubmit={handleCreateSpace} className="mb-4 space-y-2">
              <Input
                value={newSpaceName}
                onChange={(e) => setNewSpaceName(e.target.value)}
                placeholder="Space name"
              />
              <Button type="submit" size="sm" className="w-full">Create Space</Button>
            </form>
          )}

          <div className="flex-1 overflow-y-auto space-y-1">
            {spaces.map((space) => (
              <button
                key={space.id}
                onClick={() => selectSpace(space.id)}
                className={`w-full text-left rounded-lg px-3 py-2 text-sm transition-colors ${
                  selectedSpace?.id === space.id
                    ? "bg-mobius-elevated text-mobius-accent"
                    : "text-mobius-muted hover:bg-mobius-elevated"
                }`}
              >
                <div className="font-medium">{space.name}</div>
                <div className="text-xs text-mobius-muted">
                  {space.document_count ?? 0} docs · {space.chunk_count ?? 0} chunks
                </div>
              </button>
            ))}
            {!spaces.length && !loading && (
              <p className="text-sm text-mobius-muted text-center py-4">No knowledge spaces yet</p>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!selectedSpace ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <BookOpen size={48} className="text-mobius-accent mb-4" />
              <h2 className="text-xl font-semibold mb-2">Knowledge Base</h2>
              <p className="text-mobius-muted max-w-md">
                Create a knowledge space to index GitHub repos, local folders, PDFs, and documents.
                MOBIUS uses hybrid RAG to answer questions with your data.
              </p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold">{selectedSpace.name}</h1>
                  <p className="text-mobius-muted text-sm">
                    {selectedSpace.document_count} documents · {selectedSpace.chunk_count} chunks
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setShowAddSource(!showAddSource)}>
                    Add Source
                  </Button>
                  <label className="cursor-pointer">
                    <span className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium bg-mobius-elevated text-mobius-text border border-mobius-border hover:bg-mobius-border">
                      <Upload size={14} /> Upload
                    </span>
                    <input type="file" className="hidden" onChange={handleUpload} accept=".pdf,.docx,.md,.txt,.py,.ts,.tsx,.js,.json" />
                  </label>
                </div>
              </div>

              {showAddSource && (
                <Card>
                  <CardTitle>Add Source</CardTitle>
                  <div className="flex gap-2 mb-4 flex-wrap">
                    <Button size="sm" variant={sourceType === "local" ? "primary" : "secondary"} onClick={() => setSourceType("local")}>
                      <FolderOpen size={14} className="mr-1" /> Local Folder
                    </Button>
                    <Button size="sm" variant={sourceType === "github" ? "primary" : "secondary"} onClick={() => setSourceType("github")}>
                      <Github size={14} className="mr-1" /> GitHub
                    </Button>
                    <Button size="sm" variant={sourceType === "notion" ? "primary" : "secondary"} onClick={() => setSourceType("notion")}>
                      <FileText size={14} className="mr-1" /> Notion
                    </Button>
                    <Button size="sm" variant={sourceType === "gdrive" ? "primary" : "secondary"} onClick={() => setSourceType("gdrive")}>
                      <HardDrive size={14} className="mr-1" /> Google Drive
                    </Button>
                  </div>
                  <form onSubmit={handleAddSource} className="space-y-3">
                    <Input value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder="Source name" />
                    {sourceType === "local" && (
                      <Input value={sourcePath} onChange={(e) => setSourcePath(e.target.value)} placeholder="/path/to/folder" />
                    )}
                    {sourceType === "github" && (
                      <Input value={sourceRepo} onChange={(e) => setSourceRepo(e.target.value)} placeholder="owner/repo or GitHub URL" />
                    )}
                    {sourceType === "notion" && (
                      <>
                        <Input value={sourceNotionDb} onChange={(e) => setSourceNotionDb(e.target.value)} placeholder="Notion database ID (optional)" />
                        <Input value={sourceNotionToken} onChange={(e) => setSourceNotionToken(e.target.value)} placeholder="Notion API token (optional if set in env)" type="password" />
                      </>
                    )}
                    {sourceType === "gdrive" && (
                      <>
                        <Input value={sourceGDriveFolder} onChange={(e) => setSourceGDriveFolder(e.target.value)} placeholder="Google Drive folder ID (optional)" />
                        <Input value={sourceGDriveToken} onChange={(e) => setSourceGDriveToken(e.target.value)} placeholder="Access token (optional if set in env)" type="password" />
                      </>
                    )}
                    <Button type="submit" size="sm">Add & Ready to Index</Button>
                  </form>
                </Card>
              )}

              {selectedSpace.sources?.length > 0 && (
                <Card>
                  <CardTitle>Sources</CardTitle>
                  <div className="space-y-2">
                    {selectedSpace.sources.map((source) => (
                      <div key={source.id} className="flex items-center justify-between p-3 rounded-lg bg-mobius-bg">
                        <div>
                          <span className="text-sm font-medium">{source.name}</span>
                          <span className="text-xs text-mobius-muted ml-2 uppercase">{source.source_type}</span>
                          {source.last_synced_at && (
                            <span className="text-xs text-mobius-muted block">
                              Last synced: {new Date(source.last_synced_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={ingesting === source.id}
                          onClick={() => handleIngest(source.id)}
                        >
                          <RefreshCw size={14} className={ingesting === source.id ? "animate-spin mr-1" : "mr-1"} />
                          {ingesting === source.id ? "Indexing..." : "Index"}
                        </Button>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              <Card>
                <CardTitle>Search Knowledge</CardTitle>
                <form onSubmit={handleSearch} className="flex gap-2">
                  <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search indexed content..." />
                  <Button type="submit" size="sm"><Search size={14} /></Button>
                </form>
                {searchResults.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {searchResults.map((r, i) => (
                      <div key={i} className="p-3 rounded-lg bg-mobius-bg text-sm">
                        <div className="flex justify-between mb-1">
                          <span className="text-mobius-accent font-medium">{r.filename}</span>
                          <span className="text-xs text-mobius-muted">{Math.round(r.score * 100)}%</span>
                        </div>
                        <p className="text-mobius-muted">{r.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              <Card>
                <CardTitle>Indexed Documents ({documents.length})</CardTitle>
                {documents.length ? (
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {documents.map((doc) => (
                      <div key={doc.id} className="flex justify-between text-sm py-1.5 border-b border-mobius-border last:border-0">
                        <span>{doc.file_path}</span>
                        <span className="text-mobius-muted">{doc.chunk_count} chunks</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-mobius-muted">No documents indexed yet. Add a source and click Index.</p>
                )}
              </Card>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
