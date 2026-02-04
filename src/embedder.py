"""
Embedding Utility for Style Guide Enrichment
=============================================
Provides embedding generation using intfloat/e5-mistral-7b-instruct
"""

import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Optional
import numpy as np

from config import EMBEDDING_MODEL, EMBEDDING_DIM


class StyleGuideEmbedder:
    """Singleton embedder for consistent embedding generation."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if StyleGuideEmbedder._initialized:
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Embedder] Initializing on {self.device}")

        print(f"[Embedder] Loading model: {EMBEDDING_MODEL}")
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.model = AutoModel.from_pretrained(
            EMBEDDING_MODEL,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            device_map="auto" if self.device.type == "cuda" else None
        )
        self.model.eval()
        print(f"[Embedder] Model loaded. Embedding dim: {EMBEDDING_DIM}")

        StyleGuideEmbedder._initialized = True

    @torch.no_grad()
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed_batch([text])[0]

    @torch.no_grad()
    def embed_batch(self, texts: List[str], prefix: str = "query: ") -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            prefix: Prefix for e5-mistral format (default: "query: ")

        Returns:
            List of embedding vectors
        """
        # Add instruction prefix for e5-mistral
        prefixed_texts = [f"{prefix}{t}" for t in texts]

        inputs = self.tokenizer(
            prefixed_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        if self.device.type == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        outputs = self.model(**inputs)

        # Mean pooling
        attention_mask = inputs["attention_mask"]
        token_embeddings = outputs.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * mask_expanded, dim=1)
        sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-9)
        embeddings = sum_embeddings / sum_mask
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy().tolist()

    def embed_for_style_guide(
        self,
        query: str,
        context: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding optimized for style guide enrichment.

        Args:
            query: The main search query
            context: Optional context (e.g., section being enriched)
            domain: Optional buyer domain for targeting

        Returns:
            Embedding vector
        """
        # Construct enriched query
        parts = [query]
        if domain:
            parts.append(f"Domain: {domain}")
        if context:
            parts.append(f"Context: {context}")

        enriched_query = " | ".join(parts)
        return self.embed(enriched_query)


def get_embedder() -> StyleGuideEmbedder:
    """Get singleton embedder instance."""
    return StyleGuideEmbedder()


if __name__ == "__main__":
    # Test the embedder
    embedder = get_embedder()

    test_queries = [
        "collections debt recovery outsourcing",
        "fraud prevention financial services",
        "customer experience contact center"
    ]

    print("\nTesting embeddings:")
    for query in test_queries:
        emb = embedder.embed(query)
        print(f"  '{query[:40]}...' -> dim={len(emb)}, norm={np.linalg.norm(emb):.4f}")
