# FinPilot AI 🤖
## Enterprise Multi-Agent Financial Intelligence Platform

> **"Autonomous AI Workforce for Modern Finance"**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61dafb)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.50-orange)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Enterprise-red)](LICENSE)

---

## 🚀 Overview

FinPilot AI is a **production-ready enterprise application** that deploys 17 specialized AI agents to autonomously analyze financial documents, detect fraud, ensure compliance, generate reports, and deliver real-time investment insights.

### 🤖 The 17-Agent Workforce

| # | Agent | Capability |
|---|-------|------------|
| 1 | **PlannerAgent** | Query decomposition, intent classification, agent routing |
| 2 | **RetrieverAgent** | Hybrid semantic + keyword document search |
| 3 | **FinanceAnalystAgent** | P&L, balance sheet, ratio analysis (CFA-level) |
| 4 | **RiskAssessmentAgent** | Market, credit, liquidity, operational, compliance risk scoring |
| 5 | **FraudDetectionAgent** | Benford's Law, anomaly detection, forensic accounting |
| 6 | **ComplianceAgent** | IFRS, US GAAP, SOX, Basel III, GDPR verification |
| 7 | **InvestmentAdvisorAgent** | DCF, portfolio theory, factor investing recommendations |
| 8 | **KnowledgeAgent** | Financial concepts, theory, market mechanisms Q&A |
| 9 | **SQLAgent** | Natural language to SQL for structured financial data |
| 10 | **DocumentAgent** | Document classification, summarization, entity extraction |
| 11 | **ForecastingAgent** | Revenue projection, scenario analysis, Monte Carlo |
| 12 | **VisualizationAgent** | Recharts-compatible chart generation |
| 13 | **ReportGeneratorAgent** | McKinsey-quality executive report compilation |
| 14 | **CriticAgent** | Output quality review, hallucination detection |
| 15 | **ReflectionAgent** | Self-improvement based on critic feedback |
| 16 | **SupervisorAgent** | Final quality gate, response composition |
| 17 | **MemoryAgent** | Long-term conversation context management |

---

## 🏗️ Architecture

```
frontend (React 19 + Vite + TailwindCSS)
    │
    │ REST API + SSE + WebSocket
    ▼
backend (FastAPI + Uvicorn)
    │
    ├─► LangGraph Pipeline (17 agents)
    │       ├─► Planner → Retriever → [Parallel Agents] → Supervisor
    │       └─► ChromaDB (Vector Store)
    │
    ├─► PostgreSQL (SQLAlchemy ORM)
    ├─► Redis (Caching, Rate Limiting, Pub/Sub)
    └─► Celery (Background Tasks)
```

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI 0.115 + Uvicorn
- LangGraph 0.2.50 (multi-agent orchestration)
- Gemini 2.5 Flash / Groq Llama / OpenRouter (LLM fallback chain)
- ChromaDB (vector store with hybrid search)
- SQLAlchemy 2.0 async + PostgreSQL
- Redis (caching, rate limiting, pub/sub)
- Celery (async document processing)
- pdfplumber + python-docx + openpyxl (document extraction)
- JWT + RBAC (security)

**Frontend:**
- React 19 + TypeScript + Vite
- TailwindCSS + Framer Motion (animations)
- Redux Toolkit + TanStack Query (state + data fetching)
- React Router v6 (routing)
- Recharts (charts)
- @xyflow/react (workflow builder)
- React Dropzone (file upload)
- React Markdown + remark-gfm (markdown rendering)
- Server-Sent Events (SSE) for streaming

---

## ⚡ Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker + Docker Compose (recommended)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone and setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker compose up -d

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
cp ../.env.example .env

# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key         # Google AI Studio
GROQ_API_KEY=your_groq_api_key             # Groq (fallback)
OPENROUTER_API_KEY=your_openrouter_key     # OpenRouter (second fallback)

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/finpilot

# Security
SECRET_KEY=your_super_secret_key_here      # 64+ chars recommended
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET  | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/chat/sessions` | Create chat session |
| GET  | `/api/v1/chat/sessions` | List sessions |
| POST | `/api/v1/chat/sessions/{id}/messages` | Send message (SSE streaming) |
| WS   | `/api/v1/chat/ws/{session_id}` | WebSocket chat |
| POST | `/api/v1/documents/upload` | Upload document |
| GET  | `/api/v1/documents` | List documents |
| POST | `/api/v1/documents/search` | Semantic search |
| GET  | `/api/v1/dashboard/kpis` | Dashboard KPIs |
| GET  | `/api/v1/analytics/token-usage` | Usage analytics |
| GET  | `/api/v1/admin/users` | User management (admin) |

---

## 🔒 Security Features

- JWT-based authentication with refresh token rotation
- Role-Based Access Control (Admin, Manager, Analyst, Viewer)
- Prompt injection detection and sanitization
- PII redaction in logs
- Request rate limiting via Redis
- Audit logging for all sensitive operations
- Bcrypt password hashing

---

## 📄 Supported Document Types

| Type | Processing |
|------|------------|
| PDF | pdfplumber + OCR fallback |
| DOCX | python-docx |
| XLSX/CSV | openpyxl + pandas |
| PPTX | python-pptx |
| TXT | Direct parsing |
| Images | PIL + Tesseract OCR |

---

## 🌟 Key Features

- **Real-time Streaming**: SSE + WebSocket for live AI responses
- **Agent Timeline**: Visual reasoning chain showing each agent's contribution
- **Citation System**: Every insight linked to source document + page number
- **Hallucination Detection**: Critic agent scores output quality and flags risks
- **Visual Workflow Builder**: React Flow drag-and-drop pipeline designer
- **Analytics Dashboard**: Token usage, cost tracking, agent performance metrics
- **PWA Support**: Works offline, installable as desktop app

---

## 🏆 Hackathon-Ready Features

1. **17-Agent Parallelism**: LangGraph fan-out for concurrent analysis
2. **Multi-Model Fallback**: Gemini → Groq → OpenRouter resilience
3. **Glassmorphism UI**: Premium dark mode with animated gradients
4. **Enterprise Security**: JWT + RBAC + audit logs + rate limiting
5. **Real-time Everything**: SSE streaming + WebSocket + Redis pub/sub
6. **PWA**: Offline support, installable

---

*Built with ❤️ by the FinPilot AI team*
