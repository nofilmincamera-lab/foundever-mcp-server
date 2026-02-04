#!/usr/bin/env python3
"""
Style Guide Enrichment - Main Script
=====================================
Enriches Foundever RFP Style Guide with evidence from Qdrant.
Uses personas instead of specific client names.

Usage:
    python main.py --section "collections"
    python main.py --taxonomy
    python main.py --foundever-analysis
    python main.py --convert "world-class fraud prevention"
"""

import argparse
import json
import sys
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import asdict

from config import CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY
from search import get_searcher, SearchResult
from enrichment_engine import get_enricher, StyleGuideEnrichment, TaxonomyEnrichment


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print formatted subheader."""
    print(f"\n--- {title} ---")


def format_claim(claim: SearchResult, indent: int = 2) -> str:
    """Format a claim for display."""
    prefix = " " * indent
    tier_badge = f"[{claim.proof_tier or 'T0'}]" if claim.proof_tier else ""
    domain_badge = f"[{claim.domain}]" if claim.domain else ""
    return f"{prefix}{tier_badge} {domain_badge} {claim.text[:100]}..."


def run_section_enrichment(
    section_topic: str,
    personas: List[str],
    use_llm: bool = True,
    output_json: bool = False
):
    """Enrich a specific style guide section."""
    print_header(f"Enriching Section: {section_topic}")

    enricher = get_enricher(use_llm=use_llm)
    enrichment = enricher.enrich_section(
        section_topic=section_topic,
        target_personas=personas,
        include_taxonomy=True
    )

    if output_json:
        # Convert to JSON-serializable format
        output = {
            "section_name": enrichment.section_name,
            "timestamp": enrichment.timestamp,
            "persona_examples": {
                p: [asdict(ex) for ex in examples]
                for p, examples in enrichment.persona_examples.items()
            },
            "taxonomy_enrichments": [asdict(t) for t in enrichment.taxonomy_enrichments],
            "foundever_specific": enrichment.foundever_specific,
            "metrics_discovered": enrichment.metrics_discovered,
            "templates_generated": enrichment.templates_generated,
            "raw_evidence": enrichment.raw_evidence
        }
        print(json.dumps(output, indent=2))
        return

    # Display results
    print(f"\nGenerated: {enrichment.timestamp}")
    print(f"\nEvidence Summary:")
    print(f"  High-quality claims: {enrichment.raw_evidence['high_quality_count']}")
    print(f"  Case study evidence: {enrichment.raw_evidence['case_study_count']}")
    print(f"  Outcome metrics: {enrichment.raw_evidence['outcome_count']}")

    print_subheader("Discovered Metrics")
    for metric in enrichment.metrics_discovered[:10]:
        print(f"  • {metric}")

    print_subheader("Persona Examples")
    for persona_key, examples in enrichment.persona_examples.items():
        persona_name = CLIENT_PERSONAS[persona_key]["display_name"]
        print(f"\n  {persona_name}:")
        for ex in examples[:3]:
            print(f"    [{ex.proof_tier}] {ex.domain}")
            print(f"      {ex.enriched_text[:80]}...")

    print_subheader("Taxonomy Enrichments")
    for tax in enrichment.taxonomy_enrichments:
        print(f"\n  {tax.domain} ({tax.evidence_count} claims)")
        if tax.discovered_metrics:
            print(f"    Metrics: {', '.join(tax.discovered_metrics[:3])}")
        if tax.discovered_capabilities:
            print(f"    Capabilities: {tax.discovered_capabilities[0][:60]}...")

    if enrichment.templates_generated:
        print_subheader("Generated Templates")
        for template in enrichment.templates_generated:
            print(f"  • {template}")

    print_subheader("Foundever-Specific Patterns")
    patterns = enrichment.foundever_specific
    print("\n  Domain Distribution:")
    for domain, count in sorted(patterns.get("common_domains", {}).items(), key=lambda x: -x[1])[:5]:
        print(f"    {domain}: {count}")

    print("\n  Proof Tier Distribution:")
    for tier, count in sorted(patterns.get("proof_distribution", {}).items()):
        print(f"    {tier}: {count}")

    if patterns.get("differentiators"):
        print("\n  Key Differentiators:")
        for diff in patterns["differentiators"][:3]:
            print(f"    • {diff[:80]}...")


def run_taxonomy_enrichment(use_llm: bool = True, output_json: bool = False):
    """Enrich the entire buyer domain taxonomy."""
    print_header("Enriching Buyer Domain Taxonomy")

    enricher = get_enricher(use_llm=use_llm)
    enriched = enricher.enrich_taxonomy()

    if output_json:
        output = {domain: asdict(tax) for domain, tax in enriched.items()}
        print(json.dumps(output, indent=2))
        return

    for domain, taxonomy in enriched.items():
        print_subheader(domain)
        print(f"  Evidence count: {taxonomy.evidence_count}")

        if taxonomy.discovered_metrics:
            print(f"\n  New Metrics Discovered:")
            for metric in taxonomy.discovered_metrics[:5]:
                print(f"    • {metric}")

        if taxonomy.discovered_capabilities:
            print(f"\n  Capabilities:")
            for cap in taxonomy.discovered_capabilities[:3]:
                print(f"    • {cap}")

        if taxonomy.example_claims:
            print(f"\n  Example Claims:")
            for claim in taxonomy.example_claims[:2]:
                print(f"    • {claim}")


def run_foundever_analysis(output_json: bool = False):
    """Analyze Foundever-specific patterns in the evidence."""
    print_header("Foundever Evidence Analysis")

    searcher = get_searcher()
    evidence = searcher.get_provider_evidence("Foundever")

    if output_json:
        print(json.dumps(evidence, indent=2))
        return

    print(f"\nTotal Claims: {evidence['total_claims']:,}")

    print_subheader("By Proof Tier")
    for tier, count in sorted(evidence["by_proof_tier"].items()):
        pct = (count / evidence["total_claims"]) * 100
        print(f"  {tier}: {count:,} ({pct:.1f}%)")

    print_subheader("By Claim Type")
    for ctype, count in sorted(evidence["by_claim_type"].items(), key=lambda x: -x[1]):
        print(f"  {ctype}: {count:,}")

    print_subheader("By Buyer Domain (Top 10)")
    domains_sorted = sorted(
        [(d, len(claims)) for d, claims in evidence["by_domain"].items()],
        key=lambda x: -x[1]
    )
    for domain, count in domains_sorted[:10]:
        print(f"  {domain}: {count}")

    print_subheader("Top Outcomes (T1+/T2)")
    for outcome in evidence["top_outcomes"][:10]:
        tier = outcome["proof_tier"]
        text = outcome["text"][:80]
        print(f"  [{tier}] {text}...")

    print_subheader("Case Studies")
    for cs in evidence["case_studies"][:5]:
        print(f"  • {cs['text'][:70]}...")
        print(f"    URL: {cs['source_url'][:60] if cs['source_url'] else 'N/A'}")


def run_voice_conversion(
    marketing_phrase: str,
    domain: str = "Customer Experience Operations",
    persona: str = "retail_bank",
    use_llm: bool = True,
    output_json: bool = False
):
    """Convert marketing phrases to practitioner voice."""
    print_header("Marketing to Practitioner Voice Conversion")

    enricher = get_enricher(use_llm=use_llm)
    alternatives = enricher.generate_practitioner_examples(
        marketing_phrase=marketing_phrase,
        domain=domain,
        persona=persona,
        count=5
    )

    if output_json:
        print(json.dumps(alternatives, indent=2))
        return

    print(f"\nOriginal: \"{marketing_phrase}\"")
    print(f"Domain: {domain}")
    print(f"Persona: {CLIENT_PERSONAS[persona]['display_name']}")

    print_subheader("Practitioner Alternatives")
    for i, alt in enumerate(alternatives, 1):
        print(f"\n  {i}. [{alt['proof_tier']}]")
        print(f"     {alt['practitioner_version'][:100]}...")
        if alt.get("refined_version"):
            print(f"     Refined: {alt['refined_version']}")
        if alt["metrics_used"]:
            print(f"     Metrics: {alt['metrics_used'][0] if alt['metrics_used'] else 'None'}")


def run_persona_search(
    persona: str,
    query: str,
    output_json: bool = False
):
    """Search evidence tailored to a specific persona."""
    if persona not in CLIENT_PERSONAS:
        print(f"Unknown persona: {persona}")
        print(f"Available: {', '.join(CLIENT_PERSONAS.keys())}")
        return

    print_header(f"Persona Search: {CLIENT_PERSONAS[persona]['display_name']}")

    searcher = get_searcher()
    results = searcher.search_for_persona(persona, query, limit=10)

    if output_json:
        output = {
            domain: [
                {
                    "text": r.text,
                    "score": r.score,
                    "proof_tier": r.proof_tier,
                    "source_url": r.source_url
                }
                for r in claims
            ]
            for domain, claims in results.items()
        }
        print(json.dumps(output, indent=2))
        return

    persona_info = CLIENT_PERSONAS[persona]
    print(f"\nDescription: {persona_info['description']}")
    print(f"Domains: {', '.join(persona_info['domains'])}")
    print(f"Query: \"{query}\"")

    for domain, claims in results.items():
        print_subheader(domain)
        for claim in claims[:5]:
            print(f"  [{claim.proof_tier}] Score: {claim.score:.3f}")
            print(f"    {claim.text[:80]}...")
            if claim.source_url:
                print(f"    Source: {claim.source_url[:50]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Style Guide Enrichment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich a section on collections
  python main.py --section "collections debt recovery"

  # Enrich taxonomy
  python main.py --taxonomy

  # Analyze Foundever evidence
  python main.py --foundever-analysis

  # Convert marketing to practitioner voice
  python main.py --convert "world-class fraud prevention" --domain "Financial Crime & Compliance Operations"

  # Search for a persona
  python main.py --persona card_issuer --query "dispute resolution"

Available Personas:
  paytech, retail_bank, card_issuer, investment_bank,
  insurance_carrier, mortgage_servicer, fintech_lender, collections_agency
        """
    )

    parser.add_argument(
        "--section", "-s",
        help="Section topic to enrich"
    )
    parser.add_argument(
        "--taxonomy", "-t",
        action="store_true",
        help="Enrich the buyer domain taxonomy"
    )
    parser.add_argument(
        "--foundever-analysis", "-f",
        action="store_true",
        help="Analyze Foundever evidence patterns"
    )
    parser.add_argument(
        "--convert", "-c",
        help="Convert marketing phrase to practitioner voice"
    )
    parser.add_argument(
        "--persona", "-p",
        help="Search for a specific persona"
    )
    parser.add_argument(
        "--query", "-q",
        help="Search query (used with --persona)"
    )
    parser.add_argument(
        "--domain", "-d",
        default="Customer Experience Operations",
        help="Buyer domain (used with --convert)"
    )
    parser.add_argument(
        "--personas",
        nargs="+",
        default=["paytech", "retail_bank", "card_issuer"],
        help="Personas to include in section enrichment"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM refinement (faster)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    use_llm = not args.no_llm

    if args.section:
        run_section_enrichment(
            section_topic=args.section,
            personas=args.personas,
            use_llm=use_llm,
            output_json=args.json
        )
    elif args.taxonomy:
        run_taxonomy_enrichment(use_llm=use_llm, output_json=args.json)
    elif args.foundever_analysis:
        run_foundever_analysis(output_json=args.json)
    elif args.convert:
        run_voice_conversion(
            marketing_phrase=args.convert,
            domain=args.domain,
            persona=args.personas[0] if args.personas else "retail_bank",
            use_llm=use_llm,
            output_json=args.json
        )
    elif args.persona and args.query:
        run_persona_search(
            persona=args.persona,
            query=args.query,
            output_json=args.json
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
