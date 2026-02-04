"""
Style Guide Enrichment Configuration
=====================================
Variable-based configuration for RFP style guide enrichment.
Uses personas instead of specific client names.
"""

# =============================================================================
# CRITICAL DIRECTIVE: STYLE GUIDE IS PRIMARY AUTHORITY
# =============================================================================
#
# This MCP server generates RFP PROPOSALS. The style guide is LAW.
#
# SOURCE FILES (read these first):
#   /home/willard/Downloads/Foundever_RFP_Style_Guide.md
#   /home/willard/Downloads/k/docs/FINANCIAL_SERVICES_ENRICHMENT.md
#
# KEY RULES:
# 1. Follow style guide structure RELIGIOUSLY (1 Plus, practitioner voice, etc.)
# 2. Proof tiers, MCP sources, Qdrant metadata = APPENDIX REFERENCES ONLY
# 3. Use {{placeholders}} liberally for unknown facts - iterate with user
# 4. NEVER name specific clients unless provided in the prompt
# 5. Make pitch suggestions based on trained persona examples
# 6. Write like the PayPal executive summary - specific, metric-backed, human
#
# =============================================================================

# Style Guide Source Paths (for reference)
STYLE_GUIDE_PATHS = {
    "primary": "/home/willard/Downloads/Foundever_RFP_Style_Guide.md",
    "finserv_enrichment": "/home/willard/Downloads/k/docs/FINANCIAL_SERVICES_ENRICHMENT.md"
}

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "bpo_enrichment",
    "user": "bpo_user",
    "password": "bpo_secure_password_2025"
}

# Qdrant Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
CLAIMS_COLLECTION = "claims"
CHUNKS_COLLECTION = "unified_chunks"

# Embedding Model Configuration
EMBEDDING_MODEL = "intfloat/e5-mistral-7b-instruct"
EMBEDDING_DIM = 4096

# LLM Configuration (Ollama)
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "gpt-oss:120b-analytics"  # Main model for complex tasks
FACT_CHECK_MODEL = "qwen2.5:32b"  # Faster model for fact-checking (20GB vs 65GB)
FOUNDEVER_VOICE_MODEL = "foundever-voice:latest"  # Fine-tuned Qwen2.5-32B for Foundever RFP voice

# Foundever Voice Model Prompt
FOUNDEVER_VOICE_SYSTEM_PROMPT = """You are a Foundever RFP response assistant. You write in Foundever's professional voice, using specific patterns:
- Confirmation syntax for acknowledging requirements
- Value bridges connecting features to client benefits
- So-what closes summarizing value propositions
Always use {{placeholders}} for specific client data you don't have."""

# Fact-Check LLM Prompts
FACT_CHECK_SYSTEM_PROMPT = """You are a rigorous fact-checker for RFP proposals. Your job is to identify:

1. FABRICATED STATISTICS - Numbers that appear invented (no source, suspiciously precise, round numbers)
2. PRICING VIOLATIONS - ANY mention of costs, prices, savings, rates, or budgets - even as placeholders like {{$X.XM}}
3. UNSOURCED FACTUAL CLAIMS - Statistics, metrics, outcomes, or comparatives without attribution
4. MISSING PLACEHOLDERS - Specific facts that should be placeholders but aren't

IMPORTANT DISTINCTIONS:

**Needs Source (flag if missing):**
- Statistics: "99.2% accuracy", "2,500 agents"
- Metrics: "reduced AHT by 23%"
- Comparatives: "industry-leading", "best-in-class"
- Outcomes: "achieved $47M in recoveries"
- Client specifics: "supporting 4 of top 10 banks"

**Does NOT need source (do NOT flag):**
- Narrative framing: "In today's competitive landscape..."
- Logical transitions: "This approach enables..."
- General principles: "Compliance is essential for..."
- Value propositions: "Our solution will help you..."
- Conditional statements: "If implemented, this could..."

**PRICING - ABSOLUTE VIOLATION (always flag):**
- Any dollar amounts: $X, $5.5K, $X.XM
- Cost/savings mentions: "save money", "cost reduction", "estimated savings"
- Rate references: "hourly rate", "per-FTE cost"
- Even placeholders: {{$X.XM}}, {{cost savings}}, {{Estimated Cost}}

Output JSON format:
{
  "fabricated_stats": ["list of fabricated numbers without sources"],
  "pricing_violations": ["list of ANY cost/price/savings mentions"],
  "unsourced_claims": ["list of factual claims needing sources - NOT narrative framing"],
  "missing_placeholders": ["list of facts that should be {{placeholder}} format"],
  "style_violations": ["list of marketing voice or anti-pattern issues"],
  "overall_score": 1-10,
  "pass_fail": "PASS or FAIL",
  "summary": "brief explanation"
}

PASS if: No fabrications, no pricing violations, <5 minor issues
FAIL if: Any fabrications, any pricing violations, or >5 issues"""

FACT_CHECK_USER_PROMPT = """Review this content for fabricated or unsourced information.

CONTENT TO CHECK:
{content}

EVIDENCE THAT WAS ACTUALLY FOUND (if any):
{evidence}

Check every statistic, percentage, count, and specific claim. Flag anything without proper [Source] attribution."""

