# Context: AI-Powered Photo Retrieval Discovery Engine

> **Source:** `docs/problem.txt`
> **Generated:** 2026-10-02

---

## 1. Product Overview

Build an AI-powered **Photo Retrieval Discovery Engine** — a **research and product-discovery system** that continuously analyzes publicly available user conversations to transform unstructured feedback into:

- Recurring photo-retrieval problems
- Unmet user needs
- Search/retrieval failure modes
- User intents and behaviors
- Pain points and frustrations
- Emerging problems
- Potential product opportunities
- Evidence supporting each opportunity
- Trends over time

**Core question the system answers:**
> "What are people struggling with when trying to find memories in their photo libraries, why are they struggling, how often does it happen, and what product opportunities could solve those problems?"

---

## 2. Core Problem: The Memory-to-Retrieval Gap

Users remember photos **imperfectly**. They may recall:
- Approximate time, place, people, occasion, object, activity, partial text, or feeling

But often **cannot** recall:
- Exact date, filename, location, person name, album, file type, device, or the right keywords

Traditional search expects **explicit metadata**. This creates a **memory-to-retrieval gap** — users remember the *experience*, while the system expects *metadata*.

---

## 3. Primary Objective

Ingest, process, analyze, cluster, and visualize publicly available conversations about:

> Photo search, photo retrieval, finding old photos, lost memories, forgotten photos, Google Photos/Apple Photos search, photo organization, screenshot/video retrieval, memory retrieval, visual search, and related experiences.

**Output consumers:** Product Managers, UX Researchers, Designers, Search/Relevance Teams, AI/ML Teams, Photo-storage product teams.

---

## 4. Data Sources

### Priority Sources
1. Google Play Store reviews
2. Apple App Store reviews
3. Reddit discussions
4. Google Photos Help / Community discussions
5. Google search-result discussions (where legally accessible)
6. YouTube comments
7. Public social media discussions
8. Public forums
9. Public blog comments / reviews
10. Product review websites

> **Architecture must be source-agnostic.** Use a normalized internal data format so new sources can be added later.

---

## 5. Compliance Requirements

Only collect and process data that is legally and technically permissible. Respect:
- Website terms of service
- API restrictions
- `robots.txt`
- Rate limits
- Privacy requirements
- Copyright limitations
- Platform restrictions

Prefer official APIs. **Do not** bypass authentication, anti-bot systems, CAPTCHAs, or access controls.

---

## 6. Target Users

The primary user is an **internal research/product team** interacting through a **web interface**.

| User | Key Question |
|---|---|
| Product Manager | Most common photo retrieval frustrations? |
| UX Researcher | How do users describe their problem in their own words? |
| Search Engineer | Which query types systematically fail? |
| Designer | What mental models do users have when searching for memories? |
| Leadership | What new opportunity areas are emerging? |

---

## 7. High-Level System Workflow (Pipeline)

```
PUBLIC DATA SOURCES → DATA COLLECTION → RAW DATA STORAGE
→ CLEANING + NORMALIZATION → DUPLICATE DETECTION
→ LANGUAGE / TEXT PROCESSING → AI CLASSIFICATION
→ INTENT EXTRACTION → PAIN-POINT EXTRACTION
→ FAILURE-MODE DETECTION → SEMANTIC CLUSTERING
→ PROBLEM DISCOVERY → TREND DETECTION
→ OPPORTUNITY GENERATION → EVIDENCE + CITATIONS
→ DISCOVERY DASHBOARD
```

---

## 8. Data Collection Layer

Modular ingestion with **per-source connectors** under `/connectors/`:

```
/connectors
    /reddit
    /google-play
    /app-store
    /youtube
    /google-community
    /forums
```

### Minimum Normalized Record Schema
```json
{
  "source": "reddit",
  "source_id": "...",
  "url": "...",
  "author": "...",
  "timestamp": "...",
  "title": "...",
  "text": "...",
  "language": "...",
  "engagement": { "likes": 0, "comments": 0, "shares": 0 },
  "metadata": {}
}
```

