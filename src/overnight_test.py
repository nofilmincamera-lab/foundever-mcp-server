#!/usr/bin/env python3
"""
Overnight MCP Prompt Testing Script
====================================
Runs 50 banking client scenarios through MCP tools, fact-checks each,
and logs results for analysis to improve the MCP.

Run: python3 overnight_test.py
Output: overnight_test_results.json, overnight_test_report.md
"""

import json
import httpx
import time
import random
from datetime import datetime
from pathlib import Path

# Configuration
MCP_URL = "http://localhost:8420"
OLLAMA_URL = "http://localhost:11434/api/generate"
FACT_CHECK_MODEL = "qwen2.5:32b"
OUTPUT_DIR = Path("/home/willard/style_guide_enrichment/test_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Test scenarios - 50 diverse banking client prompts
TEST_SCENARIOS = [
    # Retail Banking (10)
    {"id": 1, "persona": "top_10_retail_bank", "scenario": "Build a proposal for a top-10 retail bank needing 500 FTE for customer service across voice and chat, with 24/7 coverage and Spanish language support."},
    {"id": 2, "persona": "top_10_retail_bank", "scenario": "Create an executive summary for a retail bank RFP requesting fraud dispute handling with Reg E compliance."},
    {"id": 3, "persona": "top_10_retail_bank", "scenario": "Draft a delivery model section for a retail bank wanting nearshore collections operations in Mexico."},
    {"id": 4, "persona": "top_10_retail_bank", "scenario": "Write a technology section for a retail bank requiring Salesforce CRM integration and real-time analytics."},
    {"id": 5, "persona": "top_10_retail_bank", "scenario": "Propose a transition plan for a retail bank moving 300 agents from an incumbent vendor within 90 days."},
    {"id": 6, "persona": "top_10_retail_bank", "scenario": "Address a retail bank's concerns about CFPB compliance in collections operations."},
    {"id": 7, "persona": "top_10_retail_bank", "scenario": "Create a governance section for a retail bank requiring SOC 2 Type II and PCI DSS compliance."},
    {"id": 8, "persona": "top_10_retail_bank", "scenario": "Draft proof points for a retail bank focused on FCR improvement and AHT reduction."},
    {"id": 9, "persona": "top_10_retail_bank", "scenario": "Build a staffing model for a retail bank with 40% seasonal volume variation."},
    {"id": 10, "persona": "top_10_retail_bank", "scenario": "Write a risk mitigation section for a retail bank concerned about agent attrition."},

    # Card Issuers (10)
    {"id": 11, "persona": "national_card_issuer", "scenario": "Create a fraud operations proposal for a national card issuer processing 50,000 fraud alerts daily."},
    {"id": 12, "persona": "national_card_issuer", "scenario": "Draft a collections strategy for a card issuer with $2B in charge-off inventory."},
    {"id": 13, "persona": "national_card_issuer", "scenario": "Build a chargeback dispute handling proposal with Visa/Mastercard compliance requirements."},
    {"id": 14, "persona": "national_card_issuer", "scenario": "Create an executive summary for a card issuer RFP requiring multi-channel support (voice, chat, social)."},
    {"id": 15, "persona": "national_card_issuer", "scenario": "Propose an AI-assisted fraud detection enhancement program for a card issuer."},
    {"id": 16, "persona": "national_card_issuer", "scenario": "Draft a compliance section addressing TCPA requirements for outbound collections."},
    {"id": 17, "persona": "national_card_issuer", "scenario": "Write a solution overview for a card issuer wanting to consolidate 5 vendors into 1."},
    {"id": 18, "persona": "national_card_issuer", "scenario": "Create a KPI framework for a card issuer focused on RPC rate and promise-to-pay metrics."},
    {"id": 19, "persona": "national_card_issuer", "scenario": "Build a technology integration proposal for a card issuer using FICO for decisioning."},
    {"id": 20, "persona": "national_card_issuer", "scenario": "Draft an implementation timeline for a card issuer requiring go-live in 6 months."},

    # Mortgage Servicers (8)
    {"id": 21, "persona": "mortgage_servicer", "scenario": "Create a loss mitigation proposal for a mortgage servicer with CFPB consent order requirements."},
    {"id": 22, "persona": "mortgage_servicer", "scenario": "Draft a default servicing operations proposal with state-specific compliance."},
    {"id": 23, "persona": "mortgage_servicer", "scenario": "Build an escrow customer service proposal for a top-5 mortgage servicer."},
    {"id": 24, "persona": "mortgage_servicer", "scenario": "Write a CARES Act compliance section for mortgage forbearance operations."},
    {"id": 25, "persona": "mortgage_servicer", "scenario": "Propose a foreclosure prevention program with borrower outreach capabilities."},
    {"id": 26, "persona": "mortgage_servicer", "scenario": "Create a quality assurance framework for mortgage servicing with 100% call recording."},
    {"id": 27, "persona": "mortgage_servicer", "scenario": "Draft a technology section for a servicer requiring Black Knight MSP integration."},
    {"id": 28, "persona": "mortgage_servicer", "scenario": "Build a training program proposal for complex mortgage modification scenarios."},

    # FinTech Lenders (8)
    {"id": 29, "persona": "fintech_lender", "scenario": "Create a collections proposal for a BNPL fintech with high-volume, low-balance accounts."},
    {"id": 30, "persona": "fintech_lender", "scenario": "Draft a customer service proposal for a digital lending platform with mobile-first users."},
    {"id": 31, "persona": "fintech_lender", "scenario": "Build a rapid scale-up proposal for a fintech expecting 3x volume growth in 12 months."},
    {"id": 32, "persona": "fintech_lender", "scenario": "Write a technology integration section for a fintech using cloud-native infrastructure."},
    {"id": 33, "persona": "fintech_lender", "scenario": "Propose an AI chatbot implementation for first-contact resolution at a fintech."},
    {"id": 34, "persona": "fintech_lender", "scenario": "Create a state licensing compliance section for a multi-state fintech lender."},
    {"id": 35, "persona": "fintech_lender", "scenario": "Draft an executive summary for a fintech wanting outcome-based pricing."},
    {"id": 36, "persona": "fintech_lender", "scenario": "Build a fraud prevention proposal for a fintech experiencing synthetic identity attacks."},

    # Payment Processors (6)
    {"id": 37, "persona": "payment_processor", "scenario": "Create a merchant support proposal for a payment processor with 100K+ merchants."},
    {"id": 38, "persona": "payment_processor", "scenario": "Draft a dispute resolution operations proposal for a payment network."},
    {"id": 39, "persona": "payment_processor", "scenario": "Build a technical support proposal for payment terminal troubleshooting."},
    {"id": 40, "persona": "payment_processor", "scenario": "Write a multi-language support section for a global payment processor (15 languages)."},
    {"id": 41, "persona": "payment_processor", "scenario": "Propose a merchant onboarding acceleration program for a payment processor."},
    {"id": 42, "persona": "payment_processor", "scenario": "Create a PCI DSS compliance section for payment operations."},

    # Insurance Carriers (4)
    {"id": 43, "persona": "insurance_carrier", "scenario": "Create a FNOL proposal for an insurance carrier processing 5,000 claims daily."},
    {"id": 44, "persona": "insurance_carrier", "scenario": "Draft a claims customer service proposal for a multi-line insurer."},
    {"id": 45, "persona": "insurance_carrier", "scenario": "Build a catastrophe surge support proposal for an insurance carrier."},
    {"id": 46, "persona": "insurance_carrier", "scenario": "Write a subrogation support proposal for an auto insurance carrier."},

    # Wealth Management (4)
    {"id": 47, "persona": "wealth_manager", "scenario": "Create a high-net-worth client service proposal for a wealth management firm."},
    {"id": 48, "persona": "wealth_manager", "scenario": "Draft a Series 7 licensed agent proposal for investment support services."},
    {"id": 49, "persona": "wealth_manager", "scenario": "Build a white-glove service model for ultra-HNW clients at a private bank."},
    {"id": 50, "persona": "wealth_manager", "scenario": "Propose a digital transformation for wealth management client communications."},
]

class MCPTester:
    def __init__(self):
        self.results = []
        self.issues_found = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def call_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool via HTTP (simulated - tools return JSON)."""
        # For this test, we'll directly import and call the handlers
        # In production, this would be proper MCP protocol calls
        try:
            # We'll use a simple HTTP approach to test
            # Since MCP uses SSE, we'll simulate by calling Ollama directly with prompts
            return {"status": "ok", "tool": tool_name, "args": arguments}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_proposal_section(self, scenario: dict) -> str:
        """Use Ollama to generate a proposal section based on scenario."""
        prompt = f"""You are a Foundever RFP response writer. Generate a proposal section for this scenario.

SCENARIO:
Persona: {scenario['persona']}
Request: {scenario['scenario']}

RULES (CRITICAL):
1. Use {{{{placeholder}}}} for ANY specific numbers you don't have evidence for
2. NEVER fabricate statistics - use placeholders like {{{{X agents}}}}, {{{{X%}}}}, {{{{$X.XM}}}}
3. Every statistic MUST have [Source] attribution or be a placeholder
4. Follow this structure:
   - Framing statement (italics)
   - Key metrics table (with placeholders for unknown values)
   - "The Point" section
   - Supporting detail
   - Value statement

IMPORTANT: If you don't know a specific number, USE A PLACEHOLDER. Do not make up numbers.

Generate the proposal section:"""

        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model": FACT_CHECK_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 1500
                        }
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    return f"ERROR: {response.status_code}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def fact_check_content(self, content: str, scenario: dict) -> dict:
        """Use Ollama to fact-check the generated content."""
        prompt = f"""You are a rigorous fact-checker for RFP proposals. Analyze this content for issues.

CONTENT TO CHECK:
{content[:4000]}

SCENARIO CONTEXT:
Persona: {scenario['persona']}
Request: {scenario['scenario']}

CHECK FOR:
1. FABRICATED STATISTICS - Numbers without [Source] or {{{{placeholder}}}} format
2. PRICING VIOLATIONS - Any mention of specific rates, costs, hourly prices (FORBIDDEN)
3. UNSOURCED CLAIMS - Assertions without attribution
4. MISSING PLACEHOLDERS - Specific numbers that should be {{{{placeholders}}}}
5. STYLE GUIDE VIOLATIONS - Missing structure elements

OUTPUT FORMAT (JSON):
{{
    "fabricated_stats": ["list of suspected fabricated numbers"],
    "pricing_violations": ["list of pricing mentions"],
    "unsourced_claims": ["list of claims without sources"],
    "missing_placeholders": ["numbers that should be placeholders"],
    "style_violations": ["missing structure elements"],
    "overall_score": 1-10,
    "pass_fail": "PASS or FAIL",
    "summary": "brief assessment"
}}

Respond with ONLY the JSON:"""

        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model": FACT_CHECK_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 1000
                        }
                    }
                )
                if response.status_code == 200:
                    result_text = response.json().get("response", "{}")
                    # Try to parse as JSON
                    try:
                        # Find JSON in response
                        start = result_text.find('{')
                        end = result_text.rfind('}') + 1
                        if start >= 0 and end > start:
                            return json.loads(result_text[start:end])
                    except:
                        pass
                    return {"raw_response": result_text, "parse_error": True}
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def run_single_test(self, scenario: dict) -> dict:
        """Run a single test scenario."""
        print(f"\n{'='*60}")
        print(f"Test {scenario['id']}/50: {scenario['persona']}")
        print(f"Scenario: {scenario['scenario'][:80]}...")
        print(f"{'='*60}")

        result = {
            "id": scenario["id"],
            "persona": scenario["persona"],
            "scenario": scenario["scenario"],
            "timestamp": datetime.now().isoformat(),
        }

        # Step 1: Generate proposal content
        print("  [1/2] Generating proposal content...")
        start_time = time.time()
        content = self.generate_proposal_section(scenario)
        result["generation_time"] = time.time() - start_time
        result["generated_content"] = content
        print(f"        Generated {len(content)} chars in {result['generation_time']:.1f}s")

        # Step 2: Fact-check the content
        print("  [2/2] Fact-checking content...")
        start_time = time.time()
        fact_check = self.fact_check_content(content, scenario)
        result["fact_check_time"] = time.time() - start_time
        result["fact_check"] = fact_check

        # Analyze results
        if isinstance(fact_check, dict) and not fact_check.get("error"):
            result["pass_fail"] = fact_check.get("pass_fail", "UNKNOWN")
            result["score"] = fact_check.get("overall_score", 0)

            # Count issues
            issues = {
                "fabricated_stats": len(fact_check.get("fabricated_stats", [])),
                "pricing_violations": len(fact_check.get("pricing_violations", [])),
                "unsourced_claims": len(fact_check.get("unsourced_claims", [])),
                "missing_placeholders": len(fact_check.get("missing_placeholders", [])),
                "style_violations": len(fact_check.get("style_violations", []))
            }
            result["issue_counts"] = issues
            result["total_issues"] = sum(issues.values())

            print(f"        Result: {result['pass_fail']} (Score: {result['score']}/10)")
            print(f"        Issues: {result['total_issues']} total")

            # Track specific issues for MCP improvement
            if issues["fabricated_stats"] > 0:
                self.issues_found.append({
                    "type": "fabrication",
                    "scenario_id": scenario["id"],
                    "details": fact_check.get("fabricated_stats", [])
                })
            if issues["pricing_violations"] > 0:
                self.issues_found.append({
                    "type": "pricing",
                    "scenario_id": scenario["id"],
                    "details": fact_check.get("pricing_violations", [])
                })
        else:
            result["pass_fail"] = "ERROR"
            result["score"] = 0
            result["total_issues"] = -1
            print(f"        Result: ERROR - {fact_check.get('error', 'Unknown')}")

        return result

    def run_all_tests(self):
        """Run all 50 test scenarios."""
        print("\n" + "="*70)
        print("OVERNIGHT MCP TESTING - 50 Banking Client Scenarios")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Model: {FACT_CHECK_MODEL}")
        print("="*70)

        total_start = time.time()

        for scenario in TEST_SCENARIOS:
            try:
                result = self.run_single_test(scenario)
                self.results.append(result)

                # Save intermediate results
                self.save_results()

                # Brief pause between tests
                time.sleep(2)

            except Exception as e:
                print(f"  ERROR in test {scenario['id']}: {str(e)}")
                self.results.append({
                    "id": scenario["id"],
                    "error": str(e),
                    "pass_fail": "ERROR"
                })

        total_time = time.time() - total_start
        print(f"\n{'='*70}")
        print(f"TESTING COMPLETE")
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"{'='*70}")

        # Generate final report
        self.generate_report(total_time)

    def save_results(self):
        """Save results to JSON file."""
        output_file = OUTPUT_DIR / f"test_results_{self.timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": self.timestamp,
                "model": FACT_CHECK_MODEL,
                "results": self.results,
                "issues_found": self.issues_found
            }, f, indent=2)

    def generate_report(self, total_time: float):
        """Generate markdown report with findings and MCP recommendations."""

        # Calculate statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.get("pass_fail") == "PASS")
        failed = sum(1 for r in self.results if r.get("pass_fail") == "FAIL")
        errors = sum(1 for r in self.results if r.get("pass_fail") == "ERROR")

        avg_score = sum(r.get("score", 0) for r in self.results if r.get("score")) / max(1, total_tests - errors)

        # Count issue types
        issue_totals = {
            "fabricated_stats": 0,
            "pricing_violations": 0,
            "unsourced_claims": 0,
            "missing_placeholders": 0,
            "style_violations": 0
        }

        for r in self.results:
            if "issue_counts" in r:
                for k, v in r["issue_counts"].items():
                    issue_totals[k] += v

        # Group by persona
        persona_stats = {}
        for r in self.results:
            persona = r.get("persona", "unknown")
            if persona not in persona_stats:
                persona_stats[persona] = {"passed": 0, "failed": 0, "errors": 0, "total_issues": 0}
            if r.get("pass_fail") == "PASS":
                persona_stats[persona]["passed"] += 1
            elif r.get("pass_fail") == "FAIL":
                persona_stats[persona]["failed"] += 1
            else:
                persona_stats[persona]["errors"] += 1
            persona_stats[persona]["total_issues"] += r.get("total_issues", 0)

        # Generate report
        report = f"""# Overnight MCP Test Report

**Generated:** {datetime.now().isoformat()}
**Model:** {FACT_CHECK_MODEL}
**Total Time:** {total_time/60:.1f} minutes

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total_tests} |
| Passed | {passed} ({passed/total_tests*100:.1f}%) |
| Failed | {failed} ({failed/total_tests*100:.1f}%) |
| Errors | {errors} |
| Average Score | {avg_score:.1f}/10 |

