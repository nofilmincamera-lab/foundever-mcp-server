"""
Style Guide Enrichment Package
===============================
Tools for enriching Foundever RFP style guides with Qdrant evidence.
"""

from .config import CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY, PROOF_TIERS
from .embedder import StyleGuideEmbedder, get_embedder
from .search import StyleGuideSearcher, SearchResult, get_searcher
from .enrichment_engine import (
    StyleGuideEnricher,
    StyleGuideEnrichment,
    TaxonomyEnrichment,
    EnrichedExample,
    get_enricher
)

__all__ = [
    "CLIENT_PERSONAS",
    "BUYER_DOMAIN_TAXONOMY",
    "PROOF_TIERS",
    "StyleGuideEmbedder",
    "get_embedder",
    "StyleGuideSearcher",
    "SearchResult",
    "get_searcher",
    "StyleGuideEnricher",
    "StyleGuideEnrichment",
    "TaxonomyEnrichment",
    "EnrichedExample",
    "get_enricher"
]
