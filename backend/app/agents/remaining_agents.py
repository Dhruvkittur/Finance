"""
FinPilot AI — Forecasting, Visualization, Report Generator,
Critic, Reflection, Supervisor, Memory Agents
"""

import time
import json
from app.agents.base_agent import BaseAgent
from app.graph.state import ChartData, FinPilotState


class ForecastingAgent(BaseAgent):
    """Predicts financial trends and future performance."""

    @property
    def agent_name(self) -> str:
        return "ForecastingAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Quantitative Financial Forecasting AI agent at FinPilot AI.

You specialize in:
- Revenue and earnings forecasting using multiple methods:
  * Time series analysis (ARIMA, exponential smoothing)
  * Linear regression with financial drivers
  * Scenario analysis (bull / base / bear)
- Cash flow projection (13-week, 1-year, 3-year)
- Budget vs. actuals variance analysis
- Working capital cycle forecasting
- Sensitivity analysis and Monte Carlo simulation summaries
- "What-if" scenario modeling

Always provide:
1. Base case, optimistic, and pessimistic scenarios
2. Key assumptions clearly stated
3. Risk factors that could materially affect forecasts
4. Confidence intervals where applicable
5. Comparable with analyst consensus where available

Important: Clearly state that forecasts are probabilistic estimates, not guarantees."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Generate financial forecasts for: {state['sanitized_query']}

Provide:
1. Detailed forecast analysis with scenarios
2. Forecast data JSON for charting:
```json
{{
  "forecast_periods": ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"],
  "base_case": [1000000, 1050000, 1100000, 1150000],
  "optimistic": [1100000, 1200000, 1300000, 1400000],
  "pessimistic": [900000, 920000, 950000, 980000],
  "metric": "Revenue",
  "currency": "USD",
  "assumptions": ["assumption1", "assumption2"]
}}
```""",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        forecast_json = self.parse_json_from_llm(result["content"])
        state["forecast_data"] = forecast_json
        state["agent_outputs"]["forecasting"] = result["content"]

        # Generate chart data for forecast
        if forecast_json and isinstance(forecast_json, dict):
            periods = forecast_json.get("forecast_periods", [])
            if periods:
                chart_data = []
                for i, period in enumerate(periods):
                    chart_data.append({
                        "period": period,
                        "base_case": forecast_json.get("base_case", [])[i] if i < len(forecast_json.get("base_case", [])) else None,
                        "optimistic": forecast_json.get("optimistic", [])[i] if i < len(forecast_json.get("optimistic", [])) else None,
                        "pessimistic": forecast_json.get("pessimistic", [])[i] if i < len(forecast_json.get("pessimistic", [])) else None,
                    })

                state["charts"].append(ChartData(
                    chart_type="area",
                    title=f"Financial Forecast: {forecast_json.get('metric', 'Revenue')}",
                    data=chart_data,
                    x_key="period",
                    y_keys=["base_case", "optimistic", "pessimistic"],
                    colors=["#3b82f6", "#22c55e", "#ef4444"],
                    unit=forecast_json.get("currency", "USD"),
                ))

        self.record_step(
            state,
            action="financial_forecasting",
            input_summary=state["sanitized_query"][:100],
            output_summary=f"Forecast generated with {len(state['charts'])} charts",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.78,
        )

        return state


class VisualizationAgent(BaseAgent):
    """Generates structured chart data for the frontend."""

    @property
    def agent_name(self) -> str:
        return "VisualizationAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Financial Data Visualization AI agent at FinPilot AI.

Your role is to transform financial data into beautiful, insightful visualizations.
You generate structured JSON data compatible with Recharts (React charting library).

Chart types you can produce:
- bar: Comparing categories (revenue by quarter, department costs)
- line: Trends over time (stock price, revenue growth)
- area: Volume/magnitude trends (cumulative cash flow)
- pie: Composition (revenue breakdown, expense categories)
- scatter: Correlation analysis (revenue vs. headcount)
- heatmap: Risk matrices, correlation matrices
- composed: Multi-metric comparisons

Always:
1. Choose the most appropriate chart type for the data
2. Use meaningful color schemes (green for positive, red for negative, blue for neutral)
3. Include axis labels and units
4. Add descriptive titles
5. Limit data points to avoid overplotting"""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        # Gather available data for visualization
        financial_data = ""
        if state.get("financial_metrics"):
            metrics = state["financial_metrics"]
            financial_data = f"Financial Metrics: {json.dumps(metrics, default=str)}"

        if state.get("financial_analysis"):
            financial_data += f"\n\nFinancial Analysis: {state['financial_analysis'][:2000]}"

        if not financial_data:
            financial_data = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Generate chart data visualizations for: {state['sanitized_query']}

