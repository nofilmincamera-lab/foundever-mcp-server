# Foundever AI Competency Evaluation Framework

## Purpose

This document provides a methodology for evaluating Foundever employees' AI tool competency against the RioRock Brand/Solutions taxonomy. It maps the five core competency disciplines to Foundever's operational domains, enabling consistent assessment and development of AI-assisted work capabilities across the organization.

---

## Framework Overview

### The Five Competency Disciplines

| Discipline | Core Question | Foundever Application |
|------------|---------------|----------------------|
| **Task Decomposition → Ghost Notes** | What's missing from this task before AI can help? | Identifying absent client data, regulatory context, or operational constraints before prompting |
| **Quality Judgment → Error Optimization** | How do I deliberately expose errors before they reach the client? | Structured output validation against compliance requirements and SLA metrics |
| **Iterative Refinement → Adaptive Tension** | How do I manage the friction between speed and precision? | C.O.R.E. protocol (Clarify, Optimize, Refine, Execute) for production-grade outputs |
| **Boundary Recognition → Time Horizons** | Is this a 90-day efficiency gain or an 18-month capability erosion? | Investment horizon awareness for AI adoption decisions |
| **Identity Architecture** | What will this make me, not just what will this get me? | Professional development trajectory in an AI-augmented BPO environment |

### Regulatory Foundation

There is no AI exemption to consumer protection law. CFPB, DOJ, FTC, and EEOC issued joint guidance (April 2024) confirming that existing laws apply fully to AI-driven processes. Organizations cannot claim algorithmic complexity as a defense for compliance failures.

**CFPB Circular 2022-03:** Creditors using AI/ML must provide specific and accurate reasons for adverse actions. "The fact that the technology used is too complex, opaque, or new is not a defense."

**CFPB Circular 2023-03:** Boilerplate adverse action forms are prohibited when AI involves non-traditional data. Organizations cannot "simply select the closest, but nevertheless inaccurate, identifiable factors from the checklist."

**OCC Model Risk Management:** AI systems require board oversight, robust validation, and comprehensive documentation. Personnel must understand and explain AI outcomes.

**June 2023 Interagency Guidance:** Third-party AI vendors require lifecycle management including due diligence, contract negotiation, ongoing monitoring, and exit strategies.

---

## Domain-Specific Evaluation Criteria

### Customer Experience Operations

**Buyer Domain Context:** Inbound/outbound customer service, support, retention  
**Key Metrics:** CSAT, NPS, FCR, AHT, Abandonment Rate

**Industry Benchmarks:**
| Metric | Industry Average | World-Class Target |
|--------|-----------------|-------------------|
| First Call Resolution | 69% | 80%+ |
| Average Handle Time | 697 seconds | Context-dependent |
| CSAT | 75-84% | 85%+ |
| Abandonment Rate | 4.41% | Below 3% |

**AI Impact Evidence:** Stanford/NBER research (5,000+ agents, Fortune 500 company) documented +13.8% issues resolved per hour, -9% time per chat, and +1.3% resolution rate with AI assistance—with no significant change in customer satisfaction. Novice agents saw +35% productivity improvement; experienced agents saw minimal gains.

#### Task Decomposition (Ghost Notes)

Corporate databases capture approximately 20% of business-critical information in structured formats. The remaining 80% exists in unstructured data that most AI systems never access. This creates systematic blind spots that only human judgment can address.

| Competency Level | Observable Behavior | Ghost Note Indicators |
|------------------|--------------------|-----------------------|
| **101 - Tool Operation** | Pastes customer inquiry directly into AI, asks "how should I respond?" | Doesn't identify: customer history, account status, prior escalations, regulatory disclosure requirements |
| **201 - Applied Judgment** | Before prompting, checks CRM for interaction history; frames prompt with account context | Identifies missing: sentiment trajectory, retention risk score, compliance flags, callback commitments |
| **301 - System Design** | Builds prompt templates that require agents to input specific context fields before AI generates response | Creates checklists: mandatory context fields, regulatory disclosure triggers, escalation criteria |

**Foundever-Specific Ghost Notes for CX:**
- [ ] Customer tenure and lifetime value tier
- [ ] Active promotions or retention offers available
- [ ] Reg E/Reg Z disclosure triggers (for banking clients)
- [ ] Prior complaint history and resolution status
- [ ] NPS detractor/promoter classification
- [ ] Callback or follow-up commitments from prior interactions

