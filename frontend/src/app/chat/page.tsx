"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { api, Conversation, Message, getWebSocketUrl } from "@/lib/api";
import { Mic, Plus, Send } from "lucide-react";
import clsx from "clsx";

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [activeAgent, setActiveAgent] = useState<string>("auto");
  const [currentAgentLabel, setCurrentAgentLabel] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef("");

  useEffect(() => {
    api.listConversations().then((res) => {
      setConversations(res.items);
      if (res.items.length > 0) {
        selectConversation(res.items[0].id);
      }
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  const selectConversation = async (id: string) => {
    setActiveId(id);
    const conv = await api.getConversation(id);
    setMessages(conv.messages);
  };

  const createConversation = async () => {
    const conv = await api.createConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    setMessages([]);
  };

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;

    let convId = activeId;
    if (!convId) {
      const conv = await api.createConversation();
      convId = conv.id;
      setActiveId(convId);
      setConversations((prev) => [conv, ...prev]);
    }

    const userContent = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: userContent,
        created_at: new Date().toISOString(),
      },
    ]);

    setStreaming(true);
    setStreamContent("");
    streamBufferRef.current = "";

    const ws = new WebSocket(getWebSocketUrl(convId));
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: "message",
        content: userContent,
        agent: activeAgent === "auto" ? null : activeAgent,
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "agent") {
        setCurrentAgentLabel(data.agent);
      } else if (data.type === "token") {
        streamBufferRef.current += data.content;
        setStreamContent(streamBufferRef.current);
      } else if (data.type === "done") {
        const finalContent = streamBufferRef.current;
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: finalContent,
            created_at: new Date().toISOString(),
          },
        ]);
        setStreamContent("");
        streamBufferRef.current = "";
        setStreaming(false);
        setCurrentAgentLabel(null);
        ws.close();
        api.listConversations().then((res) => setConversations(res.items));
      } else if (data.type === "error") {
        setStreaming(false);
        setStreamContent("");
        ws.close();
      }
    };

    ws.onerror = async () => {
      try {
        const result = await api.sendMessage(convId!, userContent);
        setMessages((prev) => [...prev, result.assistant_message]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Connection error. Please check your API configuration.",
            created_at: new Date().toISOString(),
          },
        ]);
      }
      setStreaming(false);
      setStreamContent("");
    };
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <AppShell>
      <div className="flex h-screen">
        <div className="w-64 border-r border-mobius-border bg-mobius-surface flex flex-col">
          <div className="p-4 border-b border-mobius-border">
            <Button onClick={createConversation} size="sm" className="w-full">
              <Plus size={16} className="mr-2" /> New Chat
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={clsx(
                  "w-full text-left rounded-lg px-3 py-2 text-sm truncate transition-colors",
                  activeId === conv.id
                    ? "bg-mobius-elevated text-mobius-accent"
                    : "text-mobius-muted hover:bg-mobius-elevated hover:text-mobius-text"
                )}
              >
                {conv.title}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && !streaming && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <span className="text-4xl text-mobius-accent mb-4">◈</span>
                <h2 className="text-xl font-semibold mb-2">MOBIUS is ready</h2>
                <p className="text-mobius-muted max-w-md">
                  Ask about architecture, startups, code, or say &quot;I have an idea&quot; to capture one.
                </p>
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}
              >
                <div
                  className={clsx(
                    "max-w-[75%] rounded-xl px-4 py-3 text-sm",
                    msg.role === "user"
                      ? "bg-mobius-accent text-mobius-bg"
                      : "bg-mobius-elevated border border-mobius-border"
                  )}
                >
                  {msg.role === "assistant" && (
                    <span className="text-xs text-mobius-accent font-semibold block mb-1">MOBIUS</span>
                  )}
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
            {streaming && streamContent && (
              <div className="flex justify-start">
                <div className="max-w-[75%] rounded-xl px-4 py-3 text-sm bg-mobius-elevated border border-mobius-border">
                  <span className="text-xs text-mobius-accent font-semibold block mb-1">
                    MOBIUS <span className="inline-block w-2 h-2 rounded-full bg-mobius-accent animate-pulse-accent ml-1" />
                  </span>
                  <div className="whitespace-pre-wrap">{streamContent}</div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-mobius-border p-4">
            <div className="flex items-center gap-2 max-w-4xl mx-auto mb-2">
              <span className="text-xs text-mobius-muted">Agent:</span>
              {["auto", "conversation", "coding", "architecture", "research"].map((a) => (
                <button
                  key={a}
                  onClick={() => setActiveAgent(a)}
                  className={clsx(
                    "text-xs px-2 py-1 rounded-md capitalize transition-colors",
                    activeAgent === a
                      ? "bg-mobius-accent text-mobius-bg"
                      : "text-mobius-muted hover:bg-mobius-elevated"
                  )}
                >
                  {a}
                </button>
              ))}
              {currentAgentLabel && (
                <span className="text-xs text-mobius-accent ml-auto">
                  ◈ {currentAgentLabel} agent active
                </span>
              )}
            </div>
            <div className="flex items-end gap-2 max-w-4xl mx-auto">
              <button className="p-2.5 rounded-lg text-mobius-muted hover:text-mobius-accent hover:bg-mobius-elevated">
                <Mic size={20} />
              </button>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask MOBIUS anything..."
                rows={1}
                className="flex-1 resize-none rounded-lg border border-mobius-border bg-mobius-surface px-4 py-2.5 text-sm focus:border-mobius-accent focus:outline-none focus:ring-1 focus:ring-mobius-accent"
              />
              <Button onClick={sendMessage} disabled={!input.trim() || streaming} size="sm">
                <Send size={16} />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