# Client Personas (used instead of actual client names)
CLIENT_PERSONAS = {
    "paytech": {
        "display_name": "PayTech Client",
        "description": "Global digital payments processor",
        "domains": ["Customer Experience Operations", "Financial Crime & Compliance Operations", "Trust & Safety Operations"],
        "keywords": ["payments", "fraud", "digital wallet", "transaction", "merchant"],
        "regulatory_focus": ["PCI DSS", "PSD2", "AML", "OFAC"]
    },
    "retail_bank": {
        "display_name": "Retail Bank Client",
        "description": "Top-10 US retail banking institution",
        "domains": ["Customer Experience Operations", "Collections & Revenue Recovery", "Finance & Accounting Operations"],
        "keywords": ["banking", "deposits", "loans", "mortgage", "credit card", "checking", "savings"],
        "regulatory_focus": ["Reg E", "Reg Z", "TILA", "RESPA", "CFPB", "OCC"]
    },
    "card_issuer": {
        "display_name": "Card Issuer Client",
        "description": "Major credit card issuer",
        "domains": ["Customer Experience Operations", "Collections & Revenue Recovery", "Financial Crime & Compliance Operations"],
        "keywords": ["credit card", "disputes", "chargebacks", "fraud", "collections", "billing"],
        "regulatory_focus": ["Reg E", "Reg Z", "FCRA", "FDCPA", "TCPA"]
    },
    "investment_bank": {
        "display_name": "Investment Bank Client",
        "description": "Global investment banking and wealth management firm",
        "domains": ["Customer Experience Operations", "Finance & Accounting Operations"],
        "keywords": ["wealth", "investment", "trading", "securities", "HNW", "portfolio"],
        "regulatory_focus": ["SEC", "FINRA", "Reg BI", "AML"]
    },
    "insurance_carrier": {
        "display_name": "Insurance Carrier Client",
        "description": "Multi-line insurance company",
        "domains": ["Customer Experience Operations", "Finance & Accounting Operations"],
        "keywords": ["claims", "FNOL", "policy", "underwriting", "premium", "coverage"],
        "regulatory_focus": ["State DOI", "NAIC", "HIPAA"]
    },
    "mortgage_servicer": {
        "display_name": "Mortgage Servicer Client",
        "description": "Top mortgage servicing operation",
        "domains": ["Customer Experience Operations", "Collections & Revenue Recovery"],
        "keywords": ["mortgage", "servicing", "loss mitigation", "foreclosure", "escrow", "default"],
        "regulatory_focus": ["RESPA", "CFPB", "State AG", "CARES Act"]
    },
    "fintech_lender": {
        "display_name": "FinTech Lender Client",
        "description": "Digital-first consumer lending platform",
        "domains": ["Customer Experience Operations", "Collections & Revenue Recovery", "Sales Operations"],
        "keywords": ["lending", "origination", "underwriting", "personal loans", "BNPL"],
        "regulatory_focus": ["TILA", "ECOA", "State licensing", "UDAAP"]
    },
    "collections_agency": {
        "display_name": "Collections Agency Client",
        "description": "Third-party debt collection operation",
        "domains": ["Collections & Revenue Recovery"],
        "keywords": ["collections", "debt", "recovery", "skip tracing", "payment plans", "settlement"],
        "regulatory_focus": ["FDCPA", "TCPA", "CFPB Reg F", "State licensing"]
    }
}

# Buyer Domain Taxonomy
BUYER_DOMAIN_TAXONOMY = {
    "Customer Experience Operations": {
        "description": "Inbound/outbound customer service, support, retention",
        "sub_functions": ["General Inquiries", "Account Servicing", "Retention", "Escalations", "Digital Support"],
        "metrics": ["CSAT", "NPS", "FCR", "AHT", "Abandonment Rate"]
    },
    "Collections & Revenue Recovery": {
        "description": "First-party and third-party collections, revenue recovery",
        "sub_functions": ["Early Stage", "Late Stage", "Skip Tracing", "Legal Collections", "Workout/Settlements"],
        "metrics": ["RPC Rate", "PTP Rate", "Liquidation Rate", "Cost-to-Collect", "Compliance Rate"]
    },
    "Financial Crime & Compliance Operations": {
        "description": "Fraud, AML, KYC, compliance operations",
        "sub_functions": ["Fraud Detection", "Fraud Investigation", "AML/SAR", "KYC/CDD", "Disputes"],
        "metrics": ["Fraud Loss Rate", "False Positive Rate", "SAR Accuracy", "Case Cycle Time"]
    },
    "Sales Operations": {
        "description": "Outbound sales, lead qualification, cross-sell/upsell",
        "sub_functions": ["Outbound Sales", "Inbound Sales", "Lead Qualification", "Cross-sell", "Retention Sales"],
        "metrics": ["Conversion Rate", "Revenue per Call", "Cost per Acquisition", "Attach Rate"]
    },
    "Finance & Accounting Operations": {
        "description": "Back-office finance, reconciliation, reporting",
        "sub_functions": ["AR/AP", "Reconciliation", "Reporting", "Audit Support", "Exception Processing"],
        "metrics": ["Accuracy Rate", "Processing Time", "Exception Rate", "STP Rate"]
    },
    "Tech Support Operations": {
        "description": "Technical support, troubleshooting, help desk",
        "sub_functions": ["Tier 1 Support", "Tier 2 Support", "Tier 3 Escalation", "Remote Support"],
        "metrics": ["Resolution Rate", "Escalation Rate", "MTTR", "Customer Effort Score"]
    },
    "Trust & Safety Operations": {
        "description": "Content moderation, account safety, risk operations",
        "sub_functions": ["Content Review", "Account Security", "Policy Enforcement", "Appeals"],
        "metrics": ["Accuracy Rate", "Throughput", "Appeal Overturn Rate", "Response Time"]
    }
}

