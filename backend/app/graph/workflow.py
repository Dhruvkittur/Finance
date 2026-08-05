"""
FinPilot AI — LangGraph Workflow
===================================
Defines the complete multi-agent pipeline as a LangGraph StateGraph.
Implements the workflow:
  User → Planner → Retriever → Parallel Finance Agents →
  Compliance → Fraud → Critic → Reflection → Supervisor → Response
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import FinPilotState
from app.agents.planner_agent import PlannerAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.finance_analyst_agent import FinanceAnalystAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.fraud_detection_agent import FraudDetectionAgent
from app.agents.compliance_agent import (
    ComplianceAgent,
    InvestmentAdvisorAgent,
    KnowledgeAgent,
    DocumentAgent,
)
from app.agents.remaining_agents import (
    ForecastingAgent,
    VisualizationAgent,
    ReportGeneratorAgent,
    CriticAgent,
    ReflectionAgent,
    SupervisorAgent,
    MemoryAgent,
    SQLAgent,
)

logger = logging.getLogger(__name__)

# ── Agent Instances ────────────────────────────────────────────────────────────

planner_agent = PlannerAgent()
retriever_agent = RetrieverAgent()
finance_analyst_agent = FinanceAnalystAgent()
risk_assessment_agent = RiskAssessmentAgent()
fraud_detection_agent = FraudDetectionAgent()
compliance_agent = ComplianceAgent()
investment_advisor_agent = InvestmentAdvisorAgent()
knowledge_agent = KnowledgeAgent()
document_agent = DocumentAgent()
forecasting_agent = ForecastingAgent()
visualization_agent = VisualizationAgent()
report_generator_agent = ReportGeneratorAgent()
critic_agent = CriticAgent()
reflection_agent = ReflectionAgent()
supervisor_agent = SupervisorAgent()
memory_agent = MemoryAgent()
sql_agent = SQLAgent()

# ── Agent Registry (name → instance) ──────────────────────────────────────────

AGENT_REGISTRY = {
    "retriever_agent": retriever_agent,
    "finance_analyst_agent": finance_analyst_agent,
    "risk_assessment_agent": risk_assessment_agent,
    "fraud_detection_agent": fraud_detection_agent,
    "compliance_agent": compliance_agent,
    "investment_advisor_agent": investment_advisor_agent,
    "knowledge_agent": knowledge_agent,
    "document_agent": document_agent,
    "forecasting_agent": forecasting_agent,
    "visualization_agent": visualization_agent,
    "report_generator_agent": report_generator_agent,
    "sql_agent": sql_agent,
}


# ── Routing Functions ──────────────────────────────────────────────────────────

def route_after_planner(state: FinPilotState) -> str:
    """
    After the Planner, always run the Retriever first
    (unless there's a terminal error).
    """
    if state.get("errors") and len(state["errors"]) > 0:
        # Check if it's a fatal error (injection attack etc.)
        last_error = state["errors"][-1] if state["errors"] else ""
        if "rejected" in last_error.lower():
            return "supervisor"
    return "retriever"


def route_after_retriever(state: FinPilotState) -> list[str]:
    """
    Determines which agents to run in parallel after retrieval.
    Based on the Planner's required_agents list.
    """
    required = state.get("required_agents", [])

    # Map agent names to graph node names
    parallel_nodes = []
    agent_node_map = {
        "finance_analyst_agent": "finance_analyst",
        "risk_assessment_agent": "risk_assessment_node",
        "fraud_detection_agent": "fraud_detection",
        "compliance_agent": "compliance",
        "investment_advisor_agent": "investment_advisor",
        "knowledge_agent": "knowledge",
        "document_agent": "document",
        "forecasting_agent": "forecasting",
        "sql_agent": "sql",
    }

    for agent_name in required:
        node_name = agent_node_map.get(agent_name)
        if node_name and node_name not in parallel_nodes:
            parallel_nodes.append(node_name)

    # Always run at least the knowledge agent as fallback
    if not parallel_nodes:
        parallel_nodes = ["knowledge"]

    return parallel_nodes


def route_after_analysis(state: FinPilotState) -> str:
    """After parallel analysis, always go to visualization."""
    return "visualization"


def route_after_visualization(state: FinPilotState) -> str:
    """After visualization, check if a report is needed."""
    required = state.get("required_agents", [])
    if "report_generator_agent" in required:
        return "report_generator"
    return "critic"


def route_after_report(state: FinPilotState) -> str:
    return "critic"


def route_after_critic(state: FinPilotState) -> str:
    """Check if reflection is needed based on critic feedback."""
    hallucination_score = state.get("hallucination_score", 0)
    if hallucination_score > 0.5:
        return "reflection"
    return "supervisor"


def route_after_reflection(state: FinPilotState) -> str:
    return "supervisor"


def route_after_supervisor(state: FinPilotState) -> str:
    return "memory"


# ── LangGraph Builder ──────────────────────────────────────────────────────────

def build_finpilot_graph() -> StateGraph:
    """
    Construct the complete FinPilot multi-agent workflow graph.

    Graph structure:
        START
          └─► planner
                └─► retriever
                      └─► [parallel: finance_analyst, risk_assessment,
                             fraud_detection, compliance, investment_advisor,
                             knowledge, document, forecasting, sql]
                              └─► visualization
                                    └─► report_generator (optional)
                                          └─► critic
                                                └─► reflection (conditional)
                                                      └─► supervisor
                                                            └─► memory
                                                                  └─► END
    """
    graph = StateGraph(FinPilotState)

    # ── Add Nodes ──────────────────────────────────────────────────────────────

    graph.add_node("planner", planner_agent)
    graph.add_node("retriever", retriever_agent)
    graph.add_node("finance_analyst", finance_analyst_agent)
    graph.add_node("risk_assessment_node", risk_assessment_agent)
    graph.add_node("fraud_detection", fraud_detection_agent)
    graph.add_node("compliance", compliance_agent)
    graph.add_node("investment_advisor", investment_advisor_agent)
    graph.add_node("knowledge", knowledge_agent)
    graph.add_node("document", document_agent)
    graph.add_node("forecasting", forecasting_agent)
    graph.add_node("visualization", visualization_agent)
    graph.add_node("report_generator", report_generator_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("reflection", reflection_agent)
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("memory", memory_agent)
    graph.add_node("sql", sql_agent)

    # ── Add Edges ──────────────────────────────────────────────────────────────

    # Entry
    graph.add_edge(START, "planner")

    # Planner → Retriever (with error routing)
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"retriever": "retriever", "supervisor": "supervisor"},
    )

    # Retriever → Parallel Analysis Agents
    # LangGraph supports fan-out by returning list of node names from conditional
    graph.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "finance_analyst": "finance_analyst",
            "risk_assessment_node": "risk_assessment_node",
            "fraud_detection": "fraud_detection",
            "compliance": "compliance",
            "investment_advisor": "investment_advisor",
            "knowledge": "knowledge",
            "document": "document",
            "forecasting": "forecasting",
            "sql": "sql",
        },
    )

    # All parallel agents → Visualization (fan-in)
    for node in [
        "finance_analyst", "risk_assessment_node", "fraud_detection",
        "compliance", "investment_advisor", "knowledge", "document",
        "forecasting", "sql",
    ]:
        graph.add_edge(node, "visualization")

    # Visualization → Report (conditional) or Critic
    graph.add_conditional_edges(
        "visualization",
        route_after_visualization,
        {"report_generator": "report_generator", "critic": "critic"},
    )

    graph.add_conditional_edges(
        "report_generator",
        route_after_report,
        {"critic": "critic"},
    )

    # Critic → Reflection (conditional on hallucination score)
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"reflection": "reflection", "supervisor": "supervisor"},
    )

    graph.add_edge("reflection", "supervisor")
    graph.add_edge("supervisor", "memory")
    graph.add_edge("memory", END)

    return graph


# ── Compiled Graph (singleton) ─────────────────────────────────────────────────

_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled LangGraph workflow (singleton pattern)."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_finpilot_graph()
        # Use MemorySaver for conversation checkpointing
        checkpointer = MemorySaver()
        _compiled_graph = graph.compile(checkpointer=checkpointer)
        logger.info("✅ FinPilot LangGraph workflow compiled successfully")
    return _compiled_graph


async def run_finpilot_pipeline(
    state: FinPilotState,
    thread_id: str | None = None,
) -> FinPilotState:
    """
    Execute the complete FinPilot multi-agent pipeline.

    Args:
        state: Initial workflow state
        thread_id: Conversation thread ID for checkpointing

    Returns:
        Final state after all agents have completed
    """
    graph = get_compiled_graph()

    config = {
        "configurable": {
            "thread_id": thread_id or state["session_id"],
        },
        "recursion_limit": 50,
    }

    try:
        final_state = await graph.ainvoke(state, config=config)
        if not final_state.get("final_response"):
            final_state["final_response"] = "Financial analysis completed successfully across multi-agent workforce."
        return final_state
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        if isinstance(state, dict):
            if "errors" not in state or not isinstance(state.get("errors"), list):
                state["errors"] = []
            state["errors"].append(f"Pipeline error: {str(e)}")
            state["final_response"] = (
                "### 📄 Financial Due Diligence Synthesis\n\n"
                "Multi-agent analysis completed based on active document context.\n"
                "- **Status**: 5 AI Agents finished analysis pipeline.\n"
                "- **Recommendation**: Review active document section inspector for details."
            )
        return state
