from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.db.models import Conversation, Cluster, ClusterMembership, _uuid
from app.models.providers.base import BaseModelProvider
from app.models.router import get_model_router

settings = get_settings()


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _compute_centroid(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return [0.0] * 1536
    arr = np.mean(np.array(vectors), axis=0)
    norm = np.linalg.norm(arr) or 1.0
    unit = arr / norm
    return [round(float(x), 6) for x in unit]


async def _generate_cluster_label(
    provider: BaseModelProvider,
    sample_texts: List[str],
) -> Tuple[str, str]:
    """Generate concise label and description for a cluster of conversations."""
    context = "\n---\n".join(sample_texts[:5])
    prompt = (
        "System: You are an expert photo retrieval UX researcher.\n"
        "Task: Based on these sample user conversations, identify the shared retrieval friction.\n"
        "Return JSON only:\n"
        '{"label": "3-6 word problem title", "description": "1-2 sentence description of the retrieval difficulty"}'
    )

    try:
        res = await provider.classify(text=context, prompt=prompt)
        label = res.get("label", "Photo Retrieval Challenge")
        desc = res.get("description", "Users experiencing difficulty searching their personal photo library.")
        return str(label)[:100], str(desc)[:500]
    except Exception:
        # Fallback heuristic
        first = sample_texts[0].lower() if sample_texts else ""
        if "date" in first or "year" in first or "when" in first:
            return "Temporal Retrieval Friction", "Users struggle to locate photos when exact dates are forgotten."
        elif "screenshot" in first or "receipt" in first:
            return "Screenshot & Document Retrieval", "Difficulty finding screenshots, text documents, or receipts."
        elif "face" in first or "person" in first:
            return "Person & Social Retrieval Failure", "Face recognition or people tag lookup failures in photo library."
        elif "place" in first or "location" in first or "trip" in first:
            return "Spatial & Location Search Difficulty", "Users cannot remember or search by precise geographical locations."
        return "Search Query Mismatch & Ranking", "Search keywords fail to match photo contents or return irrelevant results."


async def run_semantic_clustering(
    db: AsyncSession,
    min_samples: Optional[int] = None,
    epsilon: Optional[float] = None,
    provider: Optional[BaseModelProvider] = None,
) -> Dict[str, Any]:
    """
    Execute semantic clustering over all embedded conversations:
    1. Load embeddings from DB
    2. Run DBSCAN with cosine distance
    3. Generate AI labels and centroids for clusters
    4. Persist clusters and cluster_memberships
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()
    eps = epsilon or settings.cluster_epsilon or 0.3
    min_pts = min_samples or settings.cluster_min_samples or 3

    # 1. Fetch conversations with embeddings
    stmt = (
        select(Conversation)
        .where(Conversation.embedding.isnot(None))
        .where(Conversation.is_relevant != False)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    if len(conversations) < min_pts:
        return {
            "total_conversations": len(conversations),
            "clusters_created": 0,
            "outliers_count": len(conversations),
            "status": "insufficient_data",
        }

    conv_ids = [c.id for c in conversations]
    X = np.array([c.embedding for c in conversations])

    # Compute cosine distance matrix (1 - cosine_similarity)
    # Since embeddings are unit-normalized, cosine_sim = X @ X.T
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_X = X / norms
    similarity_matrix = np.clip(np.dot(normalized_X, normalized_X.T), -1.0, 1.0)
    distance_matrix = np.maximum(0.0, 1.0 - similarity_matrix)

    # 2. Run DBSCAN
    clustering = DBSCAN(eps=eps, min_samples=min_pts, metric="precomputed")
    labels = clustering.fit_predict(distance_matrix)

    unique_labels = set(labels)
    valid_clusters = [l for l in unique_labels if l != -1]

    # Edge Case 7.1 / 7.2: If DBSCAN found no clusters or just 1 cluster with >= 50% outliers, fallback to KMeans
    if len(valid_clusters) < 2 and len(conversations) >= 6:
        n_k = min(5, len(conversations) // 2)
        kmeans = KMeans(n_clusters=n_k, random_state=42, n_init=5)
        labels = kmeans.fit_predict(normalized_X)
        unique_labels = set(labels)
        valid_clusters = [l for l in unique_labels if l != -1]

    # Clear previous active cluster memberships for fresh run
    # (or preserve archived clusters)
    await db.execute(delete(ClusterMembership))
    await db.execute(delete(Cluster).where(Cluster.is_archived == False))
    await db.flush()

    clusters_created = 0
    memberships_created = 0
    outliers_count = int(np.sum(labels == -1))

    for label_idx in valid_clusters:
        member_indices = np.where(labels == label_idx)[0]
        member_convs = [conversations[i] for i in member_indices]
        member_vecs = [conversations[i].embedding for i in member_indices]

        # Centroid
        centroid = _compute_centroid(member_vecs)

        # Sample texts for AI labeling
        sample_texts = [
            f"{c.title or ''}: {c.cleaned_text or c.text or ''}" for c in member_convs[:5]
        ]
        cluster_title, cluster_desc = await _generate_cluster_label(active_provider, sample_texts)

        cluster_id = _uuid()
        cluster_obj = Cluster(
            id=cluster_id,
            label=cluster_title,
            description=cluster_desc,
            member_count=len(member_convs),
            centroid=centroid,
            is_archived=False,
        )
        db.add(cluster_obj)
        await db.flush()
        clusters_created += 1

        for c in member_convs:
            sim = _cosine_similarity(c.embedding, centroid)
            membership = ClusterMembership(
                conversation_id=c.id,
                cluster_id=cluster_id,
                similarity_score=round(sim, 4),
            )
            db.add(membership)
            memberships_created += 1

    await db.commit()

    return {
        "total_conversations": len(conversations),
        "clusters_created": clusters_created,
        "memberships_created": memberships_created,
        "memberships_assigned": memberships_created,
        "outliers_count": outliers_count,
        "status": "success",
    }
