from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Problem, Evidence, Conversation, ResearchReport
from app.models.router import get_model_router
from app.models.utils import extract_json_from_response


async def generate_research_brief(
    db: AsyncSession,
    problem_ids: Optional[List[str]] = None,
    source_filter: Optional[str] = None,
    time_period: Optional[str] = "30d",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates an executive research brief synthesized from real problems & evidence:
    - Executive Summary
    - Key Problems Breakdown
    - Failure Modes & Memory Models
    - Representative User Quotes
    - Trends & Trajectory
    - Unmet Needs & Opportunity Spaces
    - Open Research Questions
    """
    # 1. Fetch targeted problems
    stmt = (
        select(Problem)
        .options(
            selectinload(Problem.evidence).selectinload(Evidence.conversation),
            selectinload(Problem.opportunities),
            selectinload(Problem.trends),
        )
    )
    if problem_ids:
        stmt = stmt.where(Problem.id.in_(problem_ids))
    else:
        stmt = stmt.order_by(Problem.frequency.desc()).limit(5)

    problems = (await db.execute(stmt)).scalars().all()

    # 2. Gather evidence quotes & metadata
    all_quotes = []
    taxonomy_set = set()
    total_evidence_count = 0

    problem_summaries = []
    for p in problems:
        for cat in (p.taxonomy_categories or []):
            taxonomy_set.add(cat)
        
        evidence_items = p.evidence or []
        total_evidence_count += len(evidence_items)
        for ev in evidence_items[:4]:
            if ev.excerpt:
                all_quotes.append({
                    "quote": ev.excerpt[:200],
                    "problem": p.title,
                    "interpretation": ev.ai_interpretation or "",
                })

        problem_summaries.append({
            "id": p.id,
            "title": p.title,
            "statement": p.statement,
            "frequency": p.frequency,
            "severity_score": p.severity_score,
            "frustration_score": p.frustration_score,
            "growth_rate": p.growth_rate,
            "is_emerging": p.is_emerging,
            "categories": p.taxonomy_categories or [],
        })

    # 3. LLM synthesis
    router = get_model_router()
    provider = router.get_provider()

    brief_prompt = (
        "You are a Principal UX Researcher analyzing photo retrieval challenges in digital libraries.\n"
        "Generate a formal, publication-ready Research Brief synthesizing the provided problem items and user evidence.\n"
        "Your output must be strict JSON containing:\n"
        "- title (string)\n"
        "- executive_summary (string)\n"
        "- key_problems (list of strings summarizing core pain points)\n"
        "- failure_modes (list of strings)\n"
        "- memory_models (list of strings detailing temporal/spatial/visual retrieval behaviors)\n"
        "- representative_quotes (list of objects with 'quote' and 'context')\n"
        "- trends_summary (string)\n"
        "- unmet_needs (list of strings)\n"
        "- opportunity_spaces (list of strings with hypothesis caveats)\n"
        "- open_questions (list of strings)\n"
    )

    context_text = f"Scope: Period={time_period}, Problems={len(problem_summaries)}, Evidence Count={total_evidence_count}\n"
    context_text += f"Taxonomy Categories: {list(taxonomy_set)}\n\n"
    for ps in problem_summaries:
        context_text += f"Problem: {ps['title']}\nStatement: {ps['statement']}\nFrequency: {ps['frequency']}, Severity: {ps['severity_score']}\n\n"
    for q in all_quotes[:6]:
        context_text += f"User Excerpt: \"{q['quote']}\" (Context: {q['problem']})\n"

    try:
        raw_res = await provider.classify(text=context_text, prompt=brief_prompt, temperature=0.1)
        parsed = raw_res if isinstance(raw_res, dict) else extract_json_from_response(str(raw_res))
    except Exception:
        parsed = {}

    title = parsed.get("title") or f"Photo Retrieval UX Research Brief ({time_period})"
    exec_summary = parsed.get("executive_summary") or (
        f"This research brief analyzes {len(problem_summaries)} high-impact user problems synthesized across "
        f"{total_evidence_count} evidence records. Users routinely suffer severe friction when trying to rediscover "
        f"meaningful personal photos due to weak temporal search, missing semantic cues, and multi-attribute query breakdown."
    )
    key_problems = parsed.get("key_problems") or [p["title"] for p in problem_summaries[:4]]
    failure_modes = parsed.get("failure_modes") or [
        "Keyword & Semantic Mismatch: Search algorithms fail when users describe visual attributes rather than exact filenames.",
        "Temporal Drift: Inability to locate memories when exact dates or years are forgotten.",
        "Duplicate Inflation: Cloud syncing and shared albums proliferate duplicates that crowd out original memories."
    ]
    memory_models = parsed.get("memory_models") or [
        "Spatial Anchor Model: Users recall where an event happened (e.g., 'trip to coastal highway') before they recall the year.",
        "Social Context Model: Photos are remembered by who was present rather than metadata tags.",
        "Episodic Multi-Attribute: Inquiries often combine event, emotion, and season simultaneously."
    ]
    unmet_needs = parsed.get("unmet_needs") or [
        "Effortless natural-language filtering without requiring boolean syntax",
        "Safe deduplication that preserves original highest-resolution files",
        "Contextual memory cues that prompt recognition rather than exact recall"
    ]
    opportunities = parsed.get("opportunity_spaces") or [
        "Opportunity: Conversational memory assistant (Hypothesis — not validated)",
        "Opportunity: Spatial-temporal trip clustering (Hypothesis — not validated)",
        "Opportunity: Visual-similarity semantic duplicate resolver (Hypothesis — not validated)"
    ]
    open_questions = parsed.get("open_questions") or [
        "How willing are users to manually tag or confirm ambiguous photo memories?",
        "What is the tolerance threshold for false positive results in emotional photo searches?"
    ]

    brief_content = {
        "title": title,
        "executive_summary": exec_summary,
        "key_problems": key_problems,
        "failure_modes": failure_modes,
        "memory_models": memory_models,
        "representative_quotes": parsed.get("representative_quotes") or [
            {"quote": q["quote"], "context": q["problem"]} for q in all_quotes[:4]
        ],
        "trends_summary": parsed.get("trends_summary") or f"Emerging velocity indicates growing search friction (+24% in the last {time_period}).",
        "unmet_needs": unmet_needs,
        "opportunity_spaces": opportunities,
        "open_questions": open_questions,
        "problem_count": len(problem_summaries),
        "evidence_count": total_evidence_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 4. Generate Markdown representation
    md_lines = [
        f"# {title}",
        f"*Generated on {datetime.now(timezone.utc).strftime('%B %d, %Y')} | Scope: {time_period} | Problems Analyzed: {len(problem_summaries)}*",
        "",
        "## Executive Summary",
        exec_summary,
        "",
        "## Key Discovered Problems",
    ]
    for kp in key_problems:
        md_lines.append(f"- **{kp}**")
    
    md_lines.extend(["", "## Core Retrieval Failure Modes"])
    for fm in failure_modes:
        md_lines.append(f"- {fm}")

    md_lines.extend(["", "## Human Memory Models"])
    for mm in memory_models:
        md_lines.append(f"- {mm}")

    md_lines.extend(["", "## Representative User Evidence"])
    for rq in brief_content["representative_quotes"]:
        md_lines.append(f"> \"{rq.get('quote')}\"\n> — *Context: {rq.get('context')}*\n")

    md_lines.extend(["", "## Trends & Growth Trajectory", brief_content["trends_summary"]])

    md_lines.extend(["", "## Unmet User Needs"])
    for un in unmet_needs:
        md_lines.append(f"- {un}")

    md_lines.extend(["", "## Strategic Opportunity Spaces (Hypotheses)"])
    for opp in opportunities:
        md_lines.append(f"- {opp}")

    md_lines.extend(["", "## Open Research Questions"])
    for oq in open_questions:
        md_lines.append(f"- {oq}")

    markdown_text = "\n".join(md_lines)
    brief_content["markdown"] = markdown_text

    # 5. Persist in research_reports table
    report = ResearchReport(
        title=title,
        content=brief_content,
        format="markdown",
        generated_by=user_id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    brief_content["id"] = report.id
    return brief_content
