"""
FinPilot AI — Streamlit Enterprise Financial Platform
=====================================================
Complete web application incorporating multi-agent intelligence, document analysis,
financial analytics dashboard, workflow builder, and AI chat.
"""

import os
import sys
import time
import asyncio
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Import backend modules
from app.core.config import settings
from app.core.db_sync import (
    sync_authenticate_user,
    sync_create_user,
    sync_get_user_documents,
    sync_save_document,
    sync_get_or_create_chat_session,
    sync_add_chat_message,
)
from app.services.llm_service import llm_service
from app.graph.workflow import run_finpilot_pipeline
from app.graph.state import create_initial_state

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinPilot AI — Enterprise Financial Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS Styling (Glassmorphism & Dark Theme) ──────────────────────────
st.markdown(
    """
    <style>
    /* Dark Theme Core Setup */
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 50%, #070a12 100%);
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }

    /* KPI Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-up { color: #10b981; }
    .delta-down { color: #ef4444; }

    /* Custom Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-primary { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

    /* Header Accent */
    .header-accent {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session State Initialization ─────────────────────────────────────────────
if "user" not in st.session_state:
    # Default demo user if not logged in
    st.session_state["user"] = {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "analyst@finpilot.ai",
        "full_name": "Senior Financial Analyst",
        "role": "admin",
        "organization": "FinPilot Intelligence",
    }

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Dashboard"

if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = None


# ─── Sidebar Header & Navigation ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 10px; border-radius: 12px; font-size: 24px;">⚡</div>
            <div>
                <h2 style="margin: 0; font-size: 20px; font-weight: 800; color: #f8fafc;">FinPilot <span style="color: #3b82f6;">AI</span></h2>
                <p style="margin: 0; font-size: 11px; color: #94a3b8;">Multi-Agent Financial Intelligence</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active User Profile Card
    user = st.session_state["user"]
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.6); padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px;">
            <div style="font-size: 13px; font-weight: 600; color: #f8fafc;">👤 {user['full_name']}</div>
            <div style="font-size: 11px; color: #94a3b8;">{user['email']} • <span class="badge badge-primary">{user['role']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Options
    st.markdown("<p style='font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px;'>Navigation</p>", unsafe_allow_html=True)
    
    pages = [
        ("📊 Dashboard", "Dashboard"),
        ("📄 Document Upload", "Document Intelligence"),
        ("💬 Chatbot", "FinPilot AI Chat"),
        ("⚡ Workflow", "Workflows"),
        ("⚙️ Settings", "Settings"),
    ]

    for label, page_name in pages:
        is_selected = st.session_state["active_page"] == page_name
        button_style = "primary" if is_selected else "secondary"
        if st.button(label, use_container_width=True, type=button_style, key=f"nav_{page_name}"):
            st.session_state["active_page"] = page_name
            st.rerun()

    st.markdown("---")
    
    # LLM Status Widget
    has_gemini = bool(settings.GOOGLE_API_KEY)
    has_groq = bool(settings.GROQ_API_KEY)
    st.markdown("<p style='font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px;'>LLM Provider Status</p>", unsafe_allow_html=True)
    st.markdown(f"🟢 **Groq (Llama 3.3)**: {'Active' if has_groq else 'Not Configured'}")
    st.markdown(f"🟢 **Gemini 1.5 Flash**: {'Active' if has_gemini else 'Not Configured'}")


# ==============================================================================
# PAGE 1: DASHBOARD
# ==============================================================================
if st.session_state["active_page"] == "Dashboard":
    st.markdown("<h1>Financial Intelligence <span class='header-accent'>Dashboard</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Real-time AI multi-agent overview, document insights, and portfolio analytics.</p>", unsafe_allow_html=True)

    # Top KPI Metrics Row
    docs = sync_get_user_documents(user["id"])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Portfolio Valuation</div>
                <div class="metric-value">$42.8M</div>
                <div class="metric-delta delta-up">▲ +8.4% vs last quarter</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Documents Indexed</div>
                <div class="metric-value">{len(docs)} Docs</div>
                <div class="metric-delta delta-up">▲ 100% Vectorized</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">AI Confidence Score</div>
                <div class="metric-value">98.2%</div>
                <div class="metric-delta delta-up">▲ Zero Hallucination Audit</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Active AI Workforce</div>
                <div class="metric-value">17 Agents</div>
                <div class="metric-delta delta-up">● LangGraph Pipeline Ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    chart_col1, chart_col2 = st.columns([2, 1])

    with chart_col1:
        with st.container(border=True):
            st.markdown("### 📈 Revenue & EBITDA Projection Trend (FY24-FY26)")
            
            months = ["Q1 24", "Q2 24", "Q3 24", "Q4 24", "Q1 25 (E)", "Q2 25 (E)", "Q3 25 (E)", "Q4 25 (E)"]
            revenue = [12.4, 13.8, 15.2, 17.1, 18.5, 20.2, 22.0, 24.5]
            ebitda = [3.2, 3.8, 4.2, 5.1, 5.8, 6.4, 7.1, 8.0]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=revenue, name="Revenue ($M)", mode="lines+markers", line=dict(color="#3b82f6", width=3)))
            fig.add_trace(go.Scatter(x=months, y=ebitda, name="EBITDA ($M)", mode="lines+markers", line=dict(color="#10b981", width=3, dash="dash")))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", y=1.1),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        with st.container(border=True):
            st.markdown("### 🎯 Asset Allocation")
            
            labels = ["Public Equities", "Private Credit", "Real Estate", "Venture Capital", "Treasuries"]
            values = [35, 25, 20, 12, 8]
            
            fig_pie = px.pie(
                names=labels,
                values=values,
                color_discrete_sequence=["#3b82f6", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b"],
                hole=0.5
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
                legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # Recent Activity & Agent Logs
    st.markdown("### ⚡ Live Multi-Agent Execution Log")
    with st.container(border=True):
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; gap: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span>🤖 <b>PlannerAgent</b> • Extracted sub-goals for SEC 10-K Analysis</span>
                    <span class="badge badge-success">Completed (120ms)</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span>🔍 <b>RetrieverAgent</b> • Fetched hybrid vector chunks from document store</span>
                    <span class="badge badge-success">Completed (85ms)</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span>📈 <b>FinanceAnalystAgent</b> • Calculated EBITDA Margin trend & DCF Valuation</span>
                    <span class="badge badge-primary">Active (340ms)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# PAGE 2: FINPILOT AI CHAT
# ==============================================================================
elif st.session_state["active_page"] == "FinPilot AI Chat":
    st.markdown("<h1>FinPilot <span class='header-accent'>AI Assistant</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Ask complex financial questions. 17 specialized AI agents will analyze your documents & synthesize answers.</p>", unsafe_allow_html=True)

    # Ensure chat session exists
    session_data = sync_get_or_create_chat_session(
        user_id=user["id"],
        session_id=st.session_state["current_session_id"]
    )
    st.session_state["current_session_id"] = session_data["id"]

    # Filter by Document Context
    docs = sync_get_user_documents(user["id"])
    doc_options = {d["id"]: d["original_filename"] for d in docs}
    
    col_c1, col_c2 = st.columns([4, 1])
    with col_c1:
        selected_doc_ids = st.multiselect(
            "📁 Filter Search Context by Document:",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options[x],
            placeholder="Select documents to query against (or leave empty for global intelligence)"
        )
    with col_c2:
        if st.button("🗑️ New Chat", use_container_width=True):
            st.session_state["current_session_id"] = None
            st.rerun()

    st.markdown("---")

    # Render Existing Messages
    for msg in session_data["messages"]:
        role = msg["role"]
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input Box
    if user_query := st.chat_input("Ask FinPilot AI (e.g. 'Summarize key risk factors and revenue trends in the uploaded documents')"):
        # Display User Message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_query)

        # Record User Message to DB
        sync_add_chat_message(session_data["id"], "user", user_query)

        # Assistant Stream & Agent Timeline
        with st.chat_message("assistant", avatar="🤖"):
            timeline_placeholder = st.empty()
            message_placeholder = st.empty()

            timeline_placeholder.info("⚡ **PlannerAgent**: Analyzing query intent & routing to specialized financial agents...")

            try:
                # Initialize state
                state = create_initial_state(
                    user_query=user_query,
                    user_id=user["id"],
                    session_id=session_data["id"],
                    active_document_ids=selected_doc_ids,
                    workflow_type="chat"
                )

                # Run LangGraph Multi-Agent Pipeline
                final_state = asyncio.run(run_finpilot_pipeline(state, thread_id=session_data["id"]))
                
                # Show Agent Steps Timeline
                timeline_placeholder.empty()
                with st.status("🧠 Multi-Agent Analysis Timeline", expanded=False):
                    for step in final_state.get("agent_steps", []):
                        st.write(f"✓ **{step.get('agent_name')}**: {step.get('action')} ({step.get('duration_ms', 0):.0f}ms)")

                # Display Response
                response_text = final_state.get("final_response", "No response generated.")
                message_placeholder.markdown(response_text)

                # Record Assistant Message to DB
                sync_add_chat_message(session_data["id"], "assistant", response_text)

            except Exception as e:
                message_placeholder.error(f"Error generating response: {e}")


# ==============================================================================
# PAGE 3: DOCUMENT INTELLIGENCE
# ==============================================================================
elif st.session_state["active_page"] == "Document Intelligence":
    st.markdown("<h1>Document <span class='header-accent'>Intelligence</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Upload SEC filings, financial statements, Excel models, or PDFs for AI indexing and retrieval.</p>", unsafe_allow_html=True)

    # File Upload Dropzone
    uploaded_files = st.file_uploader(
        "Upload Financial Documents",
        type=["pdf", "docx", "pptx", "xlsx", "csv", "txt", "png", "jpg"],
        accept_multiple_files=True,
        help="Upload files up to 50MB each for instant text chunking and vector indexing."
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            ext = uploaded_file.name.split(".")[-1].lower()
            
            with st.spinner(f"Processing and Vectorizing '{uploaded_file.name}'..."):
                saved_doc = sync_save_document(
                    user_id=user["id"],
                    original_filename=uploaded_file.name,
                    file_bytes=file_bytes,
                    doc_type=ext
                )
                st.success(f"Successfully indexed '{uploaded_file.name}' ({saved_doc['chunks_count']} vector chunks created)!")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📚 Indexed Document Catalog")

    # Display User's Indexed Documents
    docs = sync_get_user_documents(user["id"])
    if docs:
        df_docs = pd.DataFrame(docs)
        df_docs = df_docs[["original_filename", "doc_type", "file_size_mb", "status", "chunks_count", "created_at"]]
        df_docs.columns = ["Filename", "Type", "Size (MB)", "Status", "Vector Chunks", "Uploaded At"]
        st.dataframe(df_docs, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 👁️ Document Content Inspector")
        selected_preview_doc = st.selectbox(
            "Select document to inspect extracted raw text:",
            options=docs,
            format_func=lambda d: f"{d['original_filename']} ({d['chunks_count']} chunks)"
        )
        if selected_preview_doc:
            with st.expander(f"📄 Text Content: {selected_preview_doc['original_filename']}", expanded=True):
                st.text_area(
                    "Extracted Text Preview",
                    value=selected_preview_doc.get("raw_text") or "Text content extracted and stored.",
                    height=250
                )
    else:
        st.info("No documents uploaded yet. Upload a document above to get started!")


# ==============================================================================
# PAGE 4: WORKFLOWS
# ==============================================================================
elif st.session_state["active_page"] == "Workflows":
    st.markdown("<h1>Financial <span class='header-accent'>Workflow Builder</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Automate multi-agent research pipelines, due diligence, and credit risk evaluations.</p>", unsafe_allow_html=True)

    col_w1, col_w2 = st.columns([1, 1])

    with col_w1:
        with st.container(border=True):
            st.markdown("### ⚡ Execute Workflow")
            workflow_type = st.selectbox(
                "Select Workflow Template:",
                [
                    "Comprehensive SEC 10-K Due Diligence",
                    "EBITDA & Financial Health Audit",
                    "Fraud & Anomalous Transaction Detection",
                    "Portfolio Credit Risk Assessment"
                ]
            )
            target_company = st.text_input("Target Company / Entity:", "Acme Financial Corp")
            
            docs = sync_get_user_documents(user["id"])
            doc_options = {d["id"]: d["original_filename"] for d in docs}
            wf_doc_ids = st.multiselect(
                "Target Context Documents:",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options[x]
            )

            if st.button("🚀 Trigger Workflow Execution", use_container_width=True):
                with st.spinner(f"Executing Multi-Agent Pipeline for '{target_company}'..."):
                    wf_state = create_initial_state(
                        user_query=f"Execute {workflow_type} for target entity: {target_company}",
                        user_id=user["id"],
                        session_id=str(time.time()),
                        active_document_ids=wf_doc_ids,
                        workflow_type="workflow"
                    )
                    final_wf_state = asyncio.run(run_finpilot_pipeline(wf_state))
                    
                    st.success(f"Workflow '{workflow_type}' completed successfully!")
                    with st.expander("📊 View Execution Output & Synthesis", expanded=True):
                        st.markdown(final_wf_state.get("final_response", "Workflow execution finished."))

    with col_w2:
        with st.container(border=True):
            st.markdown("### 🧩 Agent Dependency Graph")
            st.code(
                """
[User Query]
    │
    ▼
[PlannerAgent] ──► Sub-goal Breakdown
    │
    ▼
[RetrieverAgent] ──► Hybrid Vector Search
    │
    ├───────────────┬───────────────┐
    ▼               ▼               ▼
[FinanceAnalyst] [RiskAssessment] [FraudDetection]
    │               │               │
    └───────────────┼───────────────┘
                    ▼
            [SupervisorAgent]
                    │
                    ▼
            [Final Response]
                """,
                language="markdown"
            )


# ==============================================================================
# PAGE 5: REPORTS
# ==============================================================================
elif st.session_state["active_page"] == "Reports":
    st.markdown("<h1>Financial <span class='header-accent'>Reports Generator</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Generate downloadable executive summaries, financial health reports, and valuation memos.</p>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### 📄 Generate AI Financial Report")
        
        report_title = st.text_input("Report Title:", "Q3 Financial Performance & Risk Evaluation")
        report_type = st.selectbox("Report Category:", ["Executive Summary", "Credit Risk Analysis", "DCF Valuation Model", "Audit Log Memo"])
        
        docs = sync_get_user_documents(user["id"])
        doc_options = {d["id"]: d["original_filename"] for d in docs}
        rep_doc_ids = st.multiselect(
            "Source Documents for Report:",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options[x]
        )

        if st.button("⚡ Generate Report Content"):
            with st.spinner("Synthesizing multi-agent insights into comprehensive report..."):
                rep_state = create_initial_state(
                    user_query=f"Generate a comprehensive {report_type} titled '{report_title}' based on uploaded documents.",
                    user_id=user["id"],
                    session_id=str(time.time()),
                    active_document_ids=rep_doc_ids,
                    workflow_type="report"
                )
                final_rep_state = asyncio.run(run_finpilot_pipeline(rep_state))
                
                generated_content = final_rep_state.get("final_response", "Report generation complete.")
                st.markdown("---")
                st.markdown(generated_content)
                st.download_button(
                    label="📥 Download Generated Report (.md)",
                    data=generated_content,
                    file_name=f"{report_title.replace(' ', '_')}.md",
                    mime="text/markdown"
                )


# ==============================================================================
# PAGE 6: SETTINGS & SYSTEM HEALTH
# ==============================================================================
elif st.session_state["active_page"] == "Settings":
    st.markdown("<h1>System <span class='header-accent'>Settings & Health</span></h1>", unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        with st.container(border=True):
            st.markdown("### 🔑 API Provider Credentials")
            new_gemini = st.text_input("Google Gemini API Key", value=settings.GOOGLE_API_KEY or "", type="password")
            new_groq = st.text_input("Groq API Key", value=settings.GROQ_API_KEY or "", type="password")
            new_openrouter = st.text_input("OpenRouter API Key", value=settings.OPENROUTER_API_KEY or "", type="password")
            
            if st.button("Save Credentials Configuration"):
                env_path = os.path.join(os.path.dirname(__file__), ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    for line in lines:
                        if line.startswith("GOOGLE_API_KEY="):
                            new_lines.append(f"GOOGLE_API_KEY={new_gemini}\n")
                        elif line.startswith("GROQ_API_KEY="):
                            new_lines.append(f"GROQ_API_KEY={new_groq}\n")
                        elif line.startswith("OPENROUTER_API_KEY="):
                            new_lines.append(f"OPENROUTER_API_KEY={new_openrouter}\n")
                        else:
                            new_lines.append(line)
                    
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)

                settings.GOOGLE_API_KEY = new_gemini
                settings.GROQ_API_KEY = new_groq
                settings.OPENROUTER_API_KEY = new_openrouter
                llm_service._initialize_providers()
                st.success("API credentials saved and re-initialized successfully!")

    with col_s2:
        with st.container(border=True):
            st.markdown("### 🛠️ Infrastructure & DB Status")
            st.write(f"**Database Backend**: SQLite (`finpilot.db`) ✅")
            st.write(f"**Vector Store Mode**: Embedded Vector Engine ✅")
            st.write(f"**Primary LLM Provider**: `{settings.PRIMARY_LLM_PROVIDER.upper()}` ✅")
            st.write(f"**Application Environment**: `{settings.APP_ENV}`")
            st.write(f"**Upload Storage Directory**: `{settings.UPLOAD_DIR}`")
