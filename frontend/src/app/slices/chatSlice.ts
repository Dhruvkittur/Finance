/**
 * FinPilot AI — Chat Redux Slice
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Citation {
  document_id: string;
  document_name: string;
  chunk_content: string;
  page_number?: number;
  similarity_score: number;
}

interface AgentStep {
  agent_name: string;
  action: string;
  input_summary: string;
  output_summary: string;
  duration_ms: number;
  tokens_used: number;
  confidence: number;
  timestamp: string;
}

interface ChartData {
  chart_type: string;
  title: string;
  data: Record<string, any>[];
  x_key: string;
  y_keys: string[];
  colors?: string[];
  unit?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  agent_timeline?: AgentStep[];
  charts?: ChartData[];
  tables?: any[];
  confidence_score?: number;
  tokens_used?: number;
  agents_used?: string[];
  created_at: string;
  isStreaming?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  activeDocumentIds: string[];
  agentSteps: AgentStep[];
  isLoading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  streamingContent: "",
  activeDocumentIds: [],
  agentSteps: [],
  isLoading: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    setSessions(state, action: PayloadAction<ChatSession[]>) {
      state.sessions = action.payload;
    },
    setCurrentSession(state, action: PayloadAction<string | null>) {
      state.currentSessionId = action.payload;
      state.messages = [];
      state.agentSteps = [];
    },
    setMessages(state, action: PayloadAction<Message[]>) {
      state.messages = action.payload;
    },
    addMessage(state, action: PayloadAction<Message>) {
      state.messages.push(action.payload);
    },
    updateLastMessage(state, action: PayloadAction<Partial<Message>>) {
      const last = state.messages[state.messages.length - 1];
      if (last) {
        Object.assign(last, action.payload);
      }
    },
    setStreaming(state, action: PayloadAction<boolean>) {
      state.isStreaming = action.payload;
      if (!action.payload) {
        state.streamingContent = "";
      }
    },
    appendStreamChunk(state, action: PayloadAction<string>) {
      state.streamingContent += action.payload;
      // Update the last assistant message content
      const last = state.messages[state.messages.length - 1];
      if (last && last.role === "assistant") {
        last.content = state.streamingContent;
      }
    },
    addAgentStep(state, action: PayloadAction<AgentStep>) {
      state.agentSteps.push(action.payload);
    },
    clearAgentSteps(state) {
      state.agentSteps = [];
    },
    setActiveDocumentIds(state, action: PayloadAction<string[]>) {
      state.activeDocumentIds = action.payload;
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    resetChat(state) {
      state.messages = [];
      state.streamingContent = "";
      state.isStreaming = false;
      state.agentSteps = [];
      state.error = null;
    },
  },
});

export const {
  setSessions,
  setCurrentSession,
  setMessages,
  addMessage,
  updateLastMessage,
  setStreaming,
  appendStreamChunk,
  addAgentStep,
  clearAgentSteps,
  setActiveDocumentIds,
  setLoading,
  setError,
  resetChat,
} = chatSlice.actions;

export default chatSlice.reducer;