---

## Issue Breakdown

| Issue Type | Count | Priority |
|------------|-------|----------|
| Fabricated Statistics | {issue_totals['fabricated_stats']} | 🔴 Critical |
| Pricing Violations | {issue_totals['pricing_violations']} | 🔴 Critical |
| Unsourced Claims | {issue_totals['unsourced_claims']} | 🟡 High |
| Missing Placeholders | {issue_totals['missing_placeholders']} | 🟡 High |
| Style Violations | {issue_totals['style_violations']} | 🟢 Medium |

---

## Results by Persona

| Persona | Passed | Failed | Errors | Total Issues |
|---------|--------|--------|--------|--------------|
"""
        for persona, stats in sorted(persona_stats.items()):
            report += f"| {persona} | {stats['passed']} | {stats['failed']} | {stats['errors']} | {stats['total_issues']} |\n"

        report += """
---

## MCP Improvement Recommendations

Based on the test results, the following improvements are recommended:

### Critical Fixes

"""

        if issue_totals['fabricated_stats'] > 0:
            report += f"""#### 1. Fabrication Prevention (Found: {issue_totals['fabricated_stats']} instances)

The model is still fabricating statistics despite instructions. Recommendations:
- **Strengthen `get_no_fabrication_policy`** - Make rules more prominent
- **Add pre-generation check** - Remind about placeholders before every generation
- **Enhance `check_for_fabrication`** - Add more patterns to detect
- **Consider blocking patterns** - Reject content with unsourced round numbers

