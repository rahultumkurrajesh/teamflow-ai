"""LLM client for RAG question-answering.

Abstract interface for LLM providers so implementations can be swapped easily
(OpenAI, Anthropic, local models, etc.). Currently implements OpenAI only.
"""
from abc import ABC, abstractmethod

from openai import OpenAI

from app.core.config import get_settings

# System prompt instructs the model to ground answers in the provided context
GROUNDING_PROMPT = """You are a helpful assistant answering questions based ONLY on the provided context.

IMPORTANT RULES:
1. Answer only using information from the provided context chunks.
2. If the answer is not in the context, say: "I don't have enough information in the documents to answer this question."
3. Be concise and accurate.
4. If relevant, cite which chunk(s) the information came from."""


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def answer_question(self, question: str, context_chunks: list[str]) -> str:
        """Answer a question based on provided context chunks.

        Args:
            question: The user's question.
            context_chunks: List of relevant document chunks to use as context.

        Returns:
            The model's answer grounded in the provided context.
        """
        pass


class OpenAILLM(LLMClient):
    """OpenAI LLM client using gpt-4o-mini."""

    MODEL = "gpt-4o-mini"  # Cost-effective, fast, high quality

    def __init__(self, api_key: str):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key.
        """
        self.client = OpenAI(api_key=api_key)

    def answer_question(self, question: str, context_chunks: list[str]) -> str:
        """Answer a question using provided context chunks."""
        # Format context for the model
        context_text = "\n\n---\n\n".join(
            [f"[Chunk {i}]\n{chunk}" for i, chunk in enumerate(context_chunks)]
        )

        # Build the prompt
        user_message = f"""Context:
{context_text}

Question: {question}

Provide a clear, concise answer based only on the context above. If the answer is not in the context, say so."""

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": GROUNDING_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content or ""


class NoOpLLM(LLMClient):
    """No-op LLM client when no API key is configured.

    Returns a note that LLM answer generation is disabled.
    """

    def answer_question(self, question: str, context_chunks: list[str]) -> str:
        """Return a note that LLM is disabled."""
        chunk_count = len(context_chunks)
        chunk_preview = context_chunks[0][:100] if context_chunks else "N/A"
        return (
            f"[LLM answer generation disabled - no OPENAI_API_KEY configured]\n\n"
            f"Retrieved {chunk_count} relevant chunk(s) for your question.\n"
            f"First chunk preview: {chunk_preview}..."
        )


def get_llm_client() -> LLMClient:
    """Factory function to create LLM client from config.

    If OPENAI_API_KEY is set, uses OpenAI. Otherwise, returns a no-op client
    that informs the user LLM is disabled but chunks are still retrieved.

    Returns:
        Configured LLMClient instance (OpenAI or no-op).
    """
    settings = get_settings()
    if settings.openai_api_key:
        return OpenAILLM(api_key=settings.openai_api_key)
    else:
        return NoOpLLM()
