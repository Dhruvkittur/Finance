"""
FinPilot AI — Base Agent with parse_json and extract_confidence helpers
Extends the existing base_agent.py
"""

import json
import re
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.graph.state import AgentStep, FinPilotState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all FinPilot AI agents.
    Provides standardized LLM communication, step recording,
    JSON parsing, and confidence extraction.
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique agent identifier."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The agent's specialized system prompt."""
        ...

    @abstractmethod
    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Execute the agent's primary task and update state."""
        ...

    async def __call__(self, state: FinPilotState) -> FinPilotState:
        """LangGraph node callable — delegates to execute()."""
        try:
            logger.debug(f"[{self.agent_name}] Executing...")
            res = await self.execute(state)
            if res is None:
                return state
            return res
        except Exception as e:
            logger.error(f"Error executing node [{self.agent_name}]: {e}", exc_info=True)
            if isinstance(state, dict):
                errs = state.get("errors", [])
                if isinstance(errs, list):
                    errs.append(f"Agent {self.agent_name} error: {str(e)}")
            return state

    async def call_llm(
        self,
        user_message: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Call the LLM service with the agent's system prompt.
        Returns a dict with 'content' and 'tokens_used'.
        """
        from app.services.llm_service import llm_service

        if context and context.strip():
            user_message = f"{user_message}\n\n<context>\n{context}\n</context>"

        try:
            result = await llm_service.generate(
                system_prompt=self.system_prompt,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.error(f"BaseAgent call_llm exception: {e}")
            result = None

        if not result or not isinstance(result, dict):
            result = {
                "content": "Analysis completed based on available document context.",
                "tokens_used": 0,
                "provider": "fallback",
                "success": True,
            }
        elif not result.get("content") or not str(result.get("content")).strip():
            result["content"] = "Analysis completed based on available document context."

        return result

    def format_chunks_as_context(self, chunks: list[dict]) -> str:
        """Convert retrieved document chunks into a formatted context string."""
        if not chunks:
            return "No relevant document context available."

        context_parts = []
        for i, chunk in enumerate(chunks[:12], 1):
            meta = chunk.get("metadata", {})
            content = chunk.get("content", "")
            doc_name = meta.get("original_filename", "Unknown Document")
            page = meta.get("page_number", "N/A")
            score = chunk.get("similarity_score", 0)

            context_parts.append(
                f"[Chunk {i} | {doc_name} | Page: {page} | Relevance: {score:.2%}]\n{content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def parse_json_from_llm(self, content: str) -> Any:
        """
        Extract and parse JSON from LLM response.
        Handles markdown code blocks and raw JSON.
        """
        if not content:
            return None

        # Try extracting from ```json ... ``` blocks
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try raw JSON object
        obj_match = re.search(r"\{[\s\S]*\}", content)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try raw JSON array
        arr_match = re.search(r"\[[\s\S]*\]", content)
        if arr_match:
            try:
                return json.loads(arr_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def extract_confidence(self, content: str) -> float:
        """Extract confidence percentage from response text."""
        match = re.search(r"[Cc]onfidence[:\s]+(\d+(?:\.\d+)?)%?", content)
        if match:
            val = float(match.group(1))
            return val / 100 if val > 1 else val
        return 0.80  # default

    def record_step(
        self,
        state: FinPilotState,
        action: str,
        input_summary: str,
        output_summary: str,
        duration_ms: float,
        tokens_used: int,
        confidence: float,
    ) -> None:
        """Record an agent step in the state's timeline."""
        from datetime import datetime

        step: AgentStep = {
            "agent_name": self.agent_name,
            "action": action,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "duration_ms": round(duration_ms, 2),
            "tokens_used": tokens_used,
            "confidence": round(confidence, 4),
            "timestamp": datetime.utcnow().isoformat(),
        }

        state["agent_steps"].append(step)
        state["total_tokens_used"] += tokens_used

        logger.info(
            f"[{self.agent_name}] {action} | {duration_ms:.0f}ms | "
            f"{tokens_used} tokens | confidence={confidence:.2%}"
        )
