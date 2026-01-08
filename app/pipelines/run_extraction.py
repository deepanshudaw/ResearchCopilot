
import os
import json
from typing import Dict, Any

from app.agents.extraction_agent import ExtractionAgent
from app.db import get_connection
from app.config import LLM_PROVIDER, GEMINI_MODEL

PROCESSED_DIR = os.path.join("data", "processed")
EXTRACTED_DIR = os.path.join("data", "extracted")

os.makedirs(EXTRACTED_DIR, exist_ok=True)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def already_extracted(output_path: str) -> bool:
    """
    Check whether extraction output already exists.
    This makes the pipeline idempotent.
    """
    return os.path.exists(output_path)

def insert_extraction_into_db(
    paper_id: int,
    arxiv_id: str,
    extraction: dict
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO paper_extractions (
            paper_id,
            arxiv_id,
            model_provider,
            model_name,
            task,
            method,
            datasets_json,
            metrics_json,
            key_results,
            limitations,
            raw_extraction_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            paper_id,
            arxiv_id,
            LLM_PROVIDER,
            GEMINI_MODEL,
            extraction.get("task"),
            extraction.get("method"),
            json.dumps(extraction.get("datasets")),
            json.dumps(extraction.get("metrics")),
            extraction.get("key_results"),
            extraction.get("limitations"),
            json.dumps(extraction),
        ),
    )

    conn.commit()
    conn.close()

def run_extraction():
    agent = ExtractionAgent()

    files = [
        f for f in os.listdir(PROCESSED_DIR)
        if f.endswith(".json")
    ]

    if not files:
        print("[extract] No processed papers found.")
        return

    print(f"[extract] Found {len(files)} processed papers.")

    for filename in files:
        input_path = os.path.join(PROCESSED_DIR, filename)
        output_path = os.path.join(EXTRACTED_DIR, filename)

        if already_extracted(output_path):
            print(f"[extract] Skipping already extracted: {filename}")
            continue

        try:
            paper_json = load_json(input_path)
            print(f"[extract] Extracting from {filename}...")

            extracted = agent.extract(paper_json)

            # Save JSON artifact
            save_json(output_path, extracted)
            print(f"[extract] Saved extraction → {output_path}")

            # Persist to DB 
            paper_id = paper_json.get("paper_id")
            arxiv_id = paper_json.get("arxiv_id")

            insert_extraction_into_db(
                paper_id=paper_id,
                arxiv_id=arxiv_id,
                extraction=extracted,
            )

            print(f"[extract] Inserted extraction into DB for paper_id={paper_id}")

        except Exception as e:
            print(f"[extract] ERROR processing {filename}: {e}")


if __name__ == "__main__":
    run_extraction()