Do not retain unnecessary PII.

---

## 9. Data Cleaning

The cleaning pipeline must:
- Remove exact and near-duplicate content
- Remove spam, ads, irrelevant content
- Normalize whitespace and encoding
- Detect language
- Preserve original meaning
- Remove unnecessary HTML/markup
- Identify quoted/automated/low-information content
- Detect potentially sensitive personal information

> **Important:** Do not aggressively remove conversational context — short sentences may contain high-value research signals.

---

## 10. Conversation Understanding

For every relevant conversation, extract:

### A. User Intent
(e.g., find specific photo, find photos of a person, find old family memories, retrieve deleted content, locate receipts/screenshots/memes)

### B. Retrieval Strategy
(e.g., date search, location, person, keyword, natural-language description, manual scrolling, OCR, filename, folder)

### C. Failure Reason
(e.g., unknown date/location, synonym mismatch, object/person not recognized, OCR failure, poor ranking, metadata the user doesn't remember, mixed memories)

---

## 11. Memory-Based Retrieval Analysis *(Most Important Capability)*

The system identifies where:
```
WHAT USER REMEMBERS  ≠  WHAT SEARCH SYSTEM REQUIRES
```

For each conversation, extract a structured **memory retrieval scenario**:
- **Known memory:** event, scene, people, approximate period
- **Unknown:** exact date, exact location
- **Potential retrieval challenge:** semantic/contextual memory vs. metadata memory

---

## 12. User Mental Model Extraction

Identify how users naturally think about memories across these dimensions (first-class data fields):

| Dimension | Example |
|---|---|
| Temporal | "I think it was sometime around 2018." |
| Spatial | "It was from our Goa trip." |
| Social | "Me and my college friends." |
| Visual | "There was a red car in the background." |
| Event | "The day we graduated." |
| Text | "I remember there was a sign saying..." |
| Emotional | "This was the photo from my first job." |
| Contextual | "During the trip when we stayed at that resort." |

---

## 13. Retrieval Problem Taxonomy

Start with these categories (dynamic — AI should evolve the taxonomy):

```
Temporal Retrieval          Location Retrieval
Person Retrieval            Object Retrieval
Event Retrieval             Semantic Retrieval
Visual Retrieval            Text/OCR Retrieval
Screenshot Retrieval        Video Retrieval
Document Retrieval          Downloaded Media Retrieval
Cross-Source Retrieval      Deleted/Archived Retrieval
Album/Organization Problems Search Query Formulation Problems
Ranking/Relevance Problems  Privacy/Permission Constraints
Other
```

The AI should: assign existing categories, detect emerging ones, propose new ones, merge overlapping categories, and split broad ones. **Taxonomy must evolve based on evidence.**

---

## 14. AI Analysis Pipeline

Use an LLM layer (model-provider interchangeable: OpenAI GPT, Claude, Gemini, local/OSS models).

**Per-record structured JSON output:**
```json
{
  "relevance": 0.94,
  "primary_intent": "find_specific_photo",
  "memory_type": ["event", "location", "social"],
  "retrieval_strategy": ["keyword_search", "manual_scrolling"],
  "failure_modes": ["unknown_date", "semantic_search_failure"],
  "pain_points": ["cannot remember exact date", "too many irrelevant results"],
  "user_goal": "Find a specific photo from a college trip",
  "frustration_level": 0.82,
  "severity": 0.71,
  "confidence": 0.91
}
```

---

## 15. Semantic Clustering

Use **embeddings / vector search** to group semantically similar conversations (not just keyword matching).

Example cluster — all these may express the same problem:
> "I can't remember when I took this."
> "I have no idea what year this photo is from."
> "I know the picture but not the date."
> "I wish I could search by approximate time."

**Problem:** *Retrieval when exact date is unknown.*

UI must allow researchers to inspect individual conversations within each cluster.

---

## 16. Problem Discovery

For each discovered problem, generate:

| Field | Description |
|---|---|
| **Problem title** | e.g., "Users struggle to find memories when they remember the story but not the date." |
| **Problem statement** | Concise description of the underlying difficulty |
| **Evidence** | Links to supporting conversations |
| **Frequency** | Number of relevant conversations |
| **Source diversity** | Number of different platforms |
| **Recurrence** | How consistently it appears over time |
| **User severity** | Estimated frustration/impact |
| **User segments** | e.g., parents, travelers, students (only with sufficient evidence) |
| **Example queries** | What users actually attempted |

---

## 17. Opportunity Discovery

Distinguish clearly between:
```
Observed problem → Underlying user need → Potential opportunity → Possible solution hypothesis
```

**Example:**
- **Observed problem:** Users remember an event but not the date.
- **Underlying need:** Search using approximate contextual memory.
- **Opportunity:** Memory-first photo retrieval.
- **Hypothesis:** Allow natural-language searches describing a remembered event; infer candidate dates, people, places, objects, and visual context.

> All solution hypotheses must be **explicitly labeled as hypotheses**, not validated facts.

---

## 18. Evidence-Based Insights

Every AI-generated insight must trace back to source evidence:
```
Insight → Supporting conversations → Source → URL → Date → Relevant excerpt → AI interpretation → Confidence
```
Researchers must be able to click an insight and inspect original evidence. No unsupported conclusions.

---

## 19. Trend Detection

Analyze changes over time (7 days / 30 days / 90 days / 6 months / 1 year / custom period):
- Problems increasing over the last 6 months
- Newly emerging retrieval behaviors
- Growing complaints about video search
- Emerging use of AI-based search
- Changing terminology
- Recurring seasonal problems

---

## 20. Cross-Platform Comparison

Detect the same underlying problem expressed differently across platforms:
- Reddit: "I can't find this photo even though I know what it looks like."
- App Store: "Search doesn't understand descriptions."
- Google Community: "How do I find a photo when I don't remember the date?"

Display: Underlying problem → Reddit evidence / App Store evidence / Community evidence / YouTube evidence.

---

## 21. Query Mining

Extract actual search queries users attempted. Analyze:
- Query length and structure
- Entities: objects, people, locations
- Temporal expressions
- Events, uncertainty, synonyms, ambiguity

Identify natural-language patterns for memory-based searches.

---

## 22. Query Failure Analysis

Classify failure modes:
```
Query formulation problem    Intent understanding problem
Entity recognition problem   Temporal reasoning problem
Location reasoning problem   Visual recognition problem
OCR problem                  Ranking problem
Recall problem               Precision problem
User expectation problem
```

---

## 23. Insight Scoring

Transparent, multi-dimensional scoring (no black-box ranking):
```
Frequency | Cross-source recurrence | Growth | Severity | Evidence diversity | Confidence
```

Display individual dimensions so researchers understand why something surfaced.

---

## 24. Discovery Dashboard — Home Screen

| Section | Contents |
|---|---|
| **Overview** | Total conversations, relevant conversations, sources, problems discovered, emerging problems, user intents, retrieval failure modes |
| **Top Problem Areas** | Problem + frequency + growth + sources + example evidence |
| **Emerging Problems** | Rapidly increasing problems |
| **Memory Dimensions** | Date, Location, People, Events, Objects, Text, Context, Emotion (visualized) |
| **Retrieval Failures** | Unknown date, poor semantic understanding, poor ranking, OCR issues, video retrieval, etc. |

---

## 25. Problem Detail Page

For each problem, show:
- Frequency, sources, growth trend
- Underlying user need
- Common memory signals (Event, People, Location, Approximate time)
- Typical queries
- Failure modes
- Evidence (linked conversations)
- Potential opportunities
- AI confidence

---

## 26. Research Evidence Viewer

Each evidence card shows:
- Source, date, title, original text, URL
- Extracted intent, pain point, memory dimensions
- Cluster, AI confidence

With **"Show original context"** option to view surrounding text.

---

## 27. Search the Research Dataset

Natural-language search interface over the research dataset:
> "Show conversations where users couldn't find a photo because they didn't remember the date."
> "Find problems involving screenshots."
> "What retrieval problems are increasing among users discussing old family photos?"

---

## 28. AI Research Assistant

An in-dashboard AI assistant that answers questions using **only** the collected dataset and source evidence.

Example queries:
> - What are the most common reasons people fail to find old photos?
> - What types of memory do people rely on when exact metadata is unavailable?
> - What new retrieval problems appeared in the last six months?
> - Give me 10 unmet needs related to forgotten photos.

Every factual answer must include supporting evidence links and clearly distinguish **Evidence** vs. **Interpretation** vs. **Hypothesis**.

---

## 29. Research Brief Generator

Generate structured research reports containing:
- Executive Summary
- Key User Problems
- Top Retrieval Failure Modes
- Memory Models
- Representative User Quotes
- Cross-Platform Evidence
- Emerging Trends
- Unmet Needs
- Opportunity Areas
- Open Questions / Research Gaps

**Export formats:** Markdown, PDF, CSV, JSON.

---

## 30. Human-in-the-Loop Review

Researchers can:
- Approve / correct classification
- Merge / split clusters
- Rename problems
- Mark insights or evidence as invalid/irrelevant
- Modify taxonomy
- Add notes / bookmark insights

Human corrections are stored and used to improve future classification.

---

## 31. Feedback Learning Loop

```
AI Classification → Human Review → Correction → Stored Feedback → Prompt/Model Improvement → Better Future Classification
```

Track corrections as evaluation data (not automatic retraining from tiny samples).

---

## 32. Architecture

```
Frontend
    ↓
API Layer
    ↓
Research Orchestration Layer
    ↓
 ┌──────────────────┬──────────────────┐
Data Connectors    AI Analysis        Search
    ↓                   ↓                ↓
Raw Storage     LLM + Embeddings    Vector DB
    ↓                   ↓                ↓
 └──────────────────┴──────────────────┘
                    ↓
              Insight Store
                    ↓
               Dashboard
```

### Technology Stack

| Layer | Options |
|---|---|
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS |
| **Backend** | Python / FastAPI  or  Node.js / TypeScript |
| **Database** | PostgreSQL |
| **Vector Search** | pgvector (preferred for MVP), Pinecone, Weaviate |
| **AI** | Model abstraction layer (OpenAI, Anthropic, Google, local) |
| **Background Jobs** | Celery, Temporal, BullMQ, n8n |

---

## 33. Database Entities

```
Source | Conversation | Author | Topic | Intent | MemoryDimension | FailureMode
Problem | Opportunity | Cluster | Evidence | AIAnalysis | Trend | HumanReview | ResearchReport
```

**Key relationships:**
- `Conversation → Intent → Memory Dimension → Failure Mode → Cluster → Problem`
- `Problem → Evidence → Trends → Opportunities`

---

## 34. Deduplication

The same discussion may be reposted, quoted, syndicated, cross-posted, or summarized. Use:
- **Exact matching** for identical text
- **Semantic similarity** for paraphrases/reposts

Label records as: `original | duplicate | possible duplicate | cross-post`

Do not artificially inflate problem frequency.

---

## 35. Source Weighting & Evidence Limitations

Distinguish clearly:
- Raw volume
- Unique conversation count
- Source distribution
- Approximate evidence diversity

Include an **Evidence Limitations** section in the dashboard. Do not treat the dataset as statistically representative of all photo users.

---

## 36. Privacy

Avoid storing unnecessary usernames, emails, profile information, or personal identifiers. Use **anonymous source identifiers** where possible. Provide configurable data-retention controls.

---

## 37. Multilingual Support

```
Original Language → Language Detection → Analysis → Normalized Semantic Representation
```

Do not rely on simple keyword matching for multilingual data. Design for future language expansion.

---

## 38. Explainability

Every AI insight should answer *"Why was this classified this way?"* by showing:
- Detected signals, supporting text, confidence
- Related conversations, cluster membership, reasoning summary

No private chain-of-thought; provide concise, auditable, evidence-based explanations.

---

## 39. Core Product Principle: Problems Before Solutions

> Do not force conversations into predefined solutions.

- Bad: "Users want AI search."
- Better: "Users frequently describe photos through events, relationships, approximate dates, and visual context rather than exact searchable metadata." — *then* derive opportunities.

---

## 40. Emerging-Problem Detection

Detect problems that are: new, rapidly growing, multi-source, high-frustration, and poorly represented in the taxonomy.

Periodically generate:
```
Potential New Problem: Why it is new | Evidence | First observed | Growth | Sources | Confidence
```

A **human must approve** before it becomes a permanent taxonomy category.

---

## 41. "Unknown Unknowns" Capability

Actively search for problems researchers did not define beforehand using:
- Unsupervised clustering
- Embeddings + topic discovery
- Anomaly detection
- Semantic outlier detection
- Temporal change detection

Periodically surface: *"We are seeing a recurring pattern that does not fit the current taxonomy."*

> This is a **core feature**, not optional.

---

## 42. End-to-End Example

**Input:**
> "I've been trying to find a photo from my first college trip. I remember it was near a waterfall and I'm standing with three of my friends. I don't remember the year though. Google Photos keeps showing random waterfall pictures."

**Extracted:**
- **Intent:** Find a specific photo
- **Memory dimensions:** Event, Location/context, People, Visual scene
- **Known:** College trip, Waterfall, Three friends
- **Unknown:** Exact date/year
- **Attempted strategy:** Semantic description
- **Failure:** Poor contextual retrieval, poor ranking, date uncertainty
- **Underlying need:** Retrieve a memory using incomplete contextual recollection
- **Potential opportunity:** Memory-first contextual retrieval

---

## 43. MVP Scope

### MVP Data Sources
- Reddit
- Google Play reviews
- App Store reviews
- Google Photos Community

### MVP Capabilities (16 features)
1. Data ingestion
2. Normalization
3. Deduplication
4. Relevance classification
5. Intent extraction
6. Memory-dimension extraction
7. Failure-mode extraction
8. Embedding generation
9. Semantic clustering
10. Problem generation
11. Evidence linking
12. Trend analysis
13. Search
14. Dashboard
15. AI research assistant
16. Human review

---

## 44. Dashboard MVP — Pages

| Page | Content |
|---|---|
| 1 — Overview | Conversations analyzed, relevant conversations, source distribution, problem count, emerging problems, recent trends |
| 2 — Problems | Searchable/filterable list of discovered problems |
| 3 — Problem Detail | Evidence + patterns + trends + opportunities |
| 4 — Conversations | Raw conversations with AI annotations |
| 5 — Trends | Time-based analysis |
| 6 — Explore | Natural-language research assistant |

---

## 45. Filters

Allow filtering by: source, date range, topic, intent, memory type, failure mode, confidence, problem, language, trend status.

---

## 46. Technical Requirements

The application must be: modular, scalable, observable, testable, secure, API-driven, model-provider agnostic.

Implement: structured logging, retry logic, rate-limit handling, job status tracking, ingestion/AI processing monitoring, error reporting.

Long-running data-processing jobs **must run asynchronously**.

---

## 47. AI Cost Management

Implement: batching, caching, deduplication before LLM processing, model routing, configurable models/analysis depth, embedding reuse, prompt versioning.

**Cost-efficient routing:**
```
Cheap model → Relevance filtering → Expensive model → Deep problem extraction
```

Do not send irrelevant content to expensive models.

---

## 48. Prompt Versioning

Store the AI prompt version used for each analysis (e.g., `"photo-retrieval-v1.3"`). This enables future reprocessing and evaluation.

---

## 49. Evaluation System

Maintain a manually labeled benchmark dataset. Evaluate:
- Relevance accuracy
- Intent accuracy
- Failure-mode accuracy
- Clustering quality
- Problem extraction quality
- Evidence grounding
- Hallucination rate

Expose an **internal evaluation page** showing model performance.

---

## 50. API Design

```
POST /ingest
GET  /conversations
GET  /problems
GET  /problems/:id
GET  /clusters
GET  /trends
GET  /evidence/:id
POST /reviews
POST /research/query
POST /reports
```

Use clean API contracts with full documentation.

---

## 51. Research Query API

**Input:**
```json
{ "query": "Why do users struggle to find photos when they don't remember the date?" }
```

**Output:**
```json
{
  "answer": "...",
  "evidence": [
    { "conversation_id": "...", "source": "reddit", "url": "...", "excerpt": "..." }
  ],
  "problems": [],
  "confidence": 0.89
}
```

All answers grounded in the internal research dataset.

---

## 52. Frontend UX

Design as a modern **AI research product**, not an enterprise analytics dashboard.

Prioritize:
- Clean information hierarchy
- Readable evidence
- Fast filtering
- Visual clustering
- Interactive exploration
- Easy navigation from insight to evidence
- Minimal unnecessary decoration

> Most important UI element: **the user evidence and discovered problem.**

---

## 53. Seed / Demo Dataset

Create a small demo dataset demonstrating:
- Different intents, memory types, failure modes
- Multiple clusters
- Trends and emerging problems
- Evidence chains

Clearly label all synthetic data as **DEMO DATA**. Do not represent it as real user evidence.

---

## 54. Security

Implement: authentication, role-based access, protected APIs, environment-variable secrets, no API keys in frontend, secure database access.

**Roles:** Admin | Researcher | Viewer

---

## 55. Configuration

Make configurable without code changes:
```
AI provider / AI model / embedding model / batch size / crawler limits / rate limits /
retention period / similarity thresholds / clustering thresholds / confidence thresholds / analysis frequency
```

---

## 56. Future Extensibility

Architecture should support future data sources:
- Browser search behavior
- Anonymized product telemetry
- Support tickets
- Customer interviews
- Survey responses
- Internal research / direct user feedback
- Search-query logs
- Experiment results

Same research schema should combine all sources.

---

## 57. Final Product Goal

A researcher opens the application and goes from:
```
Millions of unstructured conversations
→ "What are users struggling with?"
→ Discovered problem
→ Underlying user need
→ Evidence
→ User behavior
→ Failure mode
→ Emerging trend
→ Opportunity hypothesis
```

The product is an **AI-powered continuous discovery engine for photo retrieval**: turning scattered user conversations into structured, evidence-backed insights for future photo-search and memory-retrieval products.

---

## 58. Build Instructions

Build a **working full-stack web application** (not a prototype or static mockup):

1. Complete application architecture
2. Backend + database
3. Frontend dashboard
4. Ingestion pipeline abstraction
5. AI analysis with configurable LLM providers
6. Embeddings + semantic search
7. Clustering + problem discovery
8. Evidence traceability
9. Human review workflow
10. Trend detection
11. Research assistant
12. Seed with clearly labeled demo data
13. Authentication + basic roles
14. Automated tests for critical workflows
15. README + setup instructions
16. Environment variables for all secrets
17. Runnable locally with a simple setup process

> When a source requires unavailable API access, create the connector interface with a mock/demo implementation. Do **not** hard-code fake production behavior.

---

## 59. Definition of Done

MVP is complete when a user can:

1. Load/import conversation data
2. Process the data with AI
3. Search the dataset semantically
4. See identified user intents
5. See memory dimensions
6. See retrieval failure modes
7. See automatically generated problem clusters
8. Open a problem
9. Trace the problem back to evidence
10. Explore trends
11. Discover emerging problem areas
12. Ask the AI research assistant questions
13. Review/correct AI classifications
14. Generate a research brief

**Complete loop:** Data → Understanding → Clustering → Problem Discovery → Evidence → Research Insight → Opportunity.
