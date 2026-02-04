"""
Style Guide Enrichment Engine
==============================
Main engine for enriching RFP style guides with Qdrant evidence.
Uses personas and variable-based templates.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import requests

from config import (
    CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY, PROOF_TIERS,
    OLLAMA_URL, LLM_MODEL
)
from search import StyleGuideSearcher, SearchResult, get_searcher


@dataclass
class EnrichedExample:
    """An enriched example with persona-based framing."""
    original_text: str
    enriched_text: str
    persona: str
    domain: str
    evidence_source: str
    proof_tier: str
    confidence: float


@dataclass
class TaxonomyEnrichment:
    """Taxonomy enrichment from evidence."""
    domain: str
    sub_function: str
    discovered_metrics: List[str]
    discovered_capabilities: List[str]
    example_claims: List[str]
    evidence_count: int


@dataclass
class StyleGuideEnrichment:
    """Complete enrichment package for a style guide section."""
    section_name: str
    timestamp: str
    persona_examples: Dict[str, List[EnrichedExample]]
    taxonomy_enrichments: List[TaxonomyEnrichment]
    foundever_specific: Dict[str, Any]
    metrics_discovered: List[str]
    templates_generated: List[str]
    raw_evidence: Dict[str, Any]


class StyleGuideEnricher:
    """
    Engine for enriching style guides with evidence from Qdrant.

    Features:
    - Persona-based example generation
    - Taxonomy enrichment from evidence
    - Foundever-specific pattern identification
    - LLM-powered refinement
    """

    def __init__(self, use_llm: bool = True):
        self.searcher = get_searcher()
        self.use_llm = use_llm

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama LLM for text generation."""
        if not self.use_llm:
            return ""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=120
            )
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            print(f"[Enricher] LLM error: {e}")
            return ""

    def _extract_metrics_from_text(self, text: str) -> List[str]:
        """Extract metrics from claim text."""
        metrics = []

        # Percentage patterns
        pct_pattern = r'(\d+(?:\.\d+)?)\s*%'
        for match in re.finditer(pct_pattern, text):
            context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
            metrics.append(f"{match.group(0)} - {context.strip()}")

        # Dollar patterns
        dollar_pattern = r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([MBK])?'
        for match in re.finditer(dollar_pattern, text, re.IGNORECASE):
            context = text[max(0, match.start()-20):min(len(text), match.end()+20)]
            metrics.append(f"{match.group(0)} - {context.strip()}")

        # Time patterns
        time_pattern = r'(\d+(?:\.\d+)?)\s*(days?|hours?|minutes?|seconds?|weeks?|months?)'
        for match in re.finditer(time_pattern, text, re.IGNORECASE):
            context = text[max(0, match.start()-20):min(len(text), match.end()+20)]
            metrics.append(f"{match.group(0)} - {context.strip()}")

        # Ratio patterns
        ratio_pattern = r'(\d+)\s*:\s*(\d+)'
        for match in re.finditer(ratio_pattern, text):
            context = text[max(0, match.start()-20):min(len(text), match.end()+20)]
            metrics.append(f"{match.group(0)} ratio - {context.strip()}")

        return metrics

    def _convert_to_persona_example(
        self,
        claim: SearchResult,
        target_persona: str
    ) -> EnrichedExample:
        """Convert a claim to a persona-based example."""
        persona = CLIENT_PERSONAS.get(target_persona, CLIENT_PERSONAS["retail_bank"])
        persona_name = persona["display_name"]

        # Replace any specific provider references with generic framing
        text = claim.text

        # Create enriched version with persona framing
        if claim.claim_type == "outcome_claim":
            enriched = f"For a {persona_name}: {text}"
        elif claim.claim_type == "capability_claim":
            enriched = f"Capability demonstrated for {persona_name} engagements: {text}"
        else:
            enriched = f"[{persona_name} context] {text}"

        return EnrichedExample(
            original_text=text,
            enriched_text=enriched,
            persona=target_persona,
            domain=claim.domain or "Unknown",
            evidence_source=claim.source_url or "internal",
            proof_tier=claim.proof_tier or "T0_marketing",
            confidence=claim.weighted_score
        )

    def _identify_foundever_patterns(
        self,
        claims: List[SearchResult]
    ) -> Dict[str, Any]:
        """Identify Foundever-specific patterns from claims."""
        patterns = {
            "voice_characteristics": [],
            "metric_formats": [],
            "value_propositions": [],
            "differentiators": [],
            "common_domains": {},
            "proof_distribution": {}
        }

        for claim in claims:
            # Track domains
            if claim.domain:
                patterns["common_domains"][claim.domain] = \
                    patterns["common_domains"].get(claim.domain, 0) + 1

            # Track proof tiers
            if claim.proof_tier:
                patterns["proof_distribution"][claim.proof_tier] = \
                    patterns["proof_distribution"].get(claim.proof_tier, 0) + 1

            # Extract specific metrics as value props
            metrics = self._extract_metrics_from_text(claim.text)
            if metrics and claim.proof_tier in ["T1_vendor_artifact", "T2_case_study"]:
                patterns["value_propositions"].append({
                    "claim": claim.text[:200],
                    "metrics": metrics,
                    "tier": claim.proof_tier
                })

            # Identify differentiators (high-tier outcomes)
            if claim.claim_type == "outcome_claim" and claim.proof_tier == "T2_case_study":
                patterns["differentiators"].append(claim.text[:200])

        return patterns

    def enrich_section(
        self,
        section_topic: str,
        target_personas: List[str] = None,
        include_taxonomy: bool = True,
        provider: str = "Foundever"
    ) -> StyleGuideEnrichment:
        """
        Enrich a style guide section with evidence.

        Args:
            section_topic: Topic/title of the section
            target_personas: List of persona keys to generate examples for
            include_taxonomy: Whether to enrich taxonomy
            provider: Provider to search for (default: Foundever)

        Returns:
            StyleGuideEnrichment with all enrichments
        """
        if target_personas is None:
            target_personas = ["paytech", "retail_bank", "card_issuer"]

        # Search for evidence
        print(f"[Enricher] Searching for: {section_topic}")
        search_results = self.searcher.search_for_style_guide_section(
            section_topic=section_topic,
            target_personas=target_personas,
            limit=15
        )

        # Get provider-specific evidence
        print(f"[Enricher] Getting {provider} evidence...")
        provider_evidence = self.searcher.get_provider_evidence(
            provider=provider,
            domains=[d for p in target_personas for d in CLIENT_PERSONAS.get(p, {}).get("domains", [])]
        )

        # Generate persona examples
        persona_examples = {}
        for persona_key in target_personas:
            persona_examples[persona_key] = []

            # Get claims relevant to this persona's domains
            persona = CLIENT_PERSONAS.get(persona_key, {})
            for domain in persona.get("domains", []):
                domain_claims = [
                    c for c in search_results.get("high_quality_claims", [])
                    if c.domain == domain
                ]
                for claim in domain_claims[:3]:
                    example = self._convert_to_persona_example(claim, persona_key)
                    persona_examples[persona_key].append(example)

        # Taxonomy enrichments
        taxonomy_enrichments = []
        if include_taxonomy:
            all_claims = (
                search_results.get("high_quality_claims", []) +
                search_results.get("case_study_evidence", []) +
                search_results.get("outcome_metrics", [])
            )

            # Group by domain
            by_domain = {}
            for claim in all_claims:
                if claim.domain and claim.domain not in ["REJECTED", "Unknown Buyer Domain"]:
                    if claim.domain not in by_domain:
                        by_domain[claim.domain] = []
                    by_domain[claim.domain].append(claim)

            for domain, claims in by_domain.items():
                # Extract metrics and capabilities
                all_metrics = []
                all_capabilities = []
                example_claims = []

                for claim in claims[:10]:
                    metrics = self._extract_metrics_from_text(claim.text)
                    all_metrics.extend(metrics)

                    if claim.claim_type == "capability_claim":
                        all_capabilities.append(claim.text[:150])

                    if len(example_claims) < 3:
                        example_claims.append(claim.text[:200])

                taxonomy_enrichments.append(TaxonomyEnrichment(
                    domain=domain,
                    sub_function=BUYER_DOMAIN_TAXONOMY.get(domain, {}).get("sub_functions", ["General"])[0],
                    discovered_metrics=list(set(all_metrics))[:10],
                    discovered_capabilities=all_capabilities[:5],
                    example_claims=example_claims,
                    evidence_count=len(claims)
                ))

        # Identify Foundever patterns
        all_evidence = (
            search_results.get("high_quality_claims", []) +
            search_results.get("case_study_evidence", [])
        )
        foundever_patterns = self._identify_foundever_patterns(all_evidence)

        # Extract all discovered metrics
        all_metrics = []
        for claim in all_evidence:
            all_metrics.extend(self._extract_metrics_from_text(claim.text))

        # Generate templates using LLM if enabled
        templates = []
        if self.use_llm and all_evidence:
            sample_claims = [c.text for c in all_evidence[:5]]
            prompt = f"""Based on these example claims about {section_topic}:
{chr(10).join(f'- {c}' for c in sample_claims)}

Generate 3 reusable template patterns in this format:
TEMPLATE: [template with {{placeholders}}]

Templates should be practitioner-voiced (specific, not marketing-speak).
Focus on templates that could work for any client persona."""

            llm_response = self._call_llm(prompt, max_tokens=400)
            if llm_response:
                for line in llm_response.split("\n"):
                    if line.strip().startswith("TEMPLATE:"):
                        templates.append(line.replace("TEMPLATE:", "").strip())

        return StyleGuideEnrichment(
            section_name=section_topic,
            timestamp=datetime.now().isoformat(),
            persona_examples=persona_examples,
            taxonomy_enrichments=taxonomy_enrichments,
            foundever_specific=foundever_patterns,
            metrics_discovered=list(set(all_metrics))[:20],
            templates_generated=templates,
            raw_evidence={
                "high_quality_count": len(search_results.get("high_quality_claims", [])),
                "case_study_count": len(search_results.get("case_study_evidence", [])),
                "outcome_count": len(search_results.get("outcome_metrics", [])),
                "provider_total_claims": provider_evidence.get("total_claims", 0)
            }
        )

    def generate_practitioner_examples(
        self,
        marketing_phrase: str,
        domain: str,
        persona: str = "retail_bank",
        count: int = 3
    ) -> List[Dict[str, str]]:
        """
        Convert marketing phrases to practitioner voice using evidence.

        Args:
            marketing_phrase: The marketing phrase to convert
            domain: Target buyer domain
            persona: Target persona key
            count: Number of alternatives to generate

        Returns:
            List of practitioner-voiced alternatives with evidence
        """
        # Search for relevant claims
        results = self.searcher.search_claims(
            query=marketing_phrase,
            limit=10,
            domain_filter=domain,
            proof_tier_filter=["T1_vendor_artifact", "T2_case_study"]
        )

        alternatives = []
        persona_info = CLIENT_PERSONAS.get(persona, CLIENT_PERSONAS["retail_bank"])

        for claim in results[:count]:
            # Extract metrics
            metrics = self._extract_metrics_from_text(claim.text)

            alternative = {
                "marketing_original": marketing_phrase,
                "practitioner_version": claim.text,
                "persona": persona_info["display_name"],
                "domain": domain,
                "metrics_used": metrics,
                "proof_tier": claim.proof_tier,
                "source": claim.source_url
            }

            # If LLM available, refine the practitioner version
            if self.use_llm:
                prompt = f"""Convert this marketing phrase to practitioner voice for a {persona_info['display_name']}:
Marketing: "{marketing_phrase}"
Evidence: "{claim.text}"

Write ONE sentence that sounds like someone who does the work, not sells it.
Use specific numbers from the evidence. No superlatives."""

                refined = self._call_llm(prompt, max_tokens=100)
                if refined:
                    alternative["refined_version"] = refined

            alternatives.append(alternative)

        return alternatives

    def enrich_taxonomy(
        self,
        provider: str = "Foundever"
    ) -> Dict[str, TaxonomyEnrichment]:
        """
        Enrich the entire buyer domain taxonomy with evidence.

        Args:
            provider: Provider to get evidence from

        Returns:
            Dict mapping domain -> TaxonomyEnrichment
        """
        enriched_taxonomy = {}

        for domain, domain_info in BUYER_DOMAIN_TAXONOMY.items():
            print(f"[Enricher] Enriching taxonomy: {domain}")

            # Search for domain-specific claims
            claims = self.searcher.search_claims(
                query=domain_info["description"],
                limit=30,
                domain_filter=domain
            )

            # Extract metrics
            all_metrics = []
            all_capabilities = []
            example_claims = []

            for claim in claims:
                metrics = self._extract_metrics_from_text(claim.text)
                all_metrics.extend(metrics)

                if claim.claim_type == "capability_claim":
                    all_capabilities.append(claim.text[:150])

                if claim.proof_tier in ["T1_vendor_artifact", "T2_case_study"]:
                    if len(example_claims) < 5:
                        example_claims.append(claim.text[:200])

            # Compare with existing metrics
            existing_metrics = domain_info.get("metrics", [])
            discovered_new = [m for m in all_metrics if not any(
                em.lower() in m.lower() for em in existing_metrics
            )]

            enriched_taxonomy[domain] = TaxonomyEnrichment(
                domain=domain,
                sub_function=domain_info["sub_functions"][0] if domain_info.get("sub_functions") else "General",
                discovered_metrics=list(set(discovered_new))[:15],
                discovered_capabilities=list(set(all_capabilities))[:10],
                example_claims=example_claims,
                evidence_count=len(claims)
            )

        return enriched_taxonomy


