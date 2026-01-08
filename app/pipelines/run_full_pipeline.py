"""
Full pipeline orchestrator.

This wires together:
- arXiv ingestion
- PDF parsing
- extraction
- synthesis
- critic

It is intentionally simple and imperative.
UI layers (Streamlit / CLI) should call this.
"""

from typing import Optional
import os

from app.ingestion.search_papers import search_papers
from app.parsing.parse_all_pdfs import parse_all
from app.pipelines.run_extraction import run_extraction as run_extraction_fn
from app.pipelines.run_synthesis import run as run_synthesis_fn
from app.pipelines.run_critic import run as run_critic_fn


def run_pipeline(
    topic: str,
    max_papers: int = 5,
    run_extraction_stage: bool = True,
    run_synthesis_stage: bool = True,
    run_critic_stage: bool = True,
) -> Optional[str]:
    """
    Run the full research pipeline for a given topic.

    Returns:
        synthesis_path (str) if synthesis ran, else None
    """

    print(f"[pipeline] Starting pipeline for topic='{topic}'")

    # --------------------
    # 1. Ingestion
    # --------------------
    print("[pipeline] Step 1/5: Searching arXiv")
    search_papers(topic, max_results=max_papers)

    # --------------------
    # 2. Parsing
    # --------------------
    print("[pipeline] Step 2/5: Parsing PDFs")
    parse_all()

    # --------------------
    # 3. Extraction
    # --------------------
    if run_extraction_stage:
        print("[pipeline] Step 3/5: Running extraction agent")
        run_extraction_fn()
    else:
        print("[pipeline] Step 3/5: Skipped extraction")

    synthesis_path = None

    # --------------------
    # 4. Synthesis
    # --------------------
    if run_synthesis_stage:
        print("[pipeline] Step 4/5: Running synthesis agent")
        synthesis_path = run_synthesis_fn(topic)
        print(f"[pipeline] Synthesis saved → {synthesis_path}")
    else:
        print("[pipeline] Step 4/5: Skipped synthesis")

    # --------------------
    # 5. Critic
    # --------------------
    if run_critic_stage and synthesis_path:
        print("[pipeline] Step 5/5: Running critic agent")
        run_critic_fn(synthesis_path)
    elif run_critic_stage:
        print("[pipeline] Step 5/5: Skipped critic (no synthesis found)")
    else:
        print("[pipeline] Step 5/5: Skipped critic")

    print("[pipeline] Pipeline completed.")
    return synthesis_path


if __name__ == "__main__":
    # Simple CLI usage for testing
    run_pipeline(
        topic="LLM jailbreak defense",
        max_papers=5,
        run_extraction_stage=True,
        run_synthesis_stage=True,
        run_critic_stage=True,
    )