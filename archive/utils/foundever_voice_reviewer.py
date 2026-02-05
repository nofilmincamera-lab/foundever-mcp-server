#!/usr/bin/env python3
"""
Foundever Voice Slide Reviewer

Uses the Foundever Voice MCP to:
1. Review slide classification
2. Analyze slides against Foundever voice patterns
3. Rank slides by voice alignment
"""

import os
import json
import httpx
import asyncio
from pathlib import Path
from collections import defaultdict


# Configuration
EXTRACTED_SLIDES_DIR = "/home/willard/document_skills_mcp/extracted_slides"
CLASSIFICATION_REPORT = os.path.join(EXTRACTED_SLIDES_DIR, "classification_report.json")
OLLAMA_URL = "http://localhost:11434/api/generate"
FOUNDEVER_VOICE_MODEL = "foundever-voice-q5:latest"
OUTPUT_FILE = os.path.join(EXTRACTED_SLIDES_DIR, "foundever_voice_analysis.json")


# Foundever Voice System Prompt (from foundever-mcp-server config)
FOUNDEVER_VOICE_SYSTEM_PROMPT = """You are a Foundever RFP response assistant. You write in Foundever's professional voice, using specific patterns:
- Confirmation syntax for acknowledging requirements
- Value bridges connecting features to client benefits
- So-what closes summarizing value propositions
Always use {{placeholders}} for specific client data you don't have."""


