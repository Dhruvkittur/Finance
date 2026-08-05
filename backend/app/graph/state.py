"""
FinPilot AI — LangGraph State Definition
==========================================
Defines the shared state schema for the multi-agent workflow.
All agents read from and write to this state object.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentStep(TypedDict):
    """Records a single step taken by an agent in the pipeline."""
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: float
    tokens_used: int
    confidence: float
    timestamp: str


class Citation(TypedDict):
    """A citation linking AI output to a source document chunk."""
    document_id: str
    document_name: str
    chunk_content: str
    page_number: Optional[int]
    similarity_score: float
    chunk_index: int


class ChartData(TypedDict):
    """Structured data for chart rendering in the frontend."""
    chart_type: str        # bar | line | pie | area | scatter | heatmap
    title: str
    data: list[dict]       # Recharts-compatible data array
    x_key: str
    y_keys: list[str]
    colors: Optional[list[str]]
    unit: Optional[str]


class FinancialMetrics(TypedDict):
    """Extracted financial KPIs from analyzed documents."""
    revenue: Optional[float]
    net_income: Optional[float]
    gross_profit: Optional[float]
    operating_income: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    cash_and_equivalents: Optional[float]
    earnings_per_share: Optional[float]
    pe_ratio: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    return_on_equity: Optional[float]
    profit_margin: Optional[float]
    revenue_growth: Optional[float]
    period: Optional[str]
    currency: str


class RiskAssessment(TypedDict):
    """Risk analysis results from the Risk Assessment Agent."""
    overall_risk_score: float          # 0-100, higher = more risk
    risk_level: str                    # low | medium | high | critical
    market_risk: float
    credit_risk: float
    liquidity_risk: float
    operational_risk: float
    compliance_risk: float
    risk_factors: list[str]
    mitigation_strategies: list[str]


class FraudSignal(TypedDict):
    """Fraud detection signal from the Fraud Detection Agent."""
    signal_type: str
    description: str
    severity: str          # low | medium | high | critical
    evidence: str
    confidence: float


class ComplianceCheck(TypedDict):
    """Compliance verification result."""
    regulation: str           # IFRS | GAAP | SOX | Basel III | etc.
    is_compliant: bool
    issues: list[str]
    recommendations: list[str]
    score: float              # 0-100


def take_last(left: Any, right: Any) -> Any:
    return right if right is not None else left

def merge_dicts(left: Optional[dict], right: Optional[dict]) -> dict:
    res = dict(left or {})
    if right:
        res.update(right)
    return res

def append_steps(left: Optional[list], right: Optional[list]) -> list:
    res = list(left or [])
    if right:
        for item in right:
            if item not in res:
                res.append(item)
    return res


class FinPilotState(TypedDict):
    """
    The complete shared state object for the FinPilot multi-agent workflow.
    Passed through all nodes in the LangGraph pipeline.
    """

    # ── Session Identity ───────────────────────────────────────────────────────
    session_id: Annotated[str, take_last]
    run_id: Annotated[str, take_last]
    user_id: Annotated[str, take_last]
    user_query: Annotated[str, take_last]
    sanitized_query: Annotated[str, take_last]

    # ── Message History ────────────────────────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Active Documents ───────────────────────────────────────────────────────
    active_document_ids: Annotated[list[str], take_last]
    retrieved_chunks: Annotated[list[dict], take_last]
    citations: Annotated[list[Citation], append_steps]

    # ── Agent Routing ──────────────────────────────────────────────────────────
    planner_output: Annotated[Optional[dict], take_last]
    required_agents: Annotated[list[str], take_last]
    agent_outputs: Annotated[dict[str, Any], merge_dicts]

    # ── Agent Timeline ─────────────────────────────────────────────────────────
    agent_steps: Annotated[list[AgentStep], append_steps]

    # ── Financial Analysis ─────────────────────────────────────────────────────
    financial_metrics: Annotated[Optional[FinancialMetrics], take_last]
    financial_analysis: Annotated[Optional[str], take_last]
    risk_assessment: Annotated[Optional[RiskAssessment], take_last]
    fraud_signals: Annotated[list[FraudSignal], append_steps]
    compliance_checks: Annotated[list[ComplianceCheck], append_steps]
    investment_recommendations: Annotated[list[dict], append_steps]
    forecast_data: Annotated[Optional[dict], take_last]

    # ── Output Quality ─────────────────────────────────────────────────────────
    confidence_score: Annotated[float, take_last]
    hallucination_score: Annotated[float, take_last]
    critic_feedback: Annotated[Optional[str], take_last]
    reflection_notes: Annotated[Optional[str], take_last]
    supervisor_approved: Annotated[bool, take_last]

    # ── Visualizations ─────────────────────────────────────────────────────────
    charts: Annotated[list[ChartData], append_steps]
    tables: Annotated[list[dict], append_steps]

    # ── Final Response ─────────────────────────────────────────────────────────
    final_response: Annotated[Optional[str], take_last]
    response_format: Annotated[str, take_last]

    # ── Usage Tracking ─────────────────────────────────────────────────────────
    total_tokens_used: Annotated[int, take_last]
    total_cost_usd: Annotated[float, take_last]
    llm_provider_used: Annotated[str, take_last]
    total_duration_ms: Annotated[float, take_last]

    # ── Metadata ──────────────────────────────────────────────────────────────
    workflow_type: Annotated[str, take_last]
    timestamp: Annotated[str, take_last]
    errors: Annotated[list[str], append_steps]
    warnings: Annotated[list[str], append_steps]


def create_initial_state(
    user_query: str,
    user_id: str,
    session_id: str,
    active_document_ids: Optional[list[str]] = None,
    workflow_type: str = "chat",
) -> FinPilotState:
    """
    Factory function to create a fresh FinPilotState for a new pipeline run.

    Args:
        user_query: The user's natural language question or request
        user_id: Authenticated user's ID
        session_id: Chat session ID
        active_document_ids: Documents to search during retrieval
        workflow_type: Type of workflow being executed

    Returns:
        Initialized FinPilotState dict
    """
    return FinPilotState(
        session_id=session_id,
        run_id=str(uuid.uuid4()),
        user_id=user_id,
        user_query=user_query,
        sanitized_query=user_query,
        messages=[],
        active_document_ids=active_document_ids or [],
        retrieved_chunks=[],
        citations=[],
        planner_output=None,
        required_agents=[],
        agent_outputs={},
        agent_steps=[],
        financial_metrics=None,
        financial_analysis=None,
        risk_assessment=None,
        fraud_signals=[],
        compliance_checks=[],
        investment_recommendations=[],
        forecast_data=None,
        confidence_score=0.0,
        hallucination_score=0.0,
        critic_feedback=None,
        reflection_notes=None,
        supervisor_approved=False,
        charts=[],
        tables=[],
        final_response=None,
        response_format="markdown",
        total_tokens_used=0,
        total_cost_usd=0.0,
        llm_provider_used="",
        total_duration_ms=0.0,
        workflow_type=workflow_type,
        timestamp=datetime.utcnow().isoformat(),
        errors=[],
        warnings=[],
    )
