"""
FinPilot AI — Report Generation Celery Tasks
"""

import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.report_tasks.generate_report_task",
    queue="reports",
    max_retries=2,
    soft_time_limit=600,
)
def generate_report_task(
    self,
    session_id: str,
    user_id: str,
    report_type: str,
    document_ids: list,
    report_config: dict,
):
    """
    Background task: generate a full AI report via the multi-agent pipeline.
    Saves the report to the database on completion.
    """
    logger.info(f"Generating {report_type} report for user {user_id}")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _generate():
            from app.graph.workflow import run_finpilot_pipeline
            from app.graph.state import create_initial_state
            from app.core.database import AsyncSessionFactory
            from app.models.report import Report
            import uuid

            # Build query based on report type
            query_map = {
                "financial": "Generate a comprehensive financial performance report with ratio analysis",
                "risk": "Generate a complete risk assessment report with mitigation strategies",
                "compliance": "Generate a regulatory compliance report covering IFRS, SOX, Basel III",
                "fraud": "Generate a forensic fraud investigation report",
                "investment": "Generate an investment analysis report with DCF valuation",
                "forecast": "Generate a financial forecast report with scenario analysis",
            }
            query = query_map.get(report_type, "Generate a comprehensive financial report")

            initial_state = create_initial_state(
                user_query=query,
                user_id=user_id,
                session_id=session_id,
                active_document_ids=document_ids,
                workflow_type="report",
            )

            final_state = await run_finpilot_pipeline(initial_state, thread_id=session_id)

            async with AsyncSessionFactory() as db:
                report = Report(
                    id=uuid.uuid4(),
                    title=f"{report_type.title()} Report — {query[:50]}",
                    report_type=report_type,
                    content=final_state.get("final_response", ""),
                    financial_analysis=final_state.get("financial_analysis"),
                    charts=final_state.get("charts", []),
                    tables=final_state.get("tables", []),
                    citations=final_state.get("citations", []),
                    confidence_score=final_state.get("confidence_score", 0),
                    agents_used=final_state.get("required_agents", []),
                    tokens_used=final_state.get("total_tokens_used", 0),
                    cost_usd=final_state.get("total_cost_usd", 0),
                    session_id=uuid.UUID(session_id),
                    user_id=uuid.UUID(user_id),
                )
                db.add(report)
                await db.commit()

            return {"status": "completed", "report_id": str(report.id)}

        result = loop.run_until_complete(_generate())
        loop.close()
        return result

    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        self.retry(exc=exc, countdown=120)
