"""LangGraph email pipeline package."""

from app.ai.graph.email_pipeline import (
    PIPELINE_VERSION,
    build_email_graph,
    run_email_pipeline,
)
from app.ai.graph.pipeline_state import EmailProcessingState

__all__ = [
    "EmailProcessingState",
    "build_email_graph",
    "run_email_pipeline",
    "PIPELINE_VERSION",
]