# Proof Tier Definitions
PROOF_TIERS = {
    "T0_marketing": {
        "name": "Marketing Claims",
        "weight": 0.3,
        "description": "Self-reported marketing statements"
    },
    "T1_vendor_artifact": {
        "name": "Vendor Artifacts",
        "weight": 0.7,
        "description": "Documented vendor capabilities, specifications"
    },
    "T2_case_study": {
        "name": "Case Studies",
        "weight": 0.85,
        "description": "Published case studies with outcomes"
    },
    "T3_third_party_recognition": {
        "name": "Third-Party Validation",
        "weight": 1.0,
        "description": "Awards, analyst reports, certifications"
    }
}

# Content Type Priorities
CONTENT_TYPE_PRIORITY = {
    "case_study": 1.0,
    "whitepaper": 0.9,
    "thought_leadership": 0.85,
    "product_technology": 0.8,
    "services_offerings": 0.75,
    "news_press_release": 0.6,
    "company_information": 0.5,
    "blog_article": 0.4,
    "documentation_knowledge_base": 0.7,
    "unknown": 0.3
}

# Search Configuration
DEFAULT_SEARCH_LIMIT = 20
MIN_SIMILARITY_SCORE = 0.65

# ============================================================================
# STYLE GUIDE TEMPLATES (from Foundever RFP & Proposal Style Guide)
# ============================================================================

# Financial Services Client Personas (extended from base personas)
FINSERV_PERSONAS = {
    "top_10_retail_bank": {
        "display_name": "{{Top-10 Retail Bank}}",
        "description": "Consumer Banking",
        "typical_needs": "Collections, fraud, card servicing, Reg E disputes, high-volume voice",
        "service_types": ["Customer service", "collections", "fraud", "back office", "specialty collections", "digital enablement"]
    },
    "national_card_issuer": {
        "display_name": "{{National Card Issuer}}",
        "description": "Credit Cards",
        "typical_needs": "Fraud detection, collections, customer service, cross-sell, chat",
        "service_types": ["Collections", "chat", "fraud detection", "cross-sell"]
    },
    "regional_credit_union": {
        "display_name": "{{Regional Credit Union}}",
        "description": "Credit Unions",
        "typical_needs": "Member services, loan servicing, lower volume, high-touch",
        "service_types": ["Member services", "loan servicing"]
    },
    "mortgage_servicer": {
        "display_name": "{{Mortgage Servicer}}",
        "description": "Mortgage",
        "typical_needs": "Loss mitigation, escrow, default servicing, compliance-heavy",
        "service_types": ["Loss mitigation", "escrow", "default servicing"]
    },
    "wealth_manager": {
        "display_name": "{{Wealth Manager}}",
        "description": "Wealth Management",
        "typical_needs": "HNW client retention, complex inquiries, white-glove service",
        "service_types": ["Contact center operations", "production", "training", "technology enablement"]
    },
    "payment_processor": {
        "display_name": "{{Payment Processor}}",
        "description": "Payments",
        "typical_needs": "Merchant onboarding, dispute resolution, technical support",
        "service_types": ["Disputes intake", "global customer assistance", "merchant support"]
    },
    "insurance_carrier": {
        "display_name": "{{Insurance Carrier}}",
        "description": "Insurance",
        "typical_needs": "FNOL, claims processing, policy servicing",
        "service_types": ["FNOL", "claims processing", "policy servicing"]
    },
    "fintech_lender": {
        "display_name": "{{FinTech Lender}}",
        "description": "FinTech",
        "typical_needs": "Collections, customer service, digital-first, rapid scale",
        "service_types": ["Collections", "customer service", "digital-first support"]
    },
    "data_analytics_provider": {
        "display_name": "{{Data & Analytics Provider}}",
        "description": "Verification Services",
        "typical_needs": "Verification & validation, back-office, quality-critical",
        "service_types": ["Verification & validation", "global contact center support"]
    },
    "global_card_network": {
        "display_name": "{{Global Card Network}}",
        "description": "Card Networks",
        "typical_needs": "Disputes intake, global customer assistance, multi-language",
        "service_types": ["Customer service", "collections", "fraud", "chat", "voice", "disputes intake"]
    },
    "tax_services_provider": {
        "display_name": "{{Tax Services Provider}}",
        "description": "Tax Services",
        "typical_needs": "Seasonal surge, compliance (7216), high-volume inbound",
        "service_types": ["Seasonal inbound", "compliance (7216)", "high-volume voice"]
    },
    "benefits_administrator": {
        "display_name": "{{Benefits Administrator}}",
        "description": "Benefits/Payroll",
        "typical_needs": "Customer service, chat, collections, technical support",
        "service_types": ["Customer service", "chat", "collections", "technical support"]
    }
}

