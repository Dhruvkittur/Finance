/**
 * FinPilot AI — Chat Page with AI Agent Streaming
 * ==================================================
 * Real-time SSE streaming chat with:
 * - Agent timeline sidebar
 * - Citations panel
 * - Chart rendering in messages
 * - Document context selector
 * - Markdown rendering with syntax highlighting
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import {
  Send, Bot, User, FileText, Plus, Mic, Paperclip, ChevronRight,
  ChevronDown, Sparkles, Clock, Zap, Check, Copy, ThumbsUp, ThumbsDown,
  BookOpen, BarChart2, AlertTriangle, Loader2, X,
} from "lucide-react";

import { RootState } from "@/app/store";
import {
  addMessage, setCurrentSession, setMessages, setStreaming,
  appendStreamChunk, addAgentStep, clearAgentSteps, updateLastMessage,
  setSessions,
} from "@/app/slices/chatSlice";
import { chatAPI, documentsAPI } from "@/lib/api";

// ── Typing Indicator ──────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 p-4">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-sm flex-shrink-0">
        🤖
      </div>
      <div className="glass rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}

// ── Agent Step Badge ──────────────────────────────────────────────────────────

function AgentTimeline({ steps }: { steps: any[] }) {
  if (!steps.length) return null;

  return (
    <div className="mb-4">
      <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1.5">
        <Sparkles size={11} />
        Agent reasoning chain
      </div>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-start gap-2 text-xs"
          >
            <div className="w-4 h-4 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center mt-0.5 flex-shrink-0">
              <Check size={9} className="text-primary" />
            </div>
            <div className="flex-1">
              <span className="font-medium text-foreground">{step.agent_name}</span>
              <span className="text-muted-foreground ml-1">→ {step.action}</span>
              <span className="text-muted-foreground/60 ml-1">({step.duration_ms?.toFixed(0)}ms)</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ── Chart in Message ──────────────────────────────────────────────────────────

function MessageChart({ chart }: { chart: any }) {
  const COLORS = chart.colors || ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b"];

  return (
    <div className="mt-4 p-4 bg-secondary/50 rounded-xl border border-border">
      <div className="text-xs font-semibold text-foreground mb-3">{chart.title}</div>
      <ResponsiveContainer width="100%" height={200}>
        {chart.chart_type === "pie" ? (
          <PieChart>
            <Pie data={chart.data} cx="50%" cy="50%" outerRadius={80} dataKey={chart.y_keys?.[0] || "value"}>
              {chart.data.map((_: any, i: number) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        ) : chart.chart_type === "bar" ? (
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={chart.x_key} tick={{ fontSize: 10, fill: "#94a3b8" }} />
            <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
            <Tooltip />
            {(chart.y_keys || ["value"]).map((key: string, i: number) => (
              <Bar key={key} dataKey={key} fill={COLORS[i]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        ) : (
          <AreaChart data={chart.data}>
            <defs>
              {(chart.y_keys || ["value"]).map((key: string, i: number) => (
                <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS[i]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS[i]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={chart.x_key} tick={{ fontSize: 10, fill: "#94a3b8" }} />
            <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
            <Tooltip />
            {(chart.y_keys || ["value"]).map((key: string, i: number) => (
              <Area key={key} type="monotone" dataKey={key} stroke={COLORS[i]} fill={`url(#grad-${key})`} />
            ))}
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

// ── Message Bubble ────────────────────────────────────────────────────────────

function MessageBubble({ message, isLast }: { message: any; isLast: boolean }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end px-4 py-2"
      >
        <div className="chat-bubble-user max-w-2xl">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="px-4 py-2 group"
    >
      <div className="flex items-start gap-3 max-w-4xl">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
          🤖
        </div>

        <div className="flex-1 min-w-0">
          {/* Agent Timeline */}
          {message.agent_timeline && message.agent_timeline.length > 0 && (
            <AgentTimeline steps={message.agent_timeline} />
          )}

          {/* Content */}
          <div className="chat-bubble-assistant">
            <div className="prose-finpilot">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>

            {/* Charts */}
            {message.charts?.map((chart: any, i: number) => (
              <MessageChart key={i} chart={chart} />
            ))}

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border/50">
                <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                  <BookOpen size={10} />
                  Sources ({message.citations.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {message.citations.slice(0, 5).map((citation: any, i: number) => (
                    <span key={i} className="agent-badge text-[10px]">
                      {i + 1}. {citation.document_name} ({(citation.similarity_score * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Actions row */}
          <div className="flex items-center gap-3 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {message.confidence_score && (
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <Zap size={9} />
                {(message.confidence_score * 100).toFixed(0)}% confidence
              </span>
            )}
            {message.tokens_used > 0 && (
              <span className="text-[10px] text-muted-foreground">
                {message.tokens_used.toLocaleString()} tokens
              </span>
            )}
            <div className="flex-1" />
            <button onClick={handleCopy} className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors">
              {copied ? <><Check size={10} /> Copied</> : <><Copy size={10} /> Copy</>}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ── Chat Input ────────────────────────────────────────────────────────────────

function ChatInput({
  onSend, isStreaming, sessionId,
}: {
  onSend: (message: string) => void;
  isStreaming: boolean;
  sessionId: string | null;
}) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || isStreaming) return;
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    onSend(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const SUGGESTIONS = [
    "Analyze the revenue trends in the uploaded reports",
    "Detect any fraud signals or anomalies",
    "Check regulatory compliance status",
    "Generate an executive summary",
    "What is the current risk score?",
  ];

  return (
    <div className="border-t border-border p-4 bg-card">
      {/* Suggestions (shown when input is empty) */}
      {!input && !isStreaming && (
        <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-none">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setInput(s)}
              className="flex-shrink-0 text-xs px-3 py-1.5 bg-secondary hover:bg-secondary/80 rounded-full text-muted-foreground hover:text-foreground border border-border transition-all"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-3 glass rounded-xl p-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask FinPilot AI anything about your financial documents..."
          rows={1}
          className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none resize-none max-h-48 py-2 px-2"
          disabled={isStreaming}
        />

        <div className="flex items-center gap-1">
          <button className="w-8 h-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
            <Paperclip size={15} />
          </button>
          <button className="w-8 h-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
            <Mic size={15} />
          </button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-glow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {isStreaming ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
          </motion.button>
        </div>
      </div>

      <p className="text-center text-[10px] text-muted-foreground mt-2">
        FinPilot AI may make mistakes. Verify important financial decisions with a professional.
      </p>
    </div>
  );
}

// ── Chat Page ─────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { id: sessionIdParam } = useParams();

  const { sessions, currentSessionId, messages, isStreaming, agentSteps, activeDocumentIds } =
    useSelector((s: RootState) => s.chat);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load sessions
  const { data: sessionsData } = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: () => chatAPI.listSessions().then((r) => r.data),
  });

  useEffect(() => {
    if (sessionsData?.sessions) {
      dispatch(setSessions(sessionsData.sessions));
    }
  }, [sessionsData, dispatch]);

  // Load session messages when URL changes
  useEffect(() => {
    if (sessionIdParam && sessionIdParam !== currentSessionId) {
      dispatch(setCurrentSession(sessionIdParam));
      chatAPI.getSession(sessionIdParam).then((r) => {
        dispatch(setMessages(r.data.messages));
      });
    }
  }, [sessionIdParam, currentSessionId, dispatch]);

  // Create new session
  const createSession = async () => {
    const res = await chatAPI.createSession({ title: "New Conversation" });
    dispatch(setCurrentSession(res.data.id));
    dispatch(setMessages([]));
    navigate(`/chat/${res.data.id}`);
  };

  // Send message with SSE streaming
  const handleSendMessage = useCallback(async (content: string) => {
    let sessionId = currentSessionId;

    if (!sessionId) {
      const res = await chatAPI.createSession({ title: content.slice(0, 50) });
      sessionId = res.data.id;
      dispatch(setCurrentSession(sessionId));
      navigate(`/chat/${sessionId}`);
    }

    // Add user message optimistically
    dispatch(addMessage({
      id: Date.now().toString(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    }));

    // Add placeholder assistant message
    const assistantMsgId = `streaming-${Date.now()}`;
    dispatch(addMessage({
      id: assistantMsgId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      isStreaming: true,
    }));

    dispatch(setStreaming(true));
    dispatch(clearAgentSteps());

    try {
      const response = await chatAPI.sendMessage(sessionId!, content, activeDocumentIds);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();
          if (data === "[DONE]") continue;

          try {
            const event = JSON.parse(data);

            if (event.type === "content") {
              dispatch(appendStreamChunk(event.chunk));
            } else if (event.type === "agent_step") {
              dispatch(addAgentStep(event.step));
            } else if (event.type === "complete") {
              dispatch(updateLastMessage({
                id: assistantMsgId,
                citations: event.citations,
                charts: event.charts,
                confidence_score: event.confidence_score,
                tokens_used: event.tokens_used,
                agents_used: event.agents_used,
                isStreaming: false,
              }));
            } else if (event.type === "error") {
              dispatch(updateLastMessage({
                content: `Error: ${event.message}`,
                isStreaming: false,
              }));
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (err) {
      console.error("Streaming error:", err);
      dispatch(updateLastMessage({
        content: "Sorry, I encountered an error processing your request. Please try again.",
        isStreaming: false,
      }));
    } finally {
      dispatch(setStreaming(false));
    }
  }, [currentSessionId, activeDocumentIds, dispatch, navigate]);

  return (
    <div className="flex h-full overflow-hidden">
      {/* Session List Sidebar */}
      <div className="w-64 flex-shrink-0 border-r border-border bg-card flex flex-col">
        <div className="p-3 border-b border-border">
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={createSession}
            className="w-full flex items-center gap-2 px-3 py-2 bg-primary rounded-lg text-primary-foreground text-sm font-medium shadow-glow-sm"
          >
            <Plus size={15} />
            New Conversation
          </motion.button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((session) => (
            <motion.button
              key={session.id}
              whileHover={{ x: 2 }}
              onClick={() => {
                dispatch(setCurrentSession(session.id));
                navigate(`/chat/${session.id}`);
              }}
              className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors ${
                currentSessionId === session.id
                  ? "bg-primary/15 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              <div className="font-medium truncate">{session.title}</div>
              <div className="text-[10px] opacity-60 mt-0.5">{session.message_count} messages</div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-4">
          {!currentSessionId && messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-4xl shadow-glow-lg animate-float"
              >
                🤖
              </motion.div>
              <div className="text-center">
                <h2 className="text-xl font-bold text-foreground">FinPilot AI Agents</h2>
                <p className="text-muted-foreground text-sm mt-1 max-w-md">
                  Ask anything about your financial documents. Our 17 AI agents will
                  analyze, search, and deliver expert insights in real-time.
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id} message={msg} isLast={i === messages.length - 1} />
              ))}
              {isStreaming && messages[messages.length - 1]?.content === "" && (
                <TypingIndicator />
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          isStreaming={isStreaming}
          sessionId={currentSessionId}
        />
      </div>
    </div>
  );
}