async def analyze_slide_with_foundever_voice(slide_content, slide_title):
    """Analyze a slide using Foundever Voice model."""

    prompt = f"""Analyze this slide content from a presentation and provide:
1. Voice Alignment Score (1-10): How well does this align with Foundever's professional voice patterns?
2. Key Strengths: What voice patterns are done well?
3. Improvement Suggestions: How could this better align with Foundever voice?
4. Missing Elements: What Foundever voice patterns are missing?

Slide Title: {slide_title}

Content:
{slide_content}

Respond in JSON format:
{{
  "voice_alignment_score": <1-10>,
  "key_strengths": ["strength1", "strength2"],
  "improvement_suggestions": ["suggestion1", "suggestion2"],
  "missing_elements": ["element1", "element2"],
  "has_confirmation_syntax": <true/false>,
  "has_value_bridges": <true/false>,
  "has_so_what_closes": <true/false>,
  "overall_assessment": "brief assessment"
}}
"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": FOUNDEVER_VOICE_MODEL,
                    "prompt": prompt,
                    "system": FOUNDEVER_VOICE_SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1000
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                llm_response = data.get("response", "").strip()

                # Try to parse JSON from response
                try:
                    # Find JSON in response
                    start = llm_response.find('{')
                    end = llm_response.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = llm_response[start:end]
                        analysis = json.loads(json_str)
                        return analysis
                except json.JSONDecodeError:
                    print(f"  Warning: Could not parse JSON from LLM response for {slide_title}")
                    return {
                        "voice_alignment_score": 5,
                        "raw_response": llm_response
                    }

            else:
                print(f"  Error: HTTP {response.status_code}")
                return None

    except Exception as e:
        print(f"  Error analyzing slide {slide_title}: {e}")
        return None


async def review_all_slides():
    """Review all extracted slides with Foundever Voice."""
    print("=" * 80)
    print("Foundever Voice Slide Reviewer")
    print("=" * 80)

    # Load classification report
    with open(CLASSIFICATION_REPORT, 'r', encoding='utf-8') as f:
        classification = json.load(f)

    print(f"\n📊 Total slides to review: {classification['total_slides']}")
    print(f"📂 Categories: {len(classification['categories'])}")

    # Get all slide files
    slide_files = [f for f in os.listdir(EXTRACTED_SLIDES_DIR) if f.endswith('.txt')]
    print(f"\n📄 Found {len(slide_files)} slide text files")

    # Analyze each slide
    results = {
        'total_slides': len(slide_files),
        'slides': [],
        'rankings': {
            'top_aligned': [],
            'needs_improvement': [],
            'by_category': {}
        },
        'summary': {}
    }

    print("\n🎯 Analyzing slides with Foundever Voice model...")
    print("   (This may take a few minutes)\n")

    for idx, slide_file in enumerate(sorted(slide_files), 1):
        slide_path = os.path.join(EXTRACTED_SLIDES_DIR, slide_file)

        # Read slide content
        with open(slide_path, 'r', encoding='utf-8') as f:
            slide_content = f.read()

        # Extract title from filename
        slide_title = slide_file.replace('.txt', '').split(' - ', 1)[1] if ' - ' in slide_file else slide_file

        print(f"  [{idx}/{len(slide_files)}] Analyzing: {slide_title[:60]}...")

        # Analyze with Foundever Voice
        analysis = await analyze_slide_with_foundever_voice(slide_content, slide_title)

        if analysis:
            slide_result = {
                'filename': slide_file,
                'title': slide_title,
                'analysis': analysis,
                'content_preview': slide_content[:200]
            }
            results['slides'].append(slide_result)

            # Print score
            score = analysis.get('voice_alignment_score', 0)
            print(f"      → Voice Alignment Score: {score}/10")

    # Calculate rankings
    print("\n📈 Calculating rankings...")

    # Sort by voice alignment score
    sorted_slides = sorted(
        results['slides'],
        key=lambda x: x['analysis'].get('voice_alignment_score', 0),
        reverse=True
    )

    # Top 10 aligned slides
    results['rankings']['top_aligned'] = [
        {
            'title': s['title'],
            'filename': s['filename'],
            'score': s['analysis'].get('voice_alignment_score', 0),
            'assessment': s['analysis'].get('overall_assessment', '')
        }
        for s in sorted_slides[:10]
    ]

    # Bottom 10 needing improvement
    results['rankings']['needs_improvement'] = [
        {
            'title': s['title'],
            'filename': s['filename'],
            'score': s['analysis'].get('voice_alignment_score', 0),
            'suggestions': s['analysis'].get('improvement_suggestions', [])
        }
        for s in sorted_slides[-10:]
    ]

    # Calculate summary statistics
    scores = [s['analysis'].get('voice_alignment_score', 0) for s in results['slides']]
    results['summary'] = {
        'average_score': sum(scores) / len(scores) if scores else 0,
        'highest_score': max(scores) if scores else 0,
        'lowest_score': min(scores) if scores else 0,
        'slides_with_confirmation_syntax': sum(1 for s in results['slides'] if s['analysis'].get('has_confirmation_syntax', False)),
        'slides_with_value_bridges': sum(1 for s in results['slides'] if s['analysis'].get('has_value_bridges', False)),
        'slides_with_so_what_closes': sum(1 for s in results['slides'] if s['analysis'].get('has_so_what_closes', False))
    }

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Analysis complete!")
    print(f"   Results saved to: {OUTPUT_FILE}")

    # Print summary
    print("\n" + "=" * 80)
    print("FOUNDEVER VOICE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total slides analyzed: {len(results['slides'])}")
    print(f"Average voice alignment: {results['summary']['average_score']:.1f}/10")
    print(f"Highest score: {results['summary']['highest_score']}/10")
    print(f"Lowest score: {results['summary']['lowest_score']}/10")
    print(f"\nVoice Pattern Usage:")
    print(f"  Confirmation syntax: {results['summary']['slides_with_confirmation_syntax']} slides")
    print(f"  Value bridges: {results['summary']['slides_with_value_bridges']} slides")
    print(f"  So-what closes: {results['summary']['slides_with_so_what_closes']} slides")

    print(f"\n🏆 Top 5 Best-Aligned Slides:")
    for i, slide in enumerate(results['rankings']['top_aligned'][:5], 1):
        print(f"  {i}. [{slide['score']}/10] {slide['title'][:60]}")

    print(f"\n⚠️  Top 5 Slides Needing Improvement:")
    for i, slide in enumerate(results['rankings']['needs_improvement'][:5], 1):
        print(f"  {i}. [{slide['score']}/10] {slide['title'][:60]}")

    print("=" * 80)


async def main():
    """Main execution."""
    await review_all_slides()


if __name__ == '__main__':
    asyncio.run(main())