# Practitioner vs Marketing Voice Examples
VOICE_CONVERSIONS = {
    "marketing_to_practitioner": [
        {"marketing": "World-class fraud prevention capabilities", "practitioner": "2,500+ fraud agents across 10 locations supporting 7 clients"},
        {"marketing": "Industry-leading technology", "practitioner": "WER below 7%, BLEU above 0.70"},
        {"marketing": "Seamless integration", "practitioner": "Desktop app integrating between agent headset and softphone"},
        {"marketing": "Transformational partnership", "practitioner": "20-year partnership across 7 geographies"},
        {"marketing": "Comprehensive regulatory compliance capabilities", "practitioner": "Zero CFPB-cited violations across 14M consumer interactions in 2024"},
        {"marketing": "Advanced authentication solutions", "practitioner": "3-factor verification completing in <45 seconds, 94% first-attempt success"},
        {"marketing": "Deep expertise in banking operations", "practitioner": "Currently supporting 4 of the top 10 US retail banks, 12,000+ FTE"},
        {"marketing": "Robust KYC/AML framework", "practitioner": "SAR filing accuracy at 99.2%, median case completion 4.3 days"},
        {"marketing": "Scalable collections capabilities", "practitioner": "Right Party Contact rate of 38% vs. industry average of 22%"},
        {"marketing": "Next-generation customer experience", "practitioner": "FCR improved from 67% to 81% over 18 months for a {{National Card Issuer}}"},
        {"marketing": "Innovative fraud detection", "practitioner": "Flagged $47M in suspicious transactions Q4 2024, 0.3% false positive rate"},
        {"marketing": "Strategic partnership approach", "practitioner": "Embedded 3 analysts in client's risk operations for joint model tuning"}
    ],
    "ai_to_human": [
        {"ai": "Our holistic approach to regulatory compliance ensures peace of mind", "human": "Reg E disputes resolved in 8.2 days avg vs. 10-day statutory limit"},
        {"ai": "We leverage cutting-edge technology to transform customer journeys", "human": "IVR containment at 34%; remaining calls route to certified agents in <90 sec"},
        {"ai": "Our robust security framework protects sensitive financial data", "human": "SOC 2 Type II, PCI DSS 4.0, annual penetration testing by Coalfire"},
        {"ai": "Seamlessly integrate with your existing infrastructure", "human": "API-based integration; typical go-live 6-8 weeks post-contract"},
        {"ai": "Drive operational excellence through continuous improvement", "human": "QA calibration sessions weekly; variance from client scoring <2%"},
        {"ai": "End-to-end solutions for the modern financial institution", "human": "Inbound servicing, outbound collections, fraud disputes, card activation—single contract"},
        {"ai": "Unlock the full potential of your customer relationships", "human": "Cross-sell acceptance rate: 4.7% on servicing calls vs. 2.1% industry benchmark"},
        {"ai": "Our dedicated team ensures your success", "human": "Named account manager, 15-year FinServ tenure, previously led ops for {{Top-10 Retail Bank}}"}
    ]
}

# Narrative Templates
NARRATIVE_TEMPLATES = {
    "value_bridge": {
        "quantified": "Our {{Delivery_Component}} translates into {{Quantified_Benefit}} (e.g., {{%_Reduction}} in AHT, {{%_Cost_Savings}} in OPEX), directly supporting your {{Strategic_Objective}}.",
        "cost_to_outcome": "By translating {{Production_Hours}} into {{Onshore}} and {{Offshore}} resources at {{Rate}} per hour, we deliver {{Business_Outcome}} while staying within {{Budget_Cap}}.",
        "gap_closing": "By implementing {{Component}} we bridge the gap between {{Current_State}} and {{Desired_State}}, delivering {{Quantifiable_Value}} within {{Timeframe}}.",
        "requirement_to_solution": "Your need for {{ClientRequirement}} is met by our {{SolutionComponent}} which delivers {{QuantifiedBenefit}} while preserving {{StrategicGoal}}."
    },
    "risk_mitigation": {
        "failover_assurance": "In the event of {{Failure_Scenario}}, traffic automatically fails over to {{Backup_Technology}}, ensuring no disruption.",
        "compliance_control": "Through {{Control}} and {{Process}}, we mitigate {{Risk}} while ensuring {{RegulatoryRequirement}} compliance.",
        "transition_safety": "Our {{structured_process}} with {{timeframe}} milestones, executive oversight, and {{compliance_framework}} ensures a low-risk transition and continuous performance visibility.",
        "risk_coverage": "Our {{Risk Mitigation Plan}} covers {{RiskCategory}} by {{MitigationAction}}, ensuring compliance with {{Regulation}} and avoiding {{PotentialImpact}}."
    },
    "proof_point": {
        "time_bound_result": "Within {{Timeframe}}, {{Cash Collected}} increased by {{DollarAmount}} and {{KPI}} rose from {{Baseline}} to {{Target}}, demonstrating the impact of {{Solution Component}}.",
        "client_reference": "Our recent engagement with a {{Persona}} delivered {{Result}} ({{Result_Metric}}), demonstrating our ability to {{Capability}}.",
        "validated_capability": "Our **{{Capability}}** has been validated through **{{Evidence}}**, delivering **{{Result}}** for clients like {{Persona}}.",
        "metric_outcome": "Result: {{percentage}}% {{metric}} after {{timeframe}} of {{solution}} implementation."
    },
    "capability_statement": {
        "platform": "Our {{Capability}} platform supports {{Functional_Area}} across {{Languages}} with built-in {{Feature}} to ensure {{Outcome}}.",
        "process_expertise": "Our {{process_expertise}} in {{back_office_functions}} enables {{automation}} and ensures {{compliance}} with {{regulatory_standards}}.",
        "solution_positioning": "Our solution {{capability_placeholder}} so you can {{business_need_placeholder}} without {{pain_point_placeholder}}."
    },
    "cost_transparency": {
        "tiered_pricing": "Our tiered pricing model uses an {{FTEBand}} structure – {{PricePerHour}} per staffed hour – delivering predictable cost as you scale.",
        "inclusions_exclusions": "To recap, the quotation includes {{List_of_Included_Items}} and expressly omits {{List_of_Excluded_Items}} as per your RFP requirements."
    }
}

