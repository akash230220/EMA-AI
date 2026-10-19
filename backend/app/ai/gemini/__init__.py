"""Google Gemini AI integration package."""

from app.ai.gemini.gemini_client import (
    GeminiClient,
    generate_embedding,
    generate_embeddings,
    generate_json_response,
    generate_text_response,
    get_gemini_client,
)

__all__ = [
    "GeminiClient",
    "get_gemini_client",
    "generate_text_response",
    "generate_json_response",
    "generate_embedding",
    "generate_embeddings",
]