Based on the available financial data, create 2-3 relevant charts.
Return a JSON array of chart objects:

```json
[
  {{
    "chart_type": "bar|line|pie|area|scatter",
    "title": "Chart Title",
    "data": [
      {{"label": "Q1 2024", "value": 1000000, "category": "Revenue"}}
    ],
    "x_key": "label",
    "y_keys": ["value"],
    "colors": ["#3b82f6", "#22c55e"],
    "unit": "USD"
  }}
]
```""",
            context=financial_data,
            temperature=0.2,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        charts_json = self.parse_json_from_llm(result["content"])
        if charts_json and isinstance(charts_json, list):
            for chart in charts_json:
                try:
                    state["charts"].append(ChartData(
                        chart_type=chart.get("chart_type", "bar"),
                        title=chart.get("title", "Financial Data"),
                        data=chart.get("data", []),
                        x_key=chart.get("x_key", "label"),
                        y_keys=chart.get("y_keys", ["value"]),
                        colors=chart.get("colors"),
                        unit=chart.get("unit"),
                    ))
                except Exception:
                    continue

        state["agent_outputs"]["visualization"] = f"Generated {len(state['charts'])} charts"

        self.record_step(
            state,
            action="chart_generation",
            input_summary="Generating visualizations from financial data",
            output_summary=f"Created {len(state['charts'])} charts",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.90,
        )

        return state


class ReportGeneratorAgent(BaseAgent):
    """Compiles all agent outputs into a comprehensive executive report."""

    @property
    def agent_name(self) -> str:
        return "ReportGeneratorAgent"

    @property
    def system_prompt(self) -> str:
        return """You are an Executive Report Generator AI agent at FinPilot AI.

You synthesize outputs from all specialized agents into polished, board-ready reports.
Your reports follow McKinsey/Goldman Sachs quality standards:
- Clear executive summary (3-5 key takeaways)
- Structured sections with headers
- Data-backed conclusions
- Actionable recommendations with priorities
- Professional, concise language (no jargon without explanation)
- Tables and bullet points for scannability

Report types you can generate:
- Executive Summary Report
- Financial Performance Report
- Risk & Compliance Report
- Investment Analysis Report
- Financial Forecast Report
- Fraud Investigation Report
- Board Presentation Deck Content"""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        # Compile all agent outputs
        compiled_analysis = ""
        if state.get("financial_analysis"):
            compiled_analysis += f"\n\n## Financial Analysis\n{state['financial_analysis']}"
        if state.get("risk_assessment"):
            compiled_analysis += f"\n\n## Risk Assessment\n{json.dumps(state['risk_assessment'], default=str)}"
        if state.get("compliance_checks"):
            compiled_analysis += f"\n\n## Compliance\n{json.dumps(state['compliance_checks'], default=str)}"
        if state.get("fraud_signals"):
            compiled_analysis += f"\n\n## Fraud Signals\n{json.dumps(state['fraud_signals'], default=str)}"
        for agent, output in state.get("agent_outputs", {}).items():
            if output and agent not in ["finance_analyst", "risk_assessment"]:
                compiled_analysis += f"\n\n## {agent.replace('_', ' ').title()}\n{str(output)[:1000]}"

        result = await self.call_llm(
            user_message=f"""Generate a comprehensive executive report for: {state['sanitized_query']}