# Value Statements by Persona
PERSONA_VALUE_STATEMENTS = {
    "top_10_retail_bank": "Dispute resolution cycle reduced from 12 days to 7, keeping you inside Reg E timelines with margin for exceptions.",
    "national_card_issuer": "Fraud losses contained at 3.2 bps while maintaining 94% customer satisfaction on fraud calls.",
    "mortgage_servicer": "Loss mitigation workout completion increased 23%, reducing foreclosure inventory carrying costs.",
    "insurance_carrier": "FNOL cycle time reduced from 48 hours to 6 hours, accelerating claims processing downstream.",
    "payment_processor": "Merchant onboarding SLA compliance at 99.1%, with exception escalation within 4 hours.",
    "wealth_manager": "HNW client retention improved 8 points; service complaints to compliance reduced 62%.",
    "fintech_lender": "Right Party Contact rate of 38% vs. industry average of 22%, with 90-day ramp to full productivity.",
    "data_analytics_provider": "Verification accuracy at 99.7% with average turnaround of 4.2 hours."
}

# Threat/Context Descriptions
THREAT_CONTEXTS = {
    "app_fraud": {
        "title": "Authorized Push Payment (APP) Fraud",
        "stat": "$485M",
        "source": "US losses in 2024 (FinCEN estimates)",
        "context": "Victims willingly initiate transfers under social engineering—traditional fraud rules see clean transactions. Detection shifts to the human interaction layer: call behavior, urgency signals, deviation from established patterns.",
        "commitment": "Agents trained to recognize coercion indicators. Escalation protocol triggers supervisor review for transfers >$10K to new payees."
    },
    "reg_e_surge": {
        "title": "Reg E Dispute Surge Post-Breach",
        "stat": "72-hour",
        "source": "Typical window from breach announcement to 300%+ dispute volume spike",
        "context": "Card issuers face dual pressure: regulatory timelines don't pause, and customer anxiety drives repeat contacts. Unprepared operations see handle times balloon and provisional credit errors spike.",
        "commitment": "Surge capacity agreements in place; 150 cross-trained agents deployable within 48 hours. Provisional credit decisioning scripted to reduce adjudication errors."
    },
    "cfpb_enforcement": {
        "title": "CFPB Enforcement Environment",
        "stat": "$3.7B",
        "source": "Consumer relief ordered in 2024 enforcement actions",
        "context": "Examination focus areas include repeat-call analysis, complaint handling, and debt collection practices. Recordkeeping gaps—not intent—drive most findings.",
        "commitment": "100% call recording with 7-year retention. QA samples exceed CFPB examination protocols. Monthly compliance reporting to client risk team."
    },
    "deepfakes": {
        "title": "Deepfakes & Synthetic Identity",
        "stat": "900%",
        "source": "Growth in deepfake fraud, $40B US losses projected by 2027",
        "context": "Transactions often show no anomaly pre-authorization; fraud reveals itself only at the human touchpoint.",
        "commitment": "Strengthen the human layer where emerging threats increasingly focus. Voice biometrics, behavioral analysis, and escalation protocols for synthetic identity indicators."
    }
}

# Phrases to Use and Avoid
PHRASES_TO_USE = {
    "commitment": "We deliver...",
    "track_record": "Since [year], across [X] sites...",
    "included_value": "What you get with us as a partner...",
    "capability": "[Specific number] agents/locations/clients",
    "qualification": "Contingent on... / Requires joint discovery...",
    "recommendation": "Based on our experience with similar programs...",
    "regulatory_credibility": "Zero regulatory findings in [X] examinations",
    "measurable_outcome": "[Metric] improved from [X] to [Y] over [timeframe]",
    "risk_acknowledgment": "Requires [specific dependency]; typical timeline [X] weeks",
    "audit_readiness": "Documentation audit-ready; last examined [date] by [regulator/auditor]",
    "operational_specificity": "[X] FTE certified in [specific regulation/process]",
    "cost_transparency": "Fully loaded rate of $[X]/hr includes [components]",
    "contingency": "Surge capacity of [X] FTE deployable within [Y] hours"
}

PHRASES_TO_AVOID = {
    "World-class": "Generic, unprovable",
    "Best-in-class": "Same as world-class",
    "Seamless": "Nothing is seamless",
    "Synergy": "Corporate jargon",
    "Leverage": "Overused as verb",
    "Transform/Transformational": "Overused",
    "Holistic": "Vague",
    "End-to-end": "Vague",
    "Robust": "Generic",
    "Solution": "Overused as noun",
    "Partner": "Dilutes meaning when overused",
    "Regulatory expertise": "Vague; every competitor claims this",
    "Customer-centric approach": "Generic; show metrics instead",
    "Flexible solutions": "Meaningless without specifics",
    "Deep bench": "Jargon; state headcount instead",
    "Best practices": "Overused; describe the actual practice",
    "Compliance DNA": "Cliché; cite audit results instead",
    "Trusted advisor": "Self-congratulatory; let track record speak",
    "White-glove service": "Meaningless; define the service level",
    "Skin in the game": "Informal; describe the actual risk-sharing structure",
    "Move the needle": "Jargon; state the metric and target"
}

