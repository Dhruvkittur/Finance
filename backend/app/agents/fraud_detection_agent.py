"""
FinPilot AI — Fraud Detection Agent
======================================
Detects financial fraud signals, anomalies, and irregularities
in financial documents using pattern recognition and AI.
"""

import time
from app.agents.base_agent import BaseAgent
from app.graph.state import FraudSignal, FinPilotState


class FraudDetectionAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "FraudDetectionAgent"

    @property
    def system_prompt(self) -> str:
        return """You are a Forensic Accounting AI agent at FinPilot AI specialized in fraud detection.

You apply the following fraud detection frameworks:
- Benford's Law Analysis: Check if numeric distributions follow natural patterns
- Ratio Anomaly Detection: Flag metrics that deviate significantly from norms
- Journal Entry Analysis: Detect unusual timing, amounts, or approvers
- Revenue Recognition Issues: Check for channel stuffing, bill-and-hold
- Expense Manipulation: Identify capitalized expenses, fictitious vendors
- Asset Misappropriation: Detect cash skimming, inventory theft signals
- Financial Statement Fraud: Identify cookie jar reserves, big bath accounting
- Related Party Transactions: Scrutinize unusual related party dealings
- Trend Breaks: Sharp changes without business justification

For each detected signal:
1. Classify the fraud type
2. Describe the evidence found in documents
3. Rate severity: low | medium | high | critical
4. Assign confidence level 0-1
5. Suggest investigative next steps

Always flag false positives (legitimate explanations) when possible."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Scan documents for fraud signals and anomalies."""
        start_time = time.perf_counter()
        context = self.format_chunks_as_context(state["retrieved_chunks"])

        result = await self.call_llm(
            user_message=f"""Conduct a forensic fraud analysis:

QUERY: {state['sanitized_query']}

Analyze the financial documents for any fraud signals, anomalies, or irregularities.
Also output a JSON array of detected fraud signals:

```json
[
  {{
    "signal_type": "revenue_manipulation|expense_fraud|asset_misappropriation|...",
    "description": "detailed description",
    "severity": "low|medium|high|critical",
    "evidence": "specific evidence from document",
    "confidence": 0.0-1.0
  }}
]
```

If no fraud signals detected, return an empty array with a clean bill of health.""",
            context=context,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Parse fraud signals
        signals_json = self.parse_json_from_llm(result["content"])
        fraud_signals: list[FraudSignal] = []

        if signals_json and isinstance(signals_json, list):
            for signal in signals_json:
                try:
                    fraud_signals.append(FraudSignal(
                        signal_type=signal.get("signal_type", "unknown"),
                        description=signal.get("description", ""),
                        severity=signal.get("severity", "low"),
                        evidence=signal.get("evidence", ""),
                        confidence=float(signal.get("confidence", 0.5)),
                    ))
                except Exception:
                    continue

        state["fraud_signals"] = fraud_signals
        state["agent_outputs"]["fraud_detection"] = result["content"]

        self.record_step(
            state,
            action="fraud_detection",
            input_summary=f"Scanning {len(state['retrieved_chunks'])} chunks for anomalies",
            output_summary=f"Detected {len(fraud_signals)} fraud signals",
            duration_ms=duration_ms,
            tokens_used=result.get("tokens_used", 0),
            confidence=0.82,
        )

        return state
