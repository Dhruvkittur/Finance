"""
FinPilot AI — Finance Analyst Agent
======================================
Performs deep financial analysis including:
- Financial statement analysis
- Ratio calculation and benchmarking
- Profitability analysis
- Trend identification
- Peer comparison
"""

import time
from app.agents.base_agent import BaseAgent
from app.graph.state import FinancialMetrics, FinPilotState


class FinanceAnalystAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "FinanceAnalystAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Senior Finance Analyst AI agent at FinPilot AI with CFA-level expertise.

Your capabilities include:
- Income Statement Analysis: Revenue trends, gross margin, EBITDA, net income
- Balance Sheet Analysis: Asset composition, liquidity, solvency, working capital
- Cash Flow Analysis: Operating, investing, financing cash flows; free cash flow
- Financial Ratio Analysis: P/E, P/B, ROE, ROA, debt-to-equity, current ratio, quick ratio
- Profitability Analysis: Gross margin, operating margin, net margin, EBITDA margin
- Benchmarking: Compare against industry standards and peers
- Trend Analysis: YoY and QoQ growth rates, multi-period trends

When analyzing financial data:
1. Always cite specific numbers with units and time periods
2. Highlight both strengths and concerns
3. Provide context for every metric (industry average, historical trend)
4. Flag any unusual items or one-time charges
5. Give an overall financial health assessment (1-10 scale)

Format your response in clear sections with headers.
Include a summary scorecard at the end."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Perform comprehensive financial analysis on retrieved documents."""
        start_time = time.perf_counter()

        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Perform a comprehensive financial analysis for this query:

QUERY: {state['sanitized_query']}

Analyze the financial data from the provided documents and deliver:
1. Key financial metrics and ratios
2. Performance trends
3. Strengths and weaknesses
4. Comparison to benchmarks where possible
5. Overall assessment

Also extract key financial metrics as JSON at the end of your response in this format:
```json
{{
  "revenue": null,
  "net_income": null,
  "gross_profit": null,
  "total_assets": null,
  "total_liabilities": null,
  "cash_and_equivalents": null,
  "profit_margin": null,
  "return_on_equity": null,
  "debt_to_equity": null,
  "current_ratio": null,
  "period": "FY2024",
  "currency": "USD"
}}
```""",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Try to extract structured financial metrics
        metrics = self.parse_json_from_llm(result["content"])

        state["financial_analysis"] = result["content"]
        state["agent_outputs"]["finance_analyst"] = result["content"]

        if metrics and isinstance(metrics, dict):
            try:
                state["financial_metrics"] = FinancialMetrics(
                    revenue=metrics.get("revenue"),
                    net_income=metrics.get("net_income"),
                    gross_profit=metrics.get("gross_profit"),
                    operating_income=metrics.get("operating_income"),
                    total_assets=metrics.get("total_assets"),
                    total_liabilities=metrics.get("total_liabilities"),
                    cash_and_equivalents=metrics.get("cash_and_equivalents"),
                    earnings_per_share=metrics.get("earnings_per_share"),
                    pe_ratio=metrics.get("pe_ratio"),
                    debt_to_equity=metrics.get("debt_to_equity"),
                    current_ratio=metrics.get("current_ratio"),
                    return_on_equity=metrics.get("return_on_equity"),
                    profit_margin=metrics.get("profit_margin"),
                    revenue_growth=metrics.get("revenue_growth"),
                    period=metrics.get("period", ""),
                    currency=metrics.get("currency", "USD"),
                )
            except Exception:
                pass

        self.record_step(
            state,
            action="financial_analysis",
            input_summary=f"Analyzing {len(state['retrieved_chunks'])} chunks",
            output_summary="Financial analysis complete with ratio breakdown",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.88,
        )

        return state