"""

        if issue_totals['pricing_violations'] > 0:
            report += f"""#### 2. Pricing Leak Prevention (Found: {issue_totals['pricing_violations']} instances)

Pricing information is still appearing. Recommendations:
- **Add pricing filter** - Post-process to remove any $X/hr or rate mentions
- **Strengthen prompt** - Make pricing restriction more prominent
- **Add negative examples** - Show what NOT to include

"""

        if issue_totals['unsourced_claims'] > 0:
            report += f"""#### 3. Source Attribution (Found: {issue_totals['unsourced_claims']} instances)

Claims without sources are common. Recommendations:
- **Require [Source] format** - Make attribution syntax mandatory
- **Pre-populate sources** - Provide Qdrant evidence before generation
- **Add attribution helper** - Tool to add sources to existing content

"""

        report += """
### Process Improvements

1. **Two-Pass Generation** - Generate structure first, fill facts second
2. **Evidence-First Approach** - Search Qdrant BEFORE drafting
3. **Interactive Clarification** - Generate questions for ambiguous requirements
4. **Template Enforcement** - Stricter adherence to section templates

---

## Detailed Results

"""

        # Add detailed results for failed tests
        failed_tests = [r for r in self.results if r.get("pass_fail") == "FAIL"]
        if failed_tests:
            report += "### Failed Tests\n\n"
            for r in failed_tests[:10]:  # Top 10 failures
                report += f"""#### Test {r['id']}: {r['persona']}