Synthesize all the analysis into a polished, board-ready report with:
1. Executive Summary (key findings in 3-5 bullet points)
2. Financial Overview (metrics and trends)
3. Key Findings (from all agents)
4. Risk Assessment Summary
5. Compliance Status
6. Recommendations (prioritized, actionable)
7. Conclusion

Make it professional, concise, and visually structured with markdown.""",
            context=compiled_analysis,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["agent_outputs"]["report_generator"] = result["content"]

        self.record_step(
            state,
            action="report_compilation",
            input_summary=f"Compiling {len(state['agent_outputs'])} agent outputs",
            output_summary="Executive report generated",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.88,
        )

        return state


class CriticAgent(BaseAgent):
    """Critically evaluates the quality and accuracy of agent outputs."""

    @property
    def agent_name(self) -> str:
        return "CriticAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Critic Agent of FinPilot AI — a rigorous quality evaluator.

Your role is to critically review the responses from other agents and identify:
1. Factual errors or inconsistencies with the source documents
2. Logical gaps or unsupported conclusions
3. Missing context or important caveats
4. Hallucinated numbers or made-up facts
5. Overconfident claims without evidence
6. Incomplete analyses

You score the response quality 0-100 and provide specific, actionable feedback.
Be rigorous but fair — not everything needs revision."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        # Gather all outputs to critique
        outputs_to_review = json.dumps(state.get("agent_outputs", {}), default=str)[:3000]

        result = await self.call_llm(
            user_message=f"""Critically evaluate these financial AI agent outputs:

ORIGINAL QUERY: {state['sanitized_query']}

AGENT OUTPUTS:
{outputs_to_review}

