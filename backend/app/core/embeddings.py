"""Embeddings client for generating vector embeddings from text.

Abstract interface for embeddings generation so providers can be swapped easily
(OpenAI, Anthropic, local model, etc.). Currently implements OpenAI only.
"""
from abc import ABC, abstractmethod

from openai import OpenAI

from app.core.config import get_settings


class EmbeddingsClient(ABC):
    """Abstract base class for embeddings generation."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple text strings.

        Args:
            texts: List of texts to embed.

        Returns:
            A list of embedding vectors (each is a list of floats).
        """
        pass


class OpenAIEmbeddings(EmbeddingsClient):
    """OpenAI embeddings client using text-embedding-3-small."""

    MODEL = "text-embedding-3-small"  # 1536 dimensions

    def __init__(self, api_key: str):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key.
        """
        self.client = OpenAI(api_key=api_key)

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        response = self.client.embeddings.create(input=text, model=self.MODEL)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple text strings."""
        if not texts:
            return []
        response = self.client.embeddings.create(input=texts, model=self.MODEL)
        # Sort by index to maintain order (API may return out of order)
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]


def get_embeddings_client() -> EmbeddingsClient:
    """Factory function to create embeddings client from config.

    Returns:
        Configured EmbeddingsClient instance (currently OpenAI).
    """
    settings = get_settings()
    return OpenAIEmbeddings(api_key=settings.openai_api_key)
