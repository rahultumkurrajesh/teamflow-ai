"""Text chunking for embedding generation with overlap."""
import tiktoken

# Tokenizer for counting tokens (gpt-3.5-turbo or gpt-4)
_ENCODING = tiktoken.get_encoding("cl100k_base")


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks based on token count.

    Uses tiktoken to count tokens, so chunk sizes match the token count for
    embedding models like OpenAI's text-embedding-3-small.

    Args:
        text: The text to chunk.
        chunk_size: Target number of tokens per chunk (default 500).
        overlap: Number of tokens to overlap between chunks (default 50).

    Returns:
        List of text chunks.
    """
    # Tokenize the entire text
    tokens = _ENCODING.encode(text)

    if len(tokens) <= chunk_size:
        # If text is smaller than chunk size, return as single chunk
        return [text]

    chunks = []
    start_idx = 0

    while start_idx < len(tokens):
        # End index for this chunk
        end_idx = min(start_idx + chunk_size, len(tokens))

        # Decode tokens back to text
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = _ENCODING.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move start for next chunk, accounting for overlap
        start_idx = end_idx - overlap

        # If we're at the end, don't create tiny overlapping chunks
        if end_idx >= len(tokens):
            break

    return chunks