def get_enricher(use_llm: bool = True) -> StyleGuideEnricher:
    """Get enricher instance."""
    return StyleGuideEnricher(use_llm=use_llm)


if __name__ == "__main__":
    # Test the enricher
    enricher = get_enricher(use_llm=False)  # Disable LLM for faster testing

    print("\n" + "="*70)
    print("Testing Section Enrichment: Collections & Revenue Recovery")
    print("="*70)

    enrichment = enricher.enrich_section(
        section_topic="collections debt recovery right party contact",
        target_personas=["card_issuer", "retail_bank"],
        include_taxonomy=True
    )

    print(f"\nSection: {enrichment.section_name}")
    print(f"Timestamp: {enrichment.timestamp}")
    print(f"\nRaw Evidence Stats:")
    for k, v in enrichment.raw_evidence.items():
        print(f"  {k}: {v}")

    print(f"\nDiscovered Metrics ({len(enrichment.metrics_discovered)}):")
    for m in enrichment.metrics_discovered[:5]:
        print(f"  - {m}")

    print(f"\nFoundever Patterns - Domain Distribution:")
    for domain, count in enrichment.foundever_specific.get("common_domains", {}).items():
        print(f"  {domain}: {count}")

    print(f"\nPersona Examples:")
    for persona, examples in enrichment.persona_examples.items():
        print(f"\n  --- {CLIENT_PERSONAS[persona]['display_name']} ---")
        for ex in examples[:2]:
            print(f"    [{ex.proof_tier}] {ex.enriched_text[:80]}...")

    print("\n" + "="*70)
    print("Testing Practitioner Voice Conversion")
    print("="*70)

    alternatives = enricher.generate_practitioner_examples(
        marketing_phrase="world-class collections capabilities",
        domain="Collections & Revenue Recovery",
        persona="card_issuer",
        count=3
    )

    for alt in alternatives:
        print(f"\nMarketing: {alt['marketing_original']}")
        print(f"Practitioner: {alt['practitioner_version'][:100]}...")
        print(f"Metrics: {alt['metrics_used'][:2] if alt['metrics_used'] else 'None found'}")