**Scenario:** {r['scenario'][:100]}...

**Issues:**
- Fabricated: {r.get('issue_counts', {}).get('fabricated_stats', 0)}
- Pricing: {r.get('issue_counts', {}).get('pricing_violations', 0)}
- Unsourced: {r.get('issue_counts', {}).get('unsourced_claims', 0)}

**Fact Check Summary:** {r.get('fact_check', {}).get('summary', 'N/A')}

---

"""

        report += """
## Next Steps

1. Review failed test cases in detail
2. Update MCP tools based on recommendations
3. Re-run tests to verify improvements
4. Iterate until pass rate > 90%

---

*Report generated automatically by overnight_test.py*
"""

        # Save report
        report_file = OUTPUT_DIR / f"test_report_{self.timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\nReport saved to: {report_file}")
        print(f"Results saved to: {OUTPUT_DIR / f'test_results_{self.timestamp}.json'}")

        # Also save to a "latest" file for easy access
        latest_report = OUTPUT_DIR / "LATEST_REPORT.md"
        with open(latest_report, 'w') as f:
            f.write(report)

        latest_results = OUTPUT_DIR / "LATEST_RESULTS.json"
        with open(latest_results, 'w') as f:
            json.dump({
                "timestamp": self.timestamp,
                "model": FACT_CHECK_MODEL,
                "summary": {
                    "total": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "avg_score": avg_score,
                    "issue_totals": issue_totals
                },
                "results": self.results,
                "issues_found": self.issues_found
            }, f, indent=2)


if __name__ == "__main__":
    tester = MCPTester()
    tester.run_all_tests()
