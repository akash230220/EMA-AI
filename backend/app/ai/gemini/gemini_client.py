# backend/app/ai/gemini/gemini_client.py
"""
Google Gemini 2.x Client.

Direct async HTTP interface for Google Gemini Models (e.g. gemini-2.0-flash, text-embedding-004).
Endpoints: https://generativelanguage.googleapis.com/v1beta/models/...

Responsibilities:
  - Text generation (raw text, summarization, replies)
  - Structured JSON extraction (categorization, intent, sentiment, priority, tasks, meetings)
  - Multi-turn conversational chat (non-streaming + SSE token streaming)
  - Text embedding generation for ChromaDB RAG storage & vector search
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger("ai_email_os.gemini_client")
settings = get_settings()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
T = TypeVar("T", bound=BaseModel)


def _clean_json_markdown(text: str) -> str:
    """Strips ```json ... ``` markdown code block wrappers from LLM output."""
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return cleaned


class GeminiClient:
    """Asynchronous client for Google Gemini 2.x API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.temperature = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
        self.max_output_tokens = max_output_tokens or settings.GEMINI_MAX_OUTPUT_TOKENS

    def _get_url(self, action: str = "generateContent", model_override: Optional[str] = None) -> str:
        target_model = model_override or self.model
        return f"{GEMINI_BASE_URL}/{target_model}:{action}?key={self.api_key}"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generates standard text completion for a given prompt and optional system prompt.
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            logger.warning("GEMINI_API_KEY not configured. Returning fallback response.")
            return "Gemini response preview (API key not configured)."

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "maxOutputTokens": max_tokens or self.max_output_tokens,
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        url = self._get_url("generateContent")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            logger.error("Gemini generate_text failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Gemini API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected Gemini response structure: %s", data)
            raise ValueError(f"Failed to parse Gemini output: {exc}") from exc

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: Optional[float] = 0.1,
    ) -> dict[str, Any]:
        """
        Generates structured JSON output, optionally enforcing schema via prompt guidance
        or responseMimeType="application/json".
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            logger.warning("GEMINI_API_KEY not configured. Returning fallback mock dict.")
            return {}

        augmented_system = (system_prompt or "") + "\nOutput valid JSON only. Do not include markdown or explanations."

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
            "systemInstruction": {"parts": [{"text": augmented_system}]},
        }

        url = self._get_url("generateContent")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            logger.error("Gemini generate_json failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Gemini API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = _clean_json_markdown(raw_text)
            parsed = json.loads(cleaned)

            if schema and issubclass(schema, BaseModel):
                validated = schema.model_validate(parsed)
                return validated.model_dump()
            return parsed
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.error("Failed to parse JSON from Gemini response: %s", data)
            raise ValueError(f"Failed to parse structured JSON from Gemini: {exc}") from exc

    async def chat(
        self,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Multi-turn chat interaction.
        `history` contains list of {"role": "user"|"assistant"|"model", "content": str}.
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            return "Copilot response (Gemini API key is not configured)."

        contents = []
        for msg in history:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }

        url = self._get_url("generateContent")

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            logger.error("Gemini chat failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Gemini chat failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected Gemini chat response: %s", data)
            raise ValueError(f"Failed to parse Gemini chat response: {exc}") from exc

    async def stream_chat(
        self,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """
        Streams multi-turn chat tokens in real-time.
        Yields text chunks as they arrive from Gemini's streamGenerateContent endpoint.
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            for chunk in ["Copilot ", "streaming ", "preview ", "(Gemini ", "API key ", "not set)."]:
                yield chunk
            return

        contents = []
        for msg in history:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }

        url = self._get_url("streamGenerateContent") + "&alt=sse"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error("Gemini stream failed (%s): %s", response.status_code, error_text.decode("utf-8"))
                    yield "Sorry, I encountered an error communicating with Gemini."
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    json_str = line[6:].strip()
                    if not json_str or json_str == "[DONE]":
                        continue
                    try:
                        chunk_data = json.loads(json_str)
                        text_part = (
                            chunk_data.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if text_part:
                            yield text_part
                    except Exception:
                        continue

    async def embed_content(
        self,
        text: str,
        model: str = "text-embedding-004",
    ) -> list[float]:
        """
        Generates a 768-dimensional vector embedding for text using Google's text-embedding-004.
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            # Return dummy 768-dim vector for testing/mocking
            return [0.0] * 768

        payload = {
            "model": f"models/{model}",
            "content": {"parts": [{"text": text}]},
        }

        url = f"{GEMINI_BASE_URL}/{model}:embedContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            logger.error("Gemini embedContent failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Gemini embedding failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        return data.get("embedding", {}).get("values", [])

    async def batch_embed_contents(
        self,
        texts: list[str],
        model: str = "text-embedding-004",
    ) -> list[list[float]]:
        """
        Generates embeddings for multiple texts in a single batch request.
        """
        if not self.api_key or self.api_key.startswith("CHANGE_ME"):
            return [[0.0] * 768 for _ in texts]

        requests = [
            {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        payload = {"requests": requests}

        url = f"{GEMINI_BASE_URL}/{model}:batchEmbedContents?key={self.api_key}"

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code != 200:
            logger.error("Gemini batchEmbedContents failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Gemini batch embedding failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        embeddings = [emb.get("values", []) for emb in data.get("embeddings", [])]
        return embeddings


# ---------------------------------------------------------------------------
# Global Singleton & Helper Functions
# ---------------------------------------------------------------------------

_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Cached singleton instance of GeminiClient."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def generate_text_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Convenience helper to generate text."""
    client = get_gemini_client()
    return await client.generate_text(prompt, system_prompt)


async def generate_json_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    schema: Optional[Type[T]] = None,
) -> dict[str, Any]:
    """Convenience helper to generate JSON."""
    client = get_gemini_client()
    return await client.generate_json(prompt, system_prompt, schema=schema)


async def generate_embedding(text: str) -> list[float]:
    """Convenience helper to embed a single string."""
    client = get_gemini_client()
    return await client.embed_content(text)


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Convenience helper to embed a batch of strings."""
    client = get_gemini_client()
    return await client.batch_embed_contents(texts)