# Financial Services Metrics That Matter
FINSERV_METRICS = {
    "regulatory": ["Examination findings", "SAR accuracy", "complaint ratios", "CFPB/state AG actions"],
    "fraud": ["Fraud losses (bps)", "false positive rate", "detection-to-action time"],
    "collections": ["RPC rate", "PTP rate", "liquidation rate", "cost-to-collect"],
    "servicing": ["FCR", "AHT", "CSAT/NPS", "escalation rate", "handle time by call type"],
    "compliance": ["QA pass rate", "call monitoring %", "training completion", "audit findings"],
    "operational": ["Attrition", "absenteeism", "speed-to-proficiency", "schedule adherence"],
    "financial": ["Cost per contact", "cost per resolution", "savings vs. baseline"]
}

# Anti-Patterns to Avoid
ANTI_PATTERNS = {
    "regulatory_name_dropping": {
        "bad": "We understand UDAAP, TCPA, FDCPA, FCRA, GLBA, Reg E, Reg Z, TILA, RESPA, ECOA, HMDA, BSA/AML, OFAC, and state-specific requirements.",
        "good": "All agents complete 40-hour regulatory curriculum covering TCPA, FDCPA, and Reg E before production. Annual recertification required. QA scoring includes compliance-weighted criteria (30% of total score).",
        "why": "Listing acronyms signals awareness; describing training, certification, and QA integration signals operational embedding."
    },
    "vague_technology_claims": {
        "bad": "Our proprietary AI-powered platform delivers actionable insights in real time.",
        "good": "Speech analytics flags compliance risk phrases within 2 hours of call completion. Supervisors receive prioritized review queue daily. False positive rate: 12%.",
        "why": "FinServ clients have been burned by vague tech promises. Specificity (latency, accuracy, workflow) builds trust."
    },
    "overpromising_transitions": {
        "bad": "Seamless transition with no disruption to your operations.",
        "good": "Parallel operations for 30 days. Volume migration in 4 tranches (25% weekly). Rollback protocol documented. Historical transitions average 3.2% temporary KPI degradation, recovering by Week 6.",
        "why": "Experienced buyers know transitions have friction. Acknowledging it—with mitigation—is more credible than denial."
    },
    "hiding_pricing": {
        "bad": "Pricing buried on page 47 of a 50-page proposal, in an appendix labeled 'Commercial Terms.'",
        "good": "Pricing summary on page 3, detailed breakdown in appendix with clear cross-reference.",
        "why": "Procurement reviews pricing first. Burying it signals either lack of confidence or attempt to obscure. Neither helps."
    }
}

# Section Architecture Template
SECTION_TEMPLATE = """
# {section_title}

*{framing_statement}*

| {metric_1} | {metric_2} | {metric_3} | {metric_4} |
|------------|------------|------------|------------|
| {value_1}  | {value_2}  | {value_3}  | {value_4}  |

## The Point

{point_explanation}

{supporting_detail}

***Value for {client_name}:** {value_statement}*
"""

# The "1 Plus" Structure Pattern
ONE_PLUS_STRUCTURE = {
    "description": "Lead with prescriptive operational excellence (what the RFP asked for), then position additional value as included benefits.",
    "pattern": [
        "1. We deliver what you asked for [operational baseline]",
        "2. Here's what else you get with us as a partner [included value]",
        "3. No action required from you [framing matters]"
    ],
    "anti_pattern": "Leading with your differentiated value proposition before demonstrating you can execute the basics."
}

# ============================================================================
# RESEARCH GUIDELINES - Critical for MCP + Deep Research integration
# ============================================================================

