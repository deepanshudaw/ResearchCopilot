"""
Synthesis stage runner.

Reads paper extractions from SQLite for a given topic, runs the SynthesisAgent,
and saves a synthesis JSON artifact to data/synthesis/.

Returns the saved synthesis path (string) or "" if no matching extractions exist.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from app.db import get_connection
from app.agents.synthesis_agent import SynthesisAgent

SYNTHESIS_DIR = os.path.join("data", "synthesis")
os.makedirs(SYNTHESIS_DIR, exist_ok=True)


def fetch_extractions_for_topic(topic: str) -> List[Dict[str, Any]]:
    """
    Fetch extractions joined with paper metadata for a topic.
    Uses partial, case-insensitive matching so 'LLM jailbreak' matches
    'LLM jailbreak defense', etc.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            p.id as paper_id,
            p.arxiv_id as arxiv_id,
            p.title as title,
            p.topic as topic,
            e.task as task,
            e.model_provider as model_provider,
            e.model_name as model_name,
            e.raw_extraction_json as extraction_json,
            e.extracted_at as extracted_at
        FROM paper_extractions e
        JOIN papers p ON p.id = e.paper_id
        WHERE lower(p.topic) LIKE lower(?)
        ORDER BY p.id ASC, e.id ASC
        """,
        (f"%{topic}%",),
    )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()

    out: List[Dict[str, Any]] = []
    for r in rows:
        row = dict(zip(cols, r))
        # extraction_json may be stored as TEXT; normalize to dict if possible
        ej = row.get("extraction_json")
        if isinstance(ej, str) and ej.strip():
            try:
                row["extraction_json"] = json.loads(ej)
            except json.JSONDecodeError:
                # Keep raw string if it isn't valid JSON
                row["extraction_json"] = ej
        out.append(row)

    return out


def list_available_topics() -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT topic
        FROM papers
        WHERE topic IS NOT NULL AND trim(topic) != ''
        ORDER BY topic
        """
    )
    topics = [r[0] for r in cur.fetchall()]
    conn.close()
    return topics


def run(topic: str) -> str:
    papers = fetch_extractions_for_topic(topic)

    if not papers:
        print(f"[synth] No extractions found in DB for topic~={topic!r} (partial, case-insensitive match).")
        topics = list_available_topics()
        if topics:
            preview = topics[:20]
            print("[synth] Available topics in DB (first 20):")
            for t in preview:
                print(f"  - {t}")
            if len(topics) > 20:
                print(f"[synth] ...and {len(topics) - 20} more.")
        else:
            print("[synth] No topics found in papers table.")
        print("[synth] Tip: run `sqlite3 research.db \"SELECT DISTINCT topic FROM papers;\"`")
        return ""

    print(f"[synth] Found {len(papers)} extractions for topic~={topic!r}")

    agent = SynthesisAgent()
    synthesis: Dict[str, Any] = agent.synthesize(topic=topic, papers=papers)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in topic).strip("_")
    out_path = os.path.join(SYNTHESIS_DIR, f"synthesis_{safe_topic}_{ts}.json")

    with open(out_path, "w") as f:
        json.dump(synthesis, f, indent=2)

    print(f"[synth] Saved synthesis → {out_path}")
    return out_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.pipelines.run_synthesis \"<topic>\"")
        raise SystemExit(1)

    run(sys.argv[1])