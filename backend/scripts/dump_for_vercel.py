import sqlite3
import json
import os

def dump_data():
    db_path = os.path.join(os.path.dirname(__file__), "..", "local_dev.db")
    if not os.path.exists(db_path):
        print("Database not found:", db_path)
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get sources map
    c.execute("SELECT id, name FROM sources")
    source_map = {r['id']: r['name'] for r in c.fetchall()}

    # Get conversations with analysis
    c.execute("""
        SELECT c.id, c.source_id, c.external_id, c.author_hash, c.text, c.cleaned_text,
               c.created_at, c.url, c.title, c.is_relevant,
               a.primary_intent, a.memory_types, a.retrieval_strategies,
               a.failure_modes, a.pain_points, a.user_goal, a.known_memory,
               a.unknown_memory, a.frustration_level, a.severity, a.confidence,
               a.reasoning_summary
        FROM conversations c
        LEFT JOIN ai_analyses a ON a.conversation_id = c.id
        ORDER BY c.created_at DESC
    """)
    conversations = []
    for r in c.fetchall():
        d = dict(r)
        d['source'] = source_map.get(d['source_id'], 'reddit')
        # Parse json fields
        for k in ['memory_types', 'retrieval_strategies', 'failure_modes', 'pain_points']:
            if d.get(k) and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except:
                    d[k] = [d[k]]
            elif not d.get(k):
                d[k] = []
        conversations.append(d)

    # Get problems
    c.execute("""
        SELECT id, title, statement, taxonomy_categories, frequency, source_count,
               frustration_score, severity_score, growth_rate, cross_source_score,
               evidence_diversity_score, confidence, is_emerging, is_approved,
               user_segments, created_at, updated_at
        FROM problems
    """)
    problems = []
    for r in c.fetchall():
        d = dict(r)
        for k in ['taxonomy_categories', 'user_segments']:
            if d.get(k) and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except:
                    d[k] = [d[k]]
            elif not d.get(k):
                d[k] = []
        problems.append(d)

    # Get clusters
    c.execute("""
        SELECT id, label, description, member_count, is_archived, created_at, updated_at
        FROM clusters
    """)
    clusters = [dict(r) for r in c.fetchall()]

    # Source breakdown
    source_counts = {}
    for conv in conversations:
        src = conv.get("source") or "other"
        source_counts[src] = source_counts.get(src, 0) + 1

    # Output dataset
    dataset = {
        "metadata": {
            "total_conversations": len(conversations),
            "total_problems": len(problems),
            "total_clusters": len(clusters),
            "generated_at": "2026-10-03T19:00:00Z"
        },
        "source_breakdown": source_counts,
        "problems": problems,
        "clusters": clusters,
        "conversations": conversations
    }

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "lib", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "engine_dataset.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f)

    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"Successfully dumped {len(conversations)} conversations and {len(problems)} problems to {out_file} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    dump_data()