**CFPB Chatbot Risk Categories (June 2023):**
1. UDAAP violations from providing inaccurate information
2. Regulation E and Z failures when chatbots fail to recognize consumers invoking federal rights
3. Privacy and security risks from improper data handling

The CFPB announced (August 2024) it will "identify when the use of automated chatbots or automated artificial intelligence voice recordings is unlawful, including in situations in which customers believe they are speaking with a human being."

#### Quality Judgment (Error Optimization)

Testing of enterprise LLM deployments found that half of all answers contained at least one error, with 90% of errors traced to failures of model instructions rather than retrieval problems. Traditional prompt engineering approaches that iterated over failure cases solved only 2-3 failures because models lack capacity to follow instructions as they get longer.

| Error Category | 101 Detection | 201 Detection | 301 Prevention |
|----------------|---------------|---------------|----------------|
| **Factual inaccuracy** | Catches obvious wrong product names | Verifies pricing, dates, policy details against source | Builds validation rules into workflow |
| **Tone mismatch** | Notices when response "sounds weird" | Evaluates empathy calibration for complaint vs. inquiry | Creates tone guidelines with examples |
| **Compliance gap** | Doesn't detect | Checks for required disclosures | Embeds compliance checkpoints in templates |
| **Context loss** | Doesn't detect | Notices when AI ignores customer history | Designs prompts that enforce context carry-forward |