RESEARCH_GUIDELINES = {
    "priority_hierarchy": {
        "description": "Source priority for all research and content generation",
        "order": [
            {"priority": 1, "source": "User Instructions", "description": "Explicit user requests and constraints always take precedence"},
            {"priority": 2, "source": "RFP Style Guide", "description": "Foundever RFP & Financial Services style guide - THIS IS THE PRIMARY WRITING AUTHORITY"},
            {"priority": 3, "source": "Qdrant Database", "description": "600K+ claims for evidence - BUT evidence goes in appendix references, not inline"},
            {"priority": 4, "source": "External Research", "description": "Web sources - avoid duplicating Foundever.com content"}
        ],
        "critical_directives": [
            "THIS IS AN RFP PROPOSAL - Follow style guide structure religiously",
            "Meta narrative about proof tiers, MCP sources, Qdrant = APPENDIX ONLY",
            "Main proposal body uses practitioner voice with {{placeholders}} for unknowns",
            "Evidence supports claims but is referenced, not displayed with tier badges inline",
            "Write like the PayPal executive summary - specific, metric-backed, human-sounding"
        ]
    },
    "validation_rules": [
        "NEVER make assumptions that cannot be validated with evidence",
        "NEVER create new claims without a source attribution",
        "NEVER invent statistics, metrics, or outcomes",
        "NEVER fabricate numbers to 'fill in' a proposal - use placeholders instead",
        "ALWAYS cite the source: [Qdrant:T2_case_study], [User], [Style Guide], [External:URL]",
        "ALWAYS distinguish between FACT (sourced) and INFERENCE (logical conclusion from facts)",
        "ALWAYS flag when information is MISSING rather than guessing",
        "EVERY statistic MUST have a source - no orphan numbers",
        "IF DATA IS MISSING: Use {{placeholder}} and iterate with user to get real facts"
    ],
    "claim_types": {
        "description": "Not all statements require sources - distinguish between types",
        "needs_source": [
            "Statistics and numbers (X%, X agents, X days)",
            "Comparative claims (better than, leading, fastest)",
            "Outcome assertions (achieved X, delivered Y)",
            "Specific client references or case studies",
            "Industry benchmarks or standards",
            "Regulatory requirements (must have authoritative source)"
        ],
        "no_source_required": [
            "Narrative framing (e.g., 'In today's competitive landscape...')",
            "Logical transitions (e.g., 'This approach enables...')",
            "General principles (e.g., 'Compliance is essential for...')",
            "Future-oriented statements (e.g., 'Our solution will...')",
            "Conditional statements (e.g., 'If implemented, this could...')",
            "Section introductions and conclusions",
            "Value proposition framing (unless it includes specific numbers)"
        ],
        "examples": {
            "needs_source": "Our 2,500 agents achieve 99.2% accuracy [Source: Internal QA]",
            "no_source": "Ensuring regulatory compliance is essential for maintaining customer trust."
        }
    },
    "no_fabrication_policy": {
        "rule": "NEVER fabricate information. If you don't have verified data, use a placeholder.",
        "what_counts_as_fabrication": [
            "Inventing specific numbers (agents, sites, seats, percentages)",
            "Creating statistics that sound plausible but aren't sourced",
            "Extrapolating specific figures from general statements",
            "Filling in details to make a proposal 'complete'",
            "Making up site names, locations, or capacities",
            "Inventing client counts, interaction volumes, or outcomes"
        ],
        "correct_approach": [
            "Use {{placeholder_description}} for missing data",
            "List what information is needed from user",
            "Ask user to provide specific facts",
            "Build narrative structure, leave facts empty",
            "Iterate: 'I need X, Y, Z to complete this section'"
        ],
        "placeholder_format": {
            "numbers": "{{X delivery centers}}",
            "percentages": "{{X%}}",
            "counts": "{{X,XXX agents}}",
            "locations": "{{City, State}}",
            "metrics": "{{metric: description of what's needed}}",
            "outcomes": "{{outcome: specify what result data is needed}}",
            "time": "{{X hours/days/weeks}}",
            "scores": "{{X/10}} or {{X%}}"
        },
        "placeholder_rules": [
            "ALWAYS use double curly braces: {{...}}",
            "Include descriptive text inside: {{X agents trained in TCPA}}",
            "NEVER use bare X without braces in final content",
            "Add [Source: TBD] after placeholders in tables",
            "For unknown sources: {{X%}} [Source: Internal Data]"
        ],
        "forbidden_in_placeholders": [
            "Dollar signs: {{$X.XM}} - NO! Use operational metrics instead",
            "Cost/savings language: {{cost reduction}} - NO!",
            "Price references: {{hourly rate}} - NO!"
        ],
        "iteration_prompt": "To complete this section, I need the following verified information:\n- [List missing facts]\n\nPlease provide these details, or I can leave as placeholders for your team to fill in."
    },
    "rfp_input_handling": {
        "description": "How to handle RFP requirements from client documents",
        "input_types": ["Word Document", "Excel Questions", "PDF RFP", "Email Requirements"],
        "process": [
            "1. Parse requirements from document",
            "2. Categorize by style guide section",
            "3. Identify gaps and ambiguities",
            "4. Generate clarifying questions",
            "5. Map to Qdrant evidence",
            "6. Build response structure with placeholders"
        ],
        "question_triggers": [
            "Ambiguous scope (could be interpreted multiple ways)",
            "Missing critical information (timeline, volume, geography)",
            "Conflicting requirements",
            "Unstated assumptions that affect solution design",
            "Regulatory/compliance implications not specified",
            "Technical integration details missing",
            "Success metrics not defined"
        ],
        "assumption_handling": {
            "rule": "NEVER assume. ALWAYS ask or placeholder.",
            "format": "ASSUMPTION NEEDED: {{description}} - Please confirm or clarify.",
            "track_assumptions": True
        }
    },
    "pricing_restrictions": {
        "rule": "NEVER discuss pricing, costs, or savings - not even as placeholders",
        "absolute_forbidden": [
            "Hourly rates (e.g., $X/hr)",
            "Per-FTE costs",
            "Total contract values",
            "Cost comparisons",
            "Pricing tiers",
            "Rate cards",
            "Budget figures",
            "Cost savings (e.g., 'save $X.XM')",
            "ROI calculations with dollar amounts",
            "ANY placeholder that implies a price: {{$X.XM}}, {{cost}}, {{savings}}"
        ],
        "forbidden_placeholder_patterns": [
            "{{$...", "{{cost...", "{{savings...", "{{price...",
            "{{rate...", "{{budget...", "{{ROI...", "Estimated Cost"
        ],
        "what_to_do_instead": [
            "Focus on OUTCOMES and METRICS (%, time, quality) not costs",
            "Describe VALUE DELIVERED without monetizing it",
            "Use operational metrics: 'reduced AHT by X%' not 'saved $X'",
            "Defer pricing discussions: 'Commercial terms available upon request'"
        ],
        "exception": "Outcome-based pricing may be discussed as a SOLUTION CONCEPT only",
        "outcome_based_framing": [
            "Outcome-based pricing aligns incentives with client success metrics",
            "Performance-based commercial models tie payment to delivered results",
            "Value-based arrangements share risk and reward",
            "Success-fee structures demonstrate confidence in delivery"
        ],
        "if_user_asks_about_pricing": "Redirect to discussing commercial model OPTIONS (fixed, outcome-based, hybrid) without specific numbers. Say: 'Detailed pricing requires scope confirmation - let's discuss commercial model structure.'"
    },
    "solution_approach": {
        "principle": "Iterate on options, don't prescribe solutions",
        "rules": [
            "Present 2-3 solution options rather than a single recommendation",
            "Ask clarifying questions before narrowing scope",
            "Identify tradeoffs explicitly for each option",
            "Let user select approach before detailing implementation",
            "Flag dependencies and assumptions that need user validation"
        ]
    },
    "qdrant_vs_external": {
        "use_qdrant_for": [
            "Foundever-specific capabilities and track record",
            "Case study evidence and outcomes",
            "Proof tier validation (T0-T3)",
            "BPO industry benchmarks already captured",
            "Competitor intelligence already extracted"
        ],
        "use_external_for": [
            "Current market trends not in database (post-extraction date)",
            "Regulatory updates and compliance changes",
            "Client-specific public information",
            "Industry analyst reports not yet ingested",
            "Technology vendor capabilities beyond Foundever"
        ],
        "avoid_external_for": [
            "Foundever.com content (already in Qdrant, causes redundancy)",
            "Generic BPO marketing claims (low value, already captured)",
            "Information that should come from user directly"
        ]
    },
    "client_naming_rules": {
        "ABSOLUTE_RULE": "NEVER name a specific client unless that name was explicitly provided in the user's prompt",
        "what_to_use_instead": [
            "Use persona templates: {{Top-10 Retail Bank}}, {{National Card Issuer}}, etc.",
            "Use descriptors: 'a leading mortgage servicer', 'a top-5 card issuer'",
            "Use anonymized references: 'a Fortune 100 financial services client'"
        ],
        "exceptions": [
            "Client name appears in user's original prompt/RFP text",
            "User explicitly provides client name to use",
            "Referencing publicly available case studies with permission"
        ],
        "in_testimonials": "Use descriptor + date: '— Top 3 Credit Card Issuer, May 2025'",
        "in_examples": "ALWAYS use {{Persona}} variables, never real names"
    },
    "output_formatting_rules": {
        "proposal_body": {
            "description": "Main proposal content follows style guide structure",
            "rules": [
                "Use '1 Plus' structure: operational baseline FIRST, then included value",
                "Every major section ends with '***Value for {{Client}}:** [statement]*'",
                "Practitioner voice throughout - specific numbers, no superlatives",
                "Tables for metrics, leadership, scenarios - easy scanning",
                "{{Placeholders}} for ALL unknown specifics - iterate with user later"
            ],
            "NEVER_in_body": [
                "Proof tier badges [T2_case_study]",
                "MCP tool references",
                "Qdrant source citations",
                "Internal system metadata",
                "Marketing language ('world-class', 'cutting-edge', 'seamless')"
            ]
        },
        "appendix_references": {
            "description": "Supporting evidence and sources go in appendix",
            "what_goes_here": [
                "Evidence sources with proof tiers",
                "Case study details",
                "Compliance certifications with dates",
                "Detailed methodology notes",
                "Data sources and extraction dates"
            ],
            "format": "Appendix A: Evidence Sources\n- [T2] Case study: {{description}}\n- [T3] Third-party: {{award/recognition}}"
        },
        "pitch_suggestions": {
            "description": "Based on trained persona examples, suggest deal-specific approaches",
            "enabled": True,
            "based_on": "FINSERV_PERSONAS value statements and scenario examples",
            "format": "**Pitch Suggestion for {{Persona}}:** [specific, metric-backed approach from training data]",
            "examples": [
                "For {{National Card Issuer}}: Lead with 'Fraud losses contained at 3.2 bps while maintaining 94% customer satisfaction'",
                "For {{Mortgage Servicer}}: Lead with 'Loss mitigation workout completion increased 23%'",
                "For {{FinTech Lender}}: Lead with 'Right Party Contact rate of 38% vs. industry average of 22%'"
            ]
        }
    },
    "claim_attribution_format": {
        "IN_APPENDIX_ONLY": True,
        "qdrant": "[Qdrant:{proof_tier}] {claim}",
        "user": "[User] {claim}",
        "style_guide": "[Style Guide] {principle}",
        "external": "[External:{source_name}] {claim}",
        "inference": "[Inference from {sources}] {conclusion}",
        "unvalidated": "[UNVALIDATED - needs confirmation] {assumption}"
    }
}

