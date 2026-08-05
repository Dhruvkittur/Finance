"""
FinPilot AI — Planner Agent
=============================
Orchestrates the multi-agent pipeline by:
1. Understanding the user's intent
2. Decomposing complex tasks into sub-tasks
3. Selecting which specialized agents to invoke
4. Setting the response format and scope
"""

import time
import json
from app.agents.base_agent import BaseAgent
from app.graph.state import FinPilotState
from app.core.security import sanitize_user_input


class PlannerAgent(BaseAgent):
    """
    The Planner Agent is the entry point of the LangGraph pipeline.
    It analyzes the user's query and creates an execution plan
    that determines which downstream agents are needed.
    """

    @property
    def agent_name(self) -> str:
        return "PlannerAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Planner Agent of FinPilot AI, an Enterprise Multi-Agent Financial Intelligence Platform.

Your role is to:
1. Analyze the user's financial query or request
2. Identify the intent (analysis, search, report, forecast, compliance check, fraud detection, etc.)
3. Decompose complex requests into atomic sub-tasks
4. Select the appropriate specialized agents from the available roster
5. Define the expected output format

AVAILABLE AGENTS:
- retriever_agent: Searches and retrieves relevant document chunks from the knowledge base
- finance_analyst_agent: Analyzes financial statements, ratios, and performance metrics
- risk_assessment_agent: Evaluates financial and operational risks
- fraud_detection_agent: Detects anomalies and potential fraud signals
- investment_advisor_agent: Provides investment insights and recommendations
- compliance_agent: Checks regulatory compliance (IFRS, GAAP, SOX, Basel III)
- knowledge_agent: Answers general financial knowledge questions
- sql_agent: Queries structured financial data
- document_agent: Summarizes and classifies documents
- forecasting_agent: Predicts future financial trends
- visualization_agent: Generates chart data for visual representation
- report_generator_agent: Compiles comprehensive reports

ALWAYS include retriever_agent when the query requires document context.
ALWAYS include visualization_agent when numerical data or trends are involved.

Respond ONLY with valid JSON in this exact format:
{
  "intent": "brief description of user intent",
  "complexity": "simple|moderate|complex",
  "required_agents": ["agent1", "agent2"],
  "parallel_agents": ["agents that can run in parallel"],
  "sequential_agents": [["step1_agents"], ["step2_agents"]],
  "sub_tasks": [
    {"agent": "agent_name", "task": "specific task description"}
  ],
  "response_format": "markdown|json|table",
  "context_needed": true|false,
  "estimated_confidence": 0.0-1.0
}"""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Analyze query and create the execution plan."""
        start_time = time.perf_counter()
        query = state["user_query"]

        # Sanitize user input (prompt injection protection)
        try:
            sanitized = sanitize_user_input(query)
            state["sanitized_query"] = sanitized
        except ValueError as e:
            state["errors"].append(f"Input rejected: {str(e)}")
            state["final_response"] = "Your input was rejected for security reasons. Please rephrase your question."
            return state

        # Call LLM to create the plan
        result = await self.call_llm(
            user_message=f"""Analyze this financial query and create an execution plan:

USER QUERY: {sanitized}

DOCUMENT CONTEXT AVAILABLE: {len(state['active_document_ids'])} documents uploaded

Return the execution plan as JSON.""",
            temperature=0.0,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Parse the plan
        plan = self.parse_json_from_llm(result["content"])

        if not plan:
            # Fallback plan for when JSON parsing fails
            plan = self._create_fallback_plan(query)

        # Update state with the plan
        state["planner_output"] = plan
        state["required_agents"] = plan.get("required_agents", ["retriever_agent", "knowledge_agent"])
        state["response_format"] = plan.get("response_format", "markdown")

        self.record_step(
            state,
            action="query_analysis",
            input_summary=query[:200],
            output_summary=f"Plan created: {len(state['required_agents'])} agents required",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=plan.get("estimated_confidence", 0.85),
        )

        return state

    def _create_fallback_plan(self, query: str) -> dict:
        """Create a highly optimized, fast execution plan."""
        query_lower = query.lower()
        agents = ["retriever_agent"]

        if any(w in query_lower for w in ["fraud", "anomaly", "suspicious", "irregular"]):
            agents.append("fraud_detection_agent")
        elif any(w in query_lower for w in ["comply", "compliance", "regulation", "ifrs", "gaap", "sox"]):
            agents.append("compliance_agent")
        elif any(w in query_lower for w in ["risk", "exposure"]):
            agents.append("risk_assessment_agent")
        elif any(w in query_lower for w in ["forecast", "predict"]):
            agents.append("forecasting_agent")
        else:
            agents.append("finance_analyst_agent")

        return {
            "intent": "financial analysis",
            "complexity": "low",
            "required_agents": list(dict.fromkeys(agents)),
            "response_format": "markdown",
            "context_needed": True,
            "estimated_confidence": 0.90,
        }
