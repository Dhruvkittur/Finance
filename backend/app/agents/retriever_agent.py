"""
FinPilot AI — Retriever Agent
================================
Retrieves relevant document chunks from ChromaDB using
semantic search, hybrid search, and multi-query strategies.
Generates citations for all retrieved content.
"""

import time
from app.agents.base_agent import BaseAgent
from app.graph.state import Citation, FinPilotState
from app.services.vector_service import VectorService


class RetrieverAgent(BaseAgent):
    """
    Retrieves the most relevant document chunks for the user's query.
    Supports semantic search, hybrid search, and query expansion.
    """

    def __init__(self):
        self.vector_service = VectorService()

    @property
    def agent_name(self) -> str:
        return "RetrieverAgent"

    @property
    def system_prompt(self) -> str:
        return """You are the Retriever Agent of FinPilot AI.
Your role is to evaluate retrieved document chunks for relevance
and generate query variations to maximize retrieval coverage.
Always prioritize precision over recall for financial queries."""

    async def execute(self, state: FinPilotState) -> FinPilotState:
        """Retrieve relevant document chunks using hybrid search."""
        start_time = time.perf_counter()
        query = state["sanitized_query"]

        # Initialize vector service collections
        await self.vector_service.initialize_collections()

        # Perform hybrid search (semantic + keyword expansion)
        chunks = await self.vector_service.hybrid_search(
            query=query,
            n_results=4,
            document_ids=state["active_document_ids"] if state["active_document_ids"] else None,
        )

        # Build citations from retrieved chunks
        citations: list[Citation] = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            citation: Citation = {
                "document_id": meta.get("document_id", "unknown"),
                "document_name": meta.get("original_filename", "Unknown Document"),
                "chunk_content": chunk.get("content", "")[:500],
                "page_number": meta.get("page_number"),
                "similarity_score": chunk.get("similarity_score", 0),
                "chunk_index": meta.get("chunk_index", 0),
            }
            citations.append(citation)

        duration_ms = (time.perf_counter() - start_time) * 1000

        state["retrieved_chunks"] = chunks
        state["citations"] = citations

        self.record_step(
            state,
            action="hybrid_retrieval",
            input_summary=f"Query: {query[:100]}",
            output_summary=f"Retrieved {len(chunks)} relevant chunks from {len(set(c['document_id'] for c in citations))} documents",
            duration_ms=duration_ms,
            tokens_used=0,
            confidence=min(chunks[0]["similarity_score"] if chunks else 0, 1.0),
        )

        return state
