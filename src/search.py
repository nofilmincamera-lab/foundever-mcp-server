"""
Qdrant Search Functions for Style Guide Enrichment
===================================================
Semantic search across claims and chunks collections.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText, Range

from config import (
    QDRANT_HOST, QDRANT_PORT,
    CLAIMS_COLLECTION, CHUNKS_COLLECTION,
    PROOF_TIERS, CONTENT_TYPE_PRIORITY,
    DEFAULT_SEARCH_LIMIT, MIN_SIMILARITY_SCORE,
    CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY
)
from embedder import get_embedder


@dataclass
class SearchResult:
    """Unified search result from claims or chunks."""
    id: str
    score: float
    source: str  # 'claims' or 'chunks'
    text: str
    provider: str
    proof_tier: Optional[str] = None
    content_type: Optional[str] = None
    domain: Optional[str] = None
    claim_type: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        """Calculate weighted score based on proof tier or content type."""
        if self.proof_tier and self.proof_tier in PROOF_TIERS:
            return self.score * PROOF_TIERS[self.proof_tier]["weight"]
        if self.content_type and self.content_type in CONTENT_TYPE_PRIORITY:
            return self.score * CONTENT_TYPE_PRIORITY[self.content_type]
        return self.score * 0.5


class StyleGuideSearcher:
    """Semantic search engine for style guide enrichment."""

    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=60)
        self.embedder = get_embedder()
        print(f"[Searcher] Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")

    def search_claims(
        self,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        provider_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        proof_tier_filter: Optional[List[str]] = None,
        claim_type_filter: Optional[str] = None,
        min_score: float = MIN_SIMILARITY_SCORE
    ) -> List[SearchResult]:
        """
        Search the claims collection.

        Args:
            query: Search query
            limit: Max results to return
            provider_filter: Filter by provider name
            domain_filter: Filter by buyer domain
            proof_tier_filter: Filter by proof tiers (list)
            claim_type_filter: Filter by claim type
            min_score: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        # Generate embedding
        query_vector = self.embedder.embed(query)

        # Build filter
        filter_conditions = []

        if provider_filter:
            filter_conditions.append(
                FieldCondition(key="provider_name", match=MatchValue(value=provider_filter))
            )

        if domain_filter:
            filter_conditions.append(
                FieldCondition(key="domain", match=MatchValue(value=domain_filter))
            )

        if proof_tier_filter:
            # Use should for multiple tiers
            tier_conditions = [
                FieldCondition(key="proof_tier", match=MatchValue(value=tier))
                for tier in proof_tier_filter
            ]
            # For simplicity, just use first tier if multiple
            if len(tier_conditions) == 1:
                filter_conditions.append(tier_conditions[0])

        if claim_type_filter:
            filter_conditions.append(
                FieldCondition(key="claim_type", match=MatchValue(value=claim_type_filter))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Execute search using query_points (newer API)
        results = self.client.query_points(
            collection_name=CLAIMS_COLLECTION,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            score_threshold=min_score
        )

        # Convert to SearchResult
        search_results = []
        for r in results.points:
            payload = r.payload or {}
            search_results.append(SearchResult(
                id=str(r.id),
                score=r.score,
                source="claims",
                text=payload.get("claim_text", ""),
                provider=payload.get("provider_name", "Unknown"),
                proof_tier=payload.get("proof_tier"),
                domain=payload.get("domain"),
                claim_type=payload.get("claim_type"),
                source_url=payload.get("source_url"),
                metadata={
                    "record_id": payload.get("record_id"),
                    "capability": payload.get("capability"),
                    "is_outcome": payload.get("is_outcome", False),
                    "products": payload.get("products", [])
                }
            ))

        return search_results

    def search_chunks(
        self,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        provider_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        min_score: float = MIN_SIMILARITY_SCORE
    ) -> List[SearchResult]:
        """
        Search the unified_chunks collection.

        Args:
            query: Search query
            limit: Max results to return
            provider_filter: Filter by provider name
            content_type_filter: Filter by content type
            min_score: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        # Generate embedding - chunks use 2048 dim, need different model
        # For now, use the same embedder but note this may need adjustment
        query_vector = self.embedder.embed(query)

        # Build filter
        filter_conditions = []

        if provider_filter:
            filter_conditions.append(
                FieldCondition(key="provider_name", match=MatchValue(value=provider_filter))
            )

        if content_type_filter:
            filter_conditions.append(
                FieldCondition(key="content_type", match=MatchValue(value=content_type_filter))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Note: unified_chunks uses 2048-dim vectors, claims uses 4096
        # This search may not work optimally - need to check embedding model used for chunks
        try:
            results = self.client.query_points(
                collection_name=CHUNKS_COLLECTION,
                query=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=min_score
            )
        except Exception as e:
            print(f"[Searcher] Chunk search error (dim mismatch?): {e}")
            # Fall back to scroll with filter
            return self._fallback_chunk_search(provider_filter, content_type_filter, limit)

        # Convert to SearchResult
        search_results = []
        for r in results.points:
            payload = r.payload or {}
            search_results.append(SearchResult(
                id=str(r.id),
                score=r.score,
                source="chunks",
                text=payload.get("text_preview", ""),
                provider=payload.get("provider_name", "Unknown"),
                content_type=payload.get("content_type"),
                source_url=payload.get("source_url"),
                metadata={
                    "source_type": payload.get("source_type"),
                    "source_id": payload.get("source_id"),
                    "domain": payload.get("domain"),
                    "title": payload.get("title"),
                    "section_header": payload.get("section_header"),
                    "has_numbers": payload.get("has_numbers", False),
                    "has_quotes": payload.get("has_quotes", False)
                }
            ))

        return search_results

    def _fallback_chunk_search(
        self,
        provider_filter: Optional[str],
        content_type_filter: Optional[str],
        limit: int
    ) -> List[SearchResult]:
        """Fallback to scroll-based search when vector search fails."""
        filter_conditions = []

        if provider_filter:
            filter_conditions.append(
                FieldCondition(key="provider_name", match=MatchValue(value=provider_filter))
            )

        if content_type_filter:
            filter_conditions.append(
                FieldCondition(key="content_type", match=MatchValue(value=content_type_filter))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        results, _ = self.client.scroll(
            collection_name=CHUNKS_COLLECTION,
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        search_results = []
        for r in results:
            payload = r.payload or {}
            search_results.append(SearchResult(
                id=str(r.id),
                score=0.5,  # Default score for non-vector search
                source="chunks",
                text=payload.get("text_preview", ""),
                provider=payload.get("provider_name", "Unknown"),
                content_type=payload.get("content_type"),
                source_url=payload.get("source_url"),
                metadata={
                    "source_type": payload.get("source_type"),
                    "source_id": payload.get("source_id"),
                    "domain": payload.get("domain"),
                    "title": payload.get("title")
                }
            ))

        return search_results

    def search_for_persona(
        self,
        persona_key: str,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> Dict[str, List[SearchResult]]:
        """
        Search tailored to a specific client persona.

        Args:
            persona_key: Key from CLIENT_PERSONAS
            query: Search query
            limit: Max results per domain

        Returns:
            Dict mapping domain -> list of results
        """
        if persona_key not in CLIENT_PERSONAS:
            raise ValueError(f"Unknown persona: {persona_key}")

        persona = CLIENT_PERSONAS[persona_key]
        results_by_domain = {}

        # Search each domain relevant to this persona
        for domain in persona["domains"]:
            # Enrich query with persona keywords
            enriched_query = f"{query} {' '.join(persona['keywords'][:3])}"

            domain_results = self.search_claims(
                query=enriched_query,
                limit=limit,
                domain_filter=domain
            )

            results_by_domain[domain] = domain_results

        return results_by_domain

    def search_for_style_guide_section(
        self,
        section_topic: str,
        target_personas: Optional[List[str]] = None,
        include_outcomes: bool = True,
        include_capabilities: bool = True,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> Dict[str, Any]:
        """
        Comprehensive search for enriching a style guide section.

        Args:
            section_topic: Topic of the section being enriched
            target_personas: List of persona keys to target
            include_outcomes: Include outcome claims
            include_capabilities: Include capability claims
            limit: Max results per category

        Returns:
            Dict with categorized results
        """
        results = {
            "topic": section_topic,
            "high_quality_claims": [],
            "case_study_evidence": [],
            "outcome_metrics": [],
            "capability_statements": [],
            "by_persona": {}
        }

        # High-quality claims (T1+)
        t1_results = self.search_claims(
            query=section_topic,
            limit=limit,
            proof_tier_filter=["T1_vendor_artifact"]
        )
        results["high_quality_claims"] = t1_results

        # Case study evidence
        t2_results = self.search_claims(
            query=section_topic,
            limit=limit,
            proof_tier_filter=["T2_case_study"]
        )
        results["case_study_evidence"] = t2_results

        # Outcomes
        if include_outcomes:
            outcome_results = self.search_claims(
                query=section_topic,
                limit=limit,
                claim_type_filter="outcome_claim"
            )
            results["outcome_metrics"] = outcome_results

        # Capabilities
        if include_capabilities:
            capability_results = self.search_claims(
                query=section_topic,
                limit=limit,
                claim_type_filter="capability_claim"
            )
            results["capability_statements"] = capability_results

        # Per-persona results
        if target_personas:
            for persona_key in target_personas:
                if persona_key in CLIENT_PERSONAS:
                    results["by_persona"][persona_key] = self.search_for_persona(
                        persona_key, section_topic, limit=limit // 2
                    )

        return results

    def get_provider_evidence(
        self,
        provider: str,
        domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get all evidence for a specific provider.

        Args:
            provider: Provider name (e.g., "Foundever")
            domains: Optional list of buyer domains to filter

        Returns:
            Comprehensive evidence package
        """
        evidence = {
            "provider": provider,
            "total_claims": 0,
            "by_proof_tier": {},
            "by_domain": {},
            "by_claim_type": {},
            "top_outcomes": [],
            "case_studies": []
        }

        # Get all claims for provider
        all_claims = []
        offset = None

        while True:
            filter_cond = [
                FieldCondition(key="provider_name", match=MatchValue(value=provider))
            ]

            results, next_offset = self.client.scroll(
                collection_name=CLAIMS_COLLECTION,
                scroll_filter=Filter(must=filter_cond),
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            all_claims.extend(results)
            offset = next_offset

            if not offset or len(results) == 0:
                break

            if len(all_claims) >= 5000:  # Safety limit
                break

        evidence["total_claims"] = len(all_claims)

        # Categorize
        for claim in all_claims:
            payload = claim.payload or {}

            # By proof tier
            tier = payload.get("proof_tier", "unknown")
            evidence["by_proof_tier"][tier] = evidence["by_proof_tier"].get(tier, 0) + 1

            # By domain
            domain = payload.get("domain", "unknown")
            if domains is None or domain in domains:
                if domain not in evidence["by_domain"]:
                    evidence["by_domain"][domain] = []
                if len(evidence["by_domain"][domain]) < 10:  # Keep top 10 per domain
                    evidence["by_domain"][domain].append({
                        "text": payload.get("claim_text", ""),
                        "proof_tier": tier,
                        "claim_type": payload.get("claim_type"),
                        "source_url": payload.get("source_url")
                    })

            # By claim type
            ctype = payload.get("claim_type", "unknown")
            evidence["by_claim_type"][ctype] = evidence["by_claim_type"].get(ctype, 0) + 1

            # Top outcomes
            if ctype == "outcome_claim" and tier in ["T1_vendor_artifact", "T2_case_study"]:
                if len(evidence["top_outcomes"]) < 20:
                    evidence["top_outcomes"].append({
                        "text": payload.get("claim_text", ""),
                        "proof_tier": tier,
                        "domain": domain,
                        "source_url": payload.get("source_url")
                    })

        # Get case studies from chunks
        case_study_chunks = self._fallback_chunk_search(
            provider_filter=provider,
            content_type_filter="case_study",
            limit=20
        )
        evidence["case_studies"] = [
            {
                "text": r.text,
                "source_url": r.source_url
            }
            for r in case_study_chunks
        ]

        return evidence


def get_searcher() -> StyleGuideSearcher:
    """Get searcher instance."""
    return StyleGuideSearcher()


if __name__ == "__main__":
    # Test the searcher
    searcher = get_searcher()

    print("\n" + "="*60)
    print("Testing Claims Search")
    print("="*60)

    results = searcher.search_claims(
        query="collections debt recovery performance metrics",
        limit=5,
        domain_filter="Collections & Revenue Recovery"
    )

    for r in results:
        print(f"\n[{r.proof_tier}] Score: {r.score:.3f}")
        print(f"  Provider: {r.provider}")
        print(f"  Text: {r.text[:100]}...")

    print("\n" + "="*60)
    print("Testing Persona Search")
    print("="*60)

    persona_results = searcher.search_for_persona(
        persona_key="card_issuer",
        query="fraud prevention dispute resolution",
        limit=3
    )

    for domain, results in persona_results.items():
        print(f"\n--- {domain} ---")
        for r in results[:2]:
            print(f"  [{r.proof_tier}] {r.text[:80]}...")