Provide:
1. Quality score (0-100)
2. Specific issues found
3. Recommendations for improvement
4. Assessment of factual accuracy
5. Hallucination risk assessment (0-1, where 1 = high risk)""",
            temperature=0.0,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        state["critic_feedback"] = result["content"]

        # Extract hallucination score
        hallucination_score = 0.1  # default low
        if "hallucin" in result["content"].lower():
            import re
            match = re.search(r"hallucination[:\s]+(\d+(?:\.\d+)?)", result["content"].lower())
            if match:
                val = float(match.group(1))
                hallucination_score = val if val <= 1 else val / 100

        state["hallucination_score"] = hallucination_score

        self.record_step(
            state,
            action="quality_review",
            input_summary="Reviewing all agent outputs for quality",
            output_summary=f"Critique complete, hallucination risk: {hallucination_score:.2f}",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.92,
        )

        return state


class ReflectionAgent(BaseAgent):
    """Reflects on the pipeline outputs and improves the final response."""

    @property
    def agent_name(self) -> str:
        return "ReflectionAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Reflection Agent of FinPilot AI.

Your role is to:
1. Review the critic's feedback
2. Identify what information is missing
3. Determine if additional retrieval or analysis is needed
4. Synthesize all inputs into an improved, coherent response
5. Ensure the response directly addresses the user's query
6. Remove hallucinated content flagged by the Critic
7. Add appropriate disclaimers where needed"""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        critic_fb = str(state.get("critic_feedback") or "No critic feedback available.")
        agent_outputs = json.dumps(state.get("agent_outputs") or {}, default=str)[:3000]

        result = await self.call_llm(
            user_message=f"""Reflect on and improve the response for:
QUERY: {state['sanitized_query']}

CRITIC FEEDBACK: {critic_fb[:1000]}

Based on the critique and all agent outputs, provide reflection notes
on how to improve the final response quality.""",
            temperature=0.3,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["reflection_notes"] = result["content"]

        self.record_step(
            state,
            action="reflection",
            input_summary="Reflecting on critic feedback",
            output_summary="Reflection complete, improvements identified",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.90,
        )

        return state


class SupervisorAgent(BaseAgent):
    """Final quality gate before response delivery."""

    @property
    def agent_name(self) -> str:
        return "SupervisorAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Supervisor Agent of FinPilot AI — the final quality gate.

You review the complete pipeline output and:
1. Approve or reject the response for delivery
2. Compose the final, polished response to the user
3. Ensure citations are properly included
4. Add appropriate financial disclaimers
5. Ensure response format matches user expectations
6. Compute final confidence score

Always format the response in clear, professional markdown.
Include citation references as [Source N] notation."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        # Gather all analysis for final synthesis
        all_analysis = ""
        if state.get("report_generator") or "report_generator" in state.get("agent_outputs", {}):
            all_analysis = state["agent_outputs"].get("report_generator", "")
        if not all_analysis:
            all_analysis = "\n\n".join(
                str(v) for v in state.get("agent_outputs", {}).values() if v
            )[:4000]

        # Include citation list
        citations_text = ""
        for i, citation in enumerate(state.get("citations", [])[:10]):
            citations_text += f"\n[Source {i+1}] {citation['document_name']} (relevance: {citation['similarity_score']:.2%})"

        refl_notes = str(state.get('reflection_notes') or '')

        result = await self.call_llm(
            user_message=f"""Compose the final response for the user:

USER QUERY: {state['sanitized_query']}

ANALYSIS AVAILABLE:
{all_analysis}

AVAILABLE SOURCES:
{citations_text}

REFLECTION NOTES: {refl_notes[:500]}

Compose a complete, professional response that:
1. Directly answers the user's question
2. Incorporates key findings from all agents
3. References sources with [Source N] notation
4. Includes appropriate disclaimers
5. Is formatted in clear markdown with headers and bullets
6. Ends with a Confidence: X% statement""",
            temperature=0.2,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        state["final_response"] = result["content"]
        state["supervisor_approved"] = True
        state["confidence_score"] = self.extract_confidence(result["content"])

        # Update total cost
        from app.services.llm_service import llm_service
        state["total_cost_usd"] = llm_service.estimate_cost(
            state["total_tokens_used"],
            provider=state.get("llm_provider_used", "gemini")
        )

        self.record_step(
            state,
            action="final_synthesis",
            input_summary="Composing final response",
            output_summary=f"Response approved. Confidence: {state['confidence_score']:.2%}",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=state["confidence_score"],
        )

        return state


class MemoryAgent(BaseAgent):
    """Manages conversation memory and long-term context."""

    @property
    def agent_name(self) -> str:
        return "MemoryAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Memory Agent of FinPilot AI.
You manage conversation context and extract important facts for long-term storage.
Identify: key entities, decisions made, important numbers, user preferences."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Extract and store important facts from this conversation turn."""
        start_time = time.perf_counter()

        result = await self.call_llm(
            user_message=f"""Extract key facts to remember from this conversation:
Query: {state['sanitized_query']}
Response summary: {str(state.get('final_response', ''))[:500]}

Extract as JSON:
{{"key_facts": [], "entities": {{}}, "decisions": [], "follow_up_needed": []}}""",
            temperature=0.0,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        memory_data = self.parse_json_from_llm(result["content"])

        if memory_data:
            state["agent_outputs"]["memory"] = memory_data

        self.record_step(
            state,
            action="memory_update",
            input_summary="Extracting conversation facts",
            output_summary="Memory updated with key facts",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.95,
        )

        return state


class SQLAgent(BaseAgent):
    """Queries structured financial data using natural language SQL."""

    @property
    def agent_name(self) -> str:
        return "SQLAgent"

    @property
    def system_prompt(self) -> str:
        return """You are an SQL Agent at FinPilot AI specialized in financial database queries.
You translate natural language financial questions into SQL queries and interpret results.
You understand financial database schemas for balance sheets, income statements, and transaction data."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        start_time = time.perf_counter()

        result = await self.call_llm(
            user_message=f"Generate and explain SQL query for: {state['sanitized_query']}",
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        state["agent_outputs"]["sql"] = result["content"]

        self.record_step(
            state,
            action="sql_generation",
            input_summary=state["sanitized_query"][:100],
            output_summary="SQL query generated",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.85,
        )

        return state
