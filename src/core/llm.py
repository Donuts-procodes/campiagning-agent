from typing import Any

import google.generativeai as genai
import instructor
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from src.core.config import settings


def get_instructor_client() -> Any:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "anthropic":
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return instructor.from_anthropic(client)

    elif provider == "gemini":
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Using the standard gemini model client for instructor
        client = genai.GenerativeModel(model_name=settings.LLM_MODEL_NAME)
        return instructor.from_gemini(client)

    elif provider == "openai":
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return instructor.from_openai(client)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Must be 'openai', 'anthropic', or 'gemini'")


async def get_embedding(text: str) -> list[float]:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']

    # Default to OpenAI embeddings, even if Anthropic is selected (as Anthropic doesn't have native embeddings)
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
