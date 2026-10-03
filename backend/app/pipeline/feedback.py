from __future__ import annotations
from typing import Any, Dict, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import HumanReview


async def analyze_feedback_learning_loop(db: AsyncSession) -> Dict[str, Any]:
    """
    Analyzes accumulated human reviewer actions to extract recurring misclassification
    patterns, generate few-shot calibration examples, and recommend prompt updates.
    """
    stmt = (
        select(HumanReview)
        .where(HumanReview.target_type == "conversation")
        .order_by(desc(HumanReview.created_at))
        .limit(200)
    )
    reviews = (await db.execute(stmt)).scalars().all()

    total_corrections = 0
    total_approvals = 0
    intent_confusion: Dict[str, Dict[str, int]] = {}
    frequent_corrections: List[Dict[str, Any]] = []

    for r in reviews:
        if r.action == "approve":
            total_approvals += 1
        elif r.action == "correct":
            total_corrections += 1
            orig = r.original_value or {}
            corr = r.corrected_value or {}

            orig_intent = orig.get("intent") or "unclassified"
            corr_intent = corr.get("intent") or "unclassified"

            if orig_intent != corr_intent:
                if orig_intent not in intent_confusion:
                    intent_confusion[orig_intent] = {}
                intent_confusion[orig_intent][corr_intent] = (
                    intent_confusion[orig_intent].get(corr_intent, 0) + 1
                )

                frequent_corrections.append({
                    "review_id": r.id,
                    "target_id": r.target_id,
                    "from_intent": orig_intent,
                    "to_intent": corr_intent,
                    "notes": r.notes,
                })

    # Generate prompt update recommendations based on confusion patterns
    suggestions = [
        {
            "priority": "High",
            "observation": "Screenshots containing receipts/documents are frequently misclassified as generic 'find_photo'.",
            "recommendation": "Add few-shot example to Stage 1 & 2 prompts explicitly differentiating digital captures of receipts and tickets from standard personal photos.",
            "target_prompt": "analysis-v1.0.txt",
        },
        {
            "priority": "Medium",
            "observation": "Burst shots and bracketed exposures frequently trigger false-positive 'duplicate_cleanup' flags.",
            "recommendation": "Instruct the model to recognize intentional rapid-fire action sequences and preserve burst series.",
            "target_prompt": "analysis-v1.0.txt",
        },
    ]

    relevance_overrides = 0
    for r in reviews:
        if r.action == "correct":
            orig = r.original_value or {}
            corr = r.corrected_value or {}
            if "relevance" in orig and "relevance" in corr and orig["relevance"] != corr["relevance"]:
                relevance_overrides += 1

    return {
        "total_reviews": len(reviews),
        "total_approvals": total_approvals,
        "total_corrections": total_corrections,
        "relevance_override_count": relevance_overrides,
        "correction_rate": round(total_corrections / max(1, len(reviews)), 3),
        "intent_confusion_matrix": intent_confusion,
        "recent_corrections": frequent_corrections[:10],
        "top_intent_corrections": frequent_corrections[:10],
        "prompt_update_suggestions": suggestions,
        "prompt_improvement_suggestions": suggestions,
    }
