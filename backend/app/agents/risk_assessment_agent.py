"""
FinPilot AI — Risk Assessment Agent
======================================
Evaluates financial, operational, market, credit,
liquidity, and compliance risks from financial documents.
"""

import time
from app.agents.base_agent import BaseAgent
from app.graph.state import FinPilotState, RiskAssessment


class RiskAssessmentAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "RiskAssessmentAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Chief Risk Officer AI agent at FinPilot AI with deep expertise in:
- Market Risk: Interest rate, FX, equity, commodity risks
- Credit Risk: Counterparty exposure, default probability, credit ratings
- Liquidity Risk: Cash position, working capital, funding gaps
- Operational Risk: Process failures, system risks, human errors
- Compliance Risk: Regulatory violations, reporting deficiencies
- Reputational Risk: ESG factors, governance issues
- Concentration Risk: Over-exposure to single customers, sectors, geographies

For every risk assessment:
1. Score each risk category 0-100 (0=no risk, 100=critical)
2. Identify specific risk factors with evidence from documents
3. Quantify risk where possible ($ amounts, percentages)
4. Map risks to business impact
5. Provide concrete mitigation strategies

Always output a structured risk scorecard with an overall risk level:
LOW (0-25) | MEDIUM (26-50) | HIGH (51-75) | CRITICAL (76-100)"""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Conduct comprehensive risk assessment."""
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Conduct a comprehensive risk assessment:

QUERY: {state['sanitized_query']}

Analyze all risk dimensions and output:
1. Detailed risk analysis narrative
2. Risk scorecard JSON at the end:

```json
{{
  "overall_risk_score": 0-100,
  "risk_level": "low|medium|high|critical",
  "market_risk": 0-100,
  "credit_risk": 0-100,
  "liquidity_risk": 0-100,
  "operational_risk": 0-100,
  "compliance_risk": 0-100,
  "risk_factors": ["factor1", "factor2"],
  "mitigation_strategies": ["strategy1", "strategy2"]
}}
```""",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Parse structured risk data
        risk_json = self.parse_json_from_llm(result["content"])
        if risk_json and isinstance(risk_json, dict):
            try:
                state["risk_assessment"] = RiskAssessment(
                    overall_risk_score=float(risk_json.get("overall_risk_score", 50)),
                    risk_level=risk_json.get("risk_level", "medium"),
                    market_risk=float(risk_json.get("market_risk", 50)),
                    credit_risk=float(risk_json.get("credit_risk", 50)),
                    liquidity_risk=float(risk_json.get("liquidity_risk", 50)),
                    operational_risk=float(risk_json.get("operational_risk", 50)),
                    compliance_risk=float(risk_json.get("compliance_risk", 50)),
                    risk_factors=risk_json.get("risk_factors", []),
                    mitigation_strategies=risk_json.get("mitigation_strategies", []),
                )
            except Exception:
                pass

        state["agent_outputs"]["risk_assessment"] = result["content"]

        self.record_step(
            state,
            action="risk_assessment",
            input_summary=f"Evaluating risks across {len(state['retrieved_chunks'])} document chunks",
            output_summary=f"Risk level: {state.get('risk_assessment', {}).get('risk_level', 'unknown') if state['risk_assessment'] else 'analyzed'}",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.85,
        )

        return state
