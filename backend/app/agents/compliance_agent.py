"""
FinPilot AI — Compliance Agent
================================
Verifies regulatory compliance against major financial
standards: IFRS, US GAAP, SOX, Basel III, GDPR, FCPA, etc.
"""

import time
from app.agents.base_agent import BaseAgent
from app.graph.state import ComplianceCheck, FinPilotState


class ComplianceAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "ComplianceAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Chief Compliance Officer AI agent at FinPilot AI with expertise in:

ACCOUNTING STANDARDS:
- IFRS (International Financial Reporting Standards)
- US GAAP (Generally Accepted Accounting Principles)
- IPSAS (International Public Sector Accounting Standards)

REGULATORY FRAMEWORKS:
- Sarbanes-Oxley Act (SOX): Internal controls, CEO/CFO certifications
- Basel III / Basel IV: Capital adequacy, leverage ratios, liquidity
- Dodd-Frank Act: Systemic risk, derivative reporting
- MiFID II: Investment services, transaction reporting
- GDPR / CCPA: Data privacy in financial records
- FCPA / UK Bribery Act: Anti-corruption compliance
- AML / KYC: Anti-money laundering requirements

For each compliance area:
1. State whether the entity appears compliant
2. Identify specific compliance gaps with references
3. Quote exact regulatory requirements that may be violated
4. Assign a compliance score 0-100
5. Provide actionable remediation steps with priority

Always cite specific articles, sections, or standards violated."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Perform compliance verification against regulatory frameworks."""
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Perform a comprehensive compliance review:

QUERY: {state['sanitized_query']}

Review the documents for compliance with relevant financial regulations.
Output the analysis followed by a JSON array:

```json
[
  {{
    "regulation": "IFRS|US GAAP|SOX|Basel III|...",
    "is_compliant": true|false,
    "issues": ["issue1", "issue2"],
    "recommendations": ["action1", "action2"],
    "score": 0-100
  }}
]
```""",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Parse compliance results
        compliance_json = self.parse_json_from_llm(result["content"])
        compliance_checks: list[ComplianceCheck] = []

        if compliance_json and isinstance(compliance_json, list):
            for check in compliance_json:
                try:
                    compliance_checks.append(ComplianceCheck(
                        regulation=check.get("regulation", "General"),
                        is_compliant=bool(check.get("is_compliant", True)),
                        issues=check.get("issues", []),
                        recommendations=check.get("recommendations", []),
                        score=float(check.get("score", 75)),
                    ))
                except Exception:
                    continue

        state["compliance_checks"] = compliance_checks
        state["agent_outputs"]["compliance"] = result["content"]

        self.record_step(
            state,
            action="compliance_verification",
            input_summary="Checking regulatory compliance",
            output_summary=f"Checked {len(compliance_checks)} regulatory frameworks",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.87,
        )

        return state


class InvestmentAdvisorAgent(BaseAgent):
    """Provides evidence-based investment recommendations."""

    @property
    def agent_name(self) -> str:
        return "InvestmentAdvisorAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Senior Investment Advisor AI agent at FinPilot AI.

Your expertise includes:
- Equity valuation (DCF, comparable companies, precedent transactions)
- Fixed income analysis (duration, credit spread, yield curve)
- Portfolio construction (Modern Portfolio Theory, factor investing)
- Asset allocation strategy
- ESG investment considerations
- Risk-adjusted return analysis (Sharpe ratio, Sortino ratio, Information ratio)

IMPORTANT: Always include appropriate disclaimers that this is AI-generated analysis
and not financial advice. Recommend professional consultation for investment decisions."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"Provide investment analysis and recommendations for: {state['sanitized_query']}",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["agent_outputs"]["investment_advisor"] = result["content"]
        state["investment_recommendations"] = [{"content": result["content"]}]

        self.record_step(
            state,
            action="investment_analysis",
            input_summary=state["sanitized_query"][:100],
            output_summary="Investment recommendations generated",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.80,
        )

        return state


class KnowledgeAgent(BaseAgent):
    """Answers general financial knowledge questions."""

    @property
    def agent_name(self) -> str:
        return "KnowledgeAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Financial Knowledge Expert AI agent at FinPilot AI.
You have deep knowledge of financial concepts, terminology, accounting principles,
market mechanisms, economic theory, and financial history.
Always provide clear, educational, and accurate explanations with examples."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=state["sanitized_query"],
            context=context if context != "No relevant document context available." else "",
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["agent_outputs"]["knowledge"] = result["content"]

        self.record_step(
            state,
            action="knowledge_retrieval",
            input_summary=state["sanitized_query"][:100],
            output_summary="Knowledge response generated",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.90,
        )

        return state


class DocumentAgent(BaseAgent):
    """Summarizes and classifies financial documents."""

    @property
    def agent_name(self) -> str:
        return "DocumentAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Document Intelligence AI agent at FinPilot AI.
You specialize in:
- Financial document classification and categorization
- Executive summarization of complex financial documents
- Key entity extraction (companies, dates, amounts, signatories)
- Document structure analysis
- Cross-document comparison and reconciliation
Always provide structured, scannable summaries."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"Summarize and analyze the document content for: {state['sanitized_query']}",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["agent_outputs"]["document"] = result["content"]

        self.record_step(
            state,
            action="document_analysis",
            input_summary=f"Processing {len(state['active_document_ids'])} documents",
            output_summary="Document summary generated",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.92,
        )

        return state