# Research mode prompts to prepend to tool outputs
RESEARCH_MODE_HEADER = """
## Research Guidelines Active

**Priority Hierarchy:**
1. User Instructions (highest)
2. Style Guide principles
3. Qdrant evidence (600K claims, proof-tiered)
4. External research (avoid Foundever.com redundancy)

**Rules:**
- No assumptions without validation
- No claims without source attribution
- Present options, don't prescribe solutions
- Flag missing information explicitly

---

"""

# Confidence levels for claims
CLAIM_CONFIDENCE = {
    "validated": {
        "label": "VALIDATED",
        "description": "Claim supported by T2+ evidence or user confirmation",
        "can_assert": True
    },
    "supported": {
        "label": "SUPPORTED",
        "description": "Claim supported by T1 evidence or multiple T0 sources",
        "can_assert": True,
        "qualifier": "Evidence suggests..."
    },
    "inferred": {
        "label": "INFERRED",
        "description": "Logical conclusion from validated facts",
        "can_assert": False,
        "qualifier": "Based on [sources], this suggests..."
    },
    "unvalidated": {
        "label": "UNVALIDATED",
        "description": "Assumption or claim lacking evidence",
        "can_assert": False,
        "qualifier": "This requires confirmation: "
    },
    "missing": {
        "label": "MISSING",
        "description": "Information not available in any source",
        "can_assert": False,
        "qualifier": "No evidence found for: "
    }
}