**Deliberate Failure Exposure Protocol (CX):**
1. Test AI response against known edge case (refund on expired promotion)
2. Check if regulatory disclosure was included without being prompted
3. Verify response doesn't contradict prior commitments in customer record
4. Confirm sentiment match (frustrated customer shouldn't receive upbeat response)

**Consumer Experience Reality Check:** 1 in 5 consumers using AI for customer service report receiving no benefits. AI customer service failure rate is 4x higher than AI use in general. Root cause: organizations deploy AI for cost-cutting rather than problem-solving.

#### Iterative Refinement (Adaptive Tension / C.O.R.E.)

Iterative prompt refinement can boost accuracy by 30%, reduce bias by 25%, and in compliance-focused implementations achieve 25% accuracy improvement with 40% reduction in manual oversight. Recommended threshold: stop iteration when relevance/accuracy exceeds 90%, or at maximum 5 iterations.

**C.O.R.E. Protocol for Customer Response Generation:**

| Phase | Action | AHT Impact | Quality Gate |
|-------|--------|------------|--------------|
| **Clarify** | Identify what the customer actually needs vs. what they stated | +15-30 sec | "Is this a billing question, service issue, or retention risk?" |
| **Optimize** | Select appropriate response framework (empathy-first vs. solution-first) | +10-20 sec | Match framework to sentiment score |
| **Refine** | Iterate AI output for compliance and personalization | +20-45 sec | Disclosure check, name/account verification |
| **Execute** | Deliver response, log interaction classification | -60-90 sec (from manual baseline) | FCR probability assessment |

**Tension Point:** AHT pressure pushes toward single-pass prompting. FCR and CSAT require iteration. The 201 employee manages this tension consciously; the 101 employee optimizes for speed and accepts quality variance.

#### Boundary Recognition (Time Horizons)

Clinicians relying on AI polyp detection saw significant declines in independent skill after just three months. Pilots trained manually but flying with high automation showed "rusty but largely intact" procedural skills but major declines in cognitive skills—failures in situational awareness, planning, and recognizing system failures. The FAA now recommends pilots periodically use manual skills for majority of flights.

| Decision | 90-Day View | 18-Month View | 5-Year View |
|----------|-------------|---------------|-------------|
| "AI handles routine inquiries" | Reduces AHT, improves throughput | Agents lose skill at handling escalations without templates | Team can't function during tool outage |
| "AI drafts all responses for review" | Maintains quality with speed | Agents develop judgment alongside efficiency | Team has both capability and augmentation |
| "AI handles everything, agents just approve" | Maximum efficiency | Skill atrophy, increased escalation rate | Operational fragility, talent exodus |

---

### Collections & Revenue Recovery

**Buyer Domain Context:** First-party and third-party collections, revenue recovery  
**Key Metrics:** RPC Rate, PTP Rate, Liquidation Rate, Cost-to-Collect, Compliance Rate

**Industry Benchmarks:**
| Metric | Industry Mean | Target |
|--------|--------------|--------|
| Right Party Contact Rate | 26% | 35%+ |
| Promise to Pay Rate | 29% | 40%+ |
| First Call Resolution | 42.83% | 55%+ |

Raising RPC, PTP, and FCR rates by just a few percentage points can lead to increased collection rates amounting to millions across a portfolio.

#### Task Decomposition (Ghost Notes)

| Competency Level | Observable Behavior | Ghost Note Indicators |
|------------------|--------------------|-----------------------|
| **101 - Tool Operation** | Asks AI "what should I say to get this person to pay?" | Doesn't identify: payment history, hardship indicators, skip status, state-specific FDCPA requirements |
| **201 - Applied Judgment** | Frames prompt with account status, payment capacity indicators, previous contact outcomes | Identifies missing: propensity-to-pay score, hardship program eligibility, time-barred debt flags |
| **301 - System Design** | Builds compliance-gated prompt flows that prevent FDCPA violations before they occur | Creates: state-specific disclosure libraries, hardship detection triggers, mini-Miranda templates |

**Foundever-Specific Ghost Notes for Collections:**
- [ ] Account age and statute of limitations status by state
- [ ] Prior payment arrangements and compliance with terms
- [ ] Hardship indicators (recent payment pattern changes, partial payments)
- [ ] Consumer consent status (TCPA compliance for outbound)
- [ ] Skip tracing results and contact attempt history
- [ ] Mini-Miranda and state disclosure requirements
- [ ] Client-specific settlement authority and waterfall

**CFPB Collections Guidance (August 2024):** Consumer protection laws apply "not only to the origination of credit but also to servicing and debt collection practices." A firm's decision to use AI tools "can itself be a policy that produces bias prohibited under civil rights laws."

#### Quality Judgment (Error Optimization)

| Error Category | 101 Detection | 201 Detection | 301 Prevention |
|----------------|---------------|---------------|----------------|
| **FDCPA violation** | Doesn't detect | Checks for prohibited language, time-barred acknowledgment | Builds compliance filters into response generation |
| **Settlement authority breach** | Offers unauthorized terms | Verifies against client waterfall before committing | Embeds authority limits in prompt constraints |
| **TCPA risk** | Doesn't consider | Confirms consent before contact method | Designs consent-gated contact flows |
| **Hardship mishandling** | Pushes payment regardless | Routes to hardship program when indicators present | Creates hardship detection scoring |

**Deliberate Failure Exposure Protocol (Collections):**
1. Test AI response with time-barred account (should not acknowledge debt validity)
2. Verify mini-Miranda included on first contact
3. Check settlement offer against client authority matrix
4. Confirm no threats or harassment language in aggressive prompting scenarios
5. Test with consumer who has filed cease-and-desist

**Foundever Evidence:** "Improving cure rate by 26%" and "reducing operational costs by 70%" in collections services. [Source: foundever.com/services/collections/] A 201 employee would verify these metrics apply to comparable portfolio types before citing in client communications.

#### Iterative Refinement (Adaptive Tension / C.O.R.E.)

**C.O.R.E. Protocol for Collections Contact:**

| Phase | Action | RPC Impact | Compliance Gate |
|-------|--------|------------|-----------------|
| **Clarify** | Identify consumer situation (willing/unable vs. unwilling/able) | +10-15 sec | Hardship screen completed |
| **Optimize** | Select negotiation strategy (settlement, plan, skip) | +20-30 sec | Authority verification |
| **Refine** | Iterate offer within authority, document consumer response | +15-30 sec | Disclosure verification |
| **Execute** | Secure commitment or appropriate disposition | -45-60 sec (from manual) | PTP logged with realistic probability |

**Tension Point:** Liquidation pressure vs. compliance exposure. The 201 employee recognizes that aggressive AI-generated scripts may hit short-term targets while creating CFPB risk. The 301 employee designs guardrails that make the aggressive-but-compliant path the default.

#### Boundary Recognition (Time Horizons)

| Decision | 90-Day View | 18-Month View | 5-Year View |
|----------|-------------|---------------|-------------|
| "AI generates all talk-offs and rebuttals" | Higher RPC through consistency | Collectors can't handle novel objections | CFPB action from template violations |
| "AI suggests strategies, collector executes" | Moderate efficiency gain | Collector judgment improves | Regulatory-ready, skill-rich team |
| "AI handles early-stage, humans handle late-stage" | Appropriate segmentation | Clear career progression path | Sustainable talent pipeline |

---

### Financial Crime & Compliance Operations

**Buyer Domain Context:** Fraud, AML, KYC, compliance operations  
**Key Metrics:** Fraud Loss Rate, False Positive Rate, SAR Accuracy, Case Cycle Time

**Industry Benchmarks:**
| Metric | Traditional Systems | AI-Enhanced Target |
|--------|--------------------|--------------------|
| AML False Positive Rate | 90-95% | Below 50% |
| Alert-to-SAR Conversion | 1-5% (rule-based) | 30%+ (human referral standard) |
| Fraud Detection Rate | — | 87-94% |
| Crime Detection (global) | ~2% of flows | Significantly higher with AI calibration |

Global AML compliance costs approximately $274 billion annually. Financial institutions spend over $54 billion per year on transaction monitoring operations—60-80% on labor costs driven by false positive investigation. The financial industry detects only approximately 2% of global financial crime flows despite 10% annual increases in compliance spending.

**AI-Enhanced Results (with proper human oversight):**
- Danske Bank reduced false positives from 99.5% to approximately 40% after ML implementation
- Major card networks reduced false declines by over 30%
- Mastercard's AI detected 15% more incidents with 25% fewer false alarms
- U.S. Treasury prevented $4 billion in fraud/improper payments in FY2024 (up from $652.7 million in FY2023)

#### Task Decomposition (Ghost Notes)

LLMs used in SAR generation "suffer from factual hallucination, limited crime typology alignment, and poor explainability—posing unacceptable risks in compliance-critical domains."

| Competency Level | Observable Behavior | Ghost Note Indicators |
|------------------|--------------------|-----------------------|
| **101 - Tool Operation** | Asks AI "is this transaction suspicious?" with minimal context | Doesn't identify: customer baseline behavior, peer group comparison, geographic risk, PEP status |
| **201 - Applied Judgment** | Frames prompt with transaction pattern, customer profile, alert trigger reason | Identifies missing: source of funds documentation, beneficial ownership, sanctions list status |
| **301 - System Design** | Builds investigation workflows that require specific evidence before disposition | Creates: evidence checklists by alert type, escalation criteria, SAR narrative templates |

**Foundever-Specific Ghost Notes for Financial Crime:**
- [ ] Customer risk rating and rating basis
- [ ] Transaction pattern baseline (velocity, geography, counterparty)
- [ ] Alert trigger reason and rule ID
- [ ] Prior case history and disposition
- [ ] PEP, sanctions, and adverse media screening results
- [ ] Source of funds/wealth documentation status
- [ ] Beneficial ownership chain (for entity accounts)

**SAR Narrative Requirements (FinCEN/FFIEC):**
- Must explain suspicious nature, not just restate fixed-field data
- Must include five essential elements: who, what, when, where, why/how
- Must explain supporting documents
- Filing without complete explanation is a compliance violation

**SEC Enforcement Example (November 2024):** Three broker-dealers received $275,000 in combined civil penalties for SAR deficiencies including omitted customer names, account numbers, transaction specifics, and suspicious pattern descriptions.

#### Quality Judgment (Error Optimization)

| Error Category | 101 Detection | 201 Detection | 301 Prevention |
|----------------|---------------|---------------|----------------|
| **False negative (missed SAR)** | Doesn't detect | Reviews dispositions against policy criteria | Builds mandatory consideration checkpoints |
| **False positive (unnecessary escalation)** | Accepts AI recommendation | Evaluates against peer group behavior | Designs threshold calibration reviews |
| **SAR narrative deficiency** | Doesn't know what's missing | Checks for who/what/when/where/why | Creates narrative templates with required elements |
| **Sanctions miss** | Relies on system screening | Verifies screening coverage and match quality | Embeds manual screening triggers |

**Deliberate Failure Exposure Protocol (Financial Crime):**
1. Test AI case summary against actual SAR filing requirements
2. Verify beneficial ownership analysis is complete (not just stated)
3. Check if AI recommendation considered all alert trigger reasons
4. Test with complex structuring scenario (should not auto-clear)
5. Confirm suspicious activity indicators are documented, not just concluded

**FinCEN Deepfake Alert (November 2024):** Increased suspicious activity reporting involving AI-generated fraud. Red flags include:
- Reverse-image lookups matching GenAI face galleries
- Third-party webcam plugins during verification
- Document metadata inconsistencies
- Lip-sync anomalies in video verification

#### Iterative Refinement (Adaptive Tension / C.O.R.E.)

**C.O.R.E. Protocol for Case Investigation:**

| Phase | Action | Cycle Time Impact | Compliance Gate |
|-------|--------|-------------------|-----------------|
| **Clarify** | Identify alert type and required evidence standard | +10-20 min | Evidence checklist generated |
| **Optimize** | Gather evidence against checklist, identify gaps | +30-60 min | Documentation completeness |
| **Refine** | Iterate case narrative for regulatory defensibility | +15-30 min | SAR narrative review |
| **Execute** | File or document disposition with full audit trail | -60-90 min (from manual) | Supervisor review completed |

**Tension Point:** Case volume vs. SAR quality. The 201 employee recognizes that AI-assisted speed creates false confidence in case quality. The 301 employee designs QA sampling that catches AI-enabled shortcuts.

#### Boundary Recognition (Time Horizons)

| Decision | 90-Day View | 18-Month View | 5-Year View |
|----------|-------------|---------------|-------------|
| "AI generates case dispositions for review" | Faster cycle time, lower cost | Analysts can't write defensible SARs without templates | Regulatory criticism for formulaic filings |
| "AI drafts, analyst validates and revises" | Moderate efficiency | Analyst judgment develops | Regulatory-ready, adaptable team |
| "AI handles Tier 1 alerts, humans handle complex" | Appropriate segmentation | Clear career path, deep expertise at Tier 2/3 | Sustainable investigation capability |

---

## Cross-Domain Evaluation Matrix

### Ghost Notes Completeness by Domain

| Required Context | CX | Collections | Financial Crime | Trust & Safety |
|------------------|----|-----------|--------------------|----------------|
| Customer/account history | ✓ | ✓ | ✓ | ✓ |
| Regulatory disclosure requirements | ✓ | ✓ | ✓ | Varies |
| Prior interaction outcomes | ✓ | ✓ | ✓ | ✓ |
| Risk/propensity scoring | Optional | ✓ | ✓ | ✓ |
| State/jurisdiction-specific rules | Banking clients | ✓ | ✓ | Varies |
| Compliance disposition authority | Escalation only | ✓ | ✓ | ✓ |

### Error Optimization Priority by Domain

| Domain | Highest-Risk Error Type | Detection Difficulty | Consequence Severity |
|--------|------------------------|---------------------|---------------------|
| **CX** | Tone mismatch + compliance gap | Medium | CSAT damage, regulatory exposure |
| **Collections** | FDCPA violation | High | CFPB action, class action |
| **Financial Crime** | False negative (missed SAR) | Very High | BSA/AML violation, criminal liability |
| **Trust & Safety** | Over-moderation / under-moderation | High | User harm, regulatory scrutiny |

### Time Horizon Risk Assessment

AI does not fail like traditional systems. It fails while still functioning. It can drift from its intended purpose. It can generate biased decisions without triggering a single operational alarm. Organizations need recovery metrics beyond RTO/RPO, including "Recovery Fairness Objective" ensuring fallback systems don't introduce bias.

| AI Adoption Pattern | 90-Day Benefit | 18-Month Risk | 5-Year Risk | Recommendation |
|--------------------|----------------|---------------|-------------|----------------|
| Full automation with human approval | Maximum efficiency | Skill atrophy | Operational fragility | Avoid for complex domains |
| AI-assisted with human judgment | Moderate efficiency | Skill development | Sustainable capability | Recommended default |
| AI for Tier 1, human for Tier 2+ | Appropriate segmentation | Clear progression | Career pathway intact | Best for regulated domains |
| No AI (human only) | None | None | Competitive disadvantage | Not sustainable |

---

## Identity Architecture Assessment

### The Core Question

**"What will this make me?"** is distinct from **"What will this get me?"**

At Foundever, this translates to: Will AI adoption create employees who have judgment augmented by tools, or employees who have judgment replaced by tools?

### The Three Illusions of AI Dependency

Research identifies three dangerous illusions created by AI reliance:

1. **Illusion of explanatory depth:** Believing one understands more than one does
2. **Illusion of exploratory breadth:** Believing all possibilities have been considered
3. **Illusion of objectivity:** Failing to recognize AI bias

Experts may believe skills remain sharp because task performance stays high with AI, while remaining unaware of skill erosion occurring beneath the surface.

### Professional Identity Threat Predictors

Three central predictors of AI identity threat in the workplace:

1. **Changes to work:** Fundamental task alteration that makes prior expertise feel irrelevant
2. **Loss of status position:** Devaluation of existing expertise when AI can perform similar functions
3. **AI identity:** Extent to which AI collaboration becomes "indispensable component of themselves"

Experiencing contradictions to professional identity can lead to loss of self-esteem and threat to identity. Junior workers (ages 22-25) in high-AI-exposure jobs have seen employment drop approximately 13%.

### Assessment Criteria

| Indicator | Healthy Trajectory | Concerning Trajectory |
|-----------|-------------------|----------------------|
| **Skill Development** | Employee can perform task without AI, uses AI to enhance | Employee cannot perform task without AI, uses AI as crutch |
| **Error Recognition** | Catches AI errors through domain knowledge | Accepts AI output because "it usually works" |
| **Career Progression** | AI proficiency + domain expertise creates advancement | AI proficiency substitutes for domain expertise |
| **Operational Resilience** | Can function during tool outage | Cannot function during tool outage |
| **Quality Ownership** | Takes responsibility for final output regardless of AI contribution | Attributes errors to "the AI got it wrong" |

### Red Flags by Role Level

Knowledge workers report generative AI makes tasks "seem cognitively easier," but they are ceding problem-solving expertise to the system. Without training, employees risk losing core cognitive skills—from planning and judgment to domain-specific expertise.

| Role Level | Red Flag Behavior | Intervention |
|------------|-------------------|--------------|
| **New Hire (0-6 months)** | Never performs task manually, only with AI | Require manual competency demonstration before AI access |
| **Experienced Agent (6-24 months)** | Quality declines when AI unavailable | Scheduled manual practice, competency refreshers |
| **Senior Agent (2+ years)** | Can't train others without referencing AI | Rebuild foundational knowledge, documentation review |
| **Team Lead** | Evaluates only AI-assisted work, can't assess manual | Leadership development on capability assessment |
| **Manager** | Workforce planning assumes 100% AI availability | Resilience planning, degraded operation procedures |

### The Skill Development Paradox

AI disseminates best practices from top performers to newer agents. An agent with 2-month tenure using AI performs like one with 6-month tenure without AI. But this acceleration may create dependency rather than genuine skill development.

The question for workforce planning: If the AI went down tomorrow, could we continue to serve customers?

---

## Evaluation Scoring Rubric

### Per-Competency Assessment

Each competency is scored 1-5:

| Score | Level | Description |
|-------|-------|-------------|
| 1 | Pre-101 | Does not use AI tools effectively or refuses to engage |
| 2 | 101 - Tool Operation | Can operate tools, gets outputs, follows instructions |
| 3 | 201 Emerging | Shows inconsistent applied judgment, beginning to iterate |
| 4 | 201 - Applied Judgment | Consistently decomposes tasks, validates quality, manages boundaries |
| 5 | 301 - System Design | Designs workflows, templates, and guardrails for others |

### Composite Score Interpretation

| Composite Range | Assessment | Development Priority |
|-----------------|------------|---------------------|
| 5-10 | Foundation building | Basic tool proficiency, supervised use only |
| 11-15 | Active development | Quality judgment training, iteration practice |
| 16-20 | Applied practitioner | Boundary recognition, time horizon awareness |
| 21-25 | Ready for 301 development | System design training, template creation |

### Weighted Scoring by Domain

Different domains weight competencies differently based on risk profile:

| Competency | CX Weight | Collections Weight | Financial Crime Weight |
|------------|-----------|-------------------|------------------------|
| Ghost Notes | 15% | 20% | 25% |
| Error Optimization | 25% | 30% | 35% |
| Adaptive Tension | 25% | 20% | 15% |
| Time Horizons | 15% | 15% | 15% |
| Identity Architecture | 20% | 15% | 10% |

---

## Implementation Notes

### Assessment Frequency

- **New Hires:** Baseline at Day 30, follow-up at Day 90
- **Experienced Staff:** Quarterly evaluation
- **Post-Incident:** Triggered assessment after quality failures involving AI-generated content
- **Tool Changes:** Re-baseline when new AI tools are deployed

### Evidence Collection

Evaluators should collect:
1. Sample AI interactions with annotations (what was prompted, what was accepted, what was revised)
2. Error logs with root cause classification (AI error vs. human error vs. process error)
3. Time-to-proficiency data comparing AI-assisted vs. manual task completion
4. Quality scores segmented by AI involvement level

### Calibration Sessions

Monthly calibration across evaluators to ensure:
- Consistent scoring standards
- Updated ghost note checklists as tools and processes change
- Shared understanding of boundary cases

### AI Maturity Staging

Most organizations operate at Level 1-2. Level 3 remains largely experimental.

| Level | Capability | Current Adoption | 2027 Projection |
|-------|-----------|-----------------|-----------------|
| Level 1: Chatbots | Basic conversation, scripted FAQ | 50%+ | 80-90% |
| Level 2: Reasoners | Human-level problem solving | ~10% | ~50% |
| Level 3: Agents | Fully autonomous handling | <1% | ~50% |

BPOs lead at 70% AI adoption versus 36% for general organizations.

**Implementation Staging:**
- Phase 1 (Weeks 1-4): Silent observation with transcription/analytics only
- Phase 2 (Weeks 5-8): Post-call automation with summaries and CRM updates
- Phase 3 (Weeks 9-16): Live assistance with real-time co-pilots
- Phase 4 (Ongoing): Continuous refinement

ROI benchmarks: $3.50 return per $1 invested on average, with top performers achieving 8x returns. Cost per AI interaction averages $0.20 versus $5.50 for human-only.

---

## Appendix: Foundever Evidence Base

### Available Proof Tiers

| Tier | Count | Description |
|------|-------|-------------|
| T0 - Marketing | 4,401 | Unvalidated marketing claims |
| T1 - Vendor Artifact | 341 | Documented capabilities (solution pages, service descriptions) |
| T2 - Case Study | 88 | Client-specific outcomes with context |
| T3 - Third Party | 170 | External validation (awards, analyst recognition) |

### Third-Party Recognition (T3)

**ISG Provider Lens 2024:** Top Global Leader in Intelligent Agent Experience and Intelligent CX. ISG noted Foundever "brings advanced AI-enabled co-pilots and auto-pilots, AI-driven learning and development initiatives."

**Everest Group PEAK Matrix:** Leader for 12 consecutive years in Americas CXM.

**Frost & Sullivan 2024:** European Company of the Year for Customer Experience Management, citing "sophisticated AI chatbots and automation tools."

**Generative AI Expo 2024:** Product of the Year Award.

### Validated Claims Relevant to AI Competency

From T1+ evidence:
- "53% fewer calls to the contact center" [T1]
- "36% reduced handling time" [T1]
- "15% reduction of costs" [T1]
- "35% improved productivity" [T1]
- "Improving cure rate by 26%" [T1, collections]
- "Reducing operational costs by 70%" [T1, collections]
- "$8.5-10 million savings" from IVR/chatbot deployment [T2, retail case study]
- "90% CSAT" achieved for multilingual hub [T2]
- "127% increase in top performers" from AI-driven coaching [T2]
- "100% compliance certification" maintained for 21-year banking partnership [T2]

### Foundever AI Infrastructure

- **EverGPT:** 24,000+ unique users, 89,000+ conversations, 9,000+ hours saved (September 2024)
- **Barcelona AI Lab:** Global hub for CX AI innovation (opened 2025)
- **R&D Team:** 700-900 engineers and data scientists
- **Strategic Partnerships:** Cognigy (agentic AI), Zenarate (AI training simulation)

### Ghost Note for Evidence Use

When citing Foundever metrics in client-facing materials:
- [ ] Verify proof tier (T0 claims require external validation)
- [ ] Confirm applicability to client context (industry, geography, scale)
- [ ] Check recency (evidence older than 24 months requires refresh)
- [ ] Ensure metric definition matches client understanding
- [ ] Cross-reference against industry benchmarks for credibility
