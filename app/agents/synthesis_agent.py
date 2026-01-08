import json
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent


SYNTHESIS_SCHEMA: Dict[str, Any] = {
    "scope": {
        "topic": "Topic/query used for the synthesis",
        "num_papers": "Number of papers synthesized",
    },
    "dominant_tasks": [
        "List the most common tasks / problem framings across papers"
    ],
    "dominant_generation_frameworks": [
        "List recurring frameworks/systems/models (if any), grouped by similarity"
    ],
    "dominant_evaluation_methods": [
        "List recurring evaluation approaches (e.g., human eval, GPT judge, benchmarks, rules/keywords, etc.)"
    ],
    "common_datasets_or_benchmarks": [
        "List named datasets/benchmarks that appear frequently"
    ],
    "common_metrics": [
        "List the most common metrics reported"
    ],
    "consensus_findings": [
        "Bullet list of findings that multiple papers support"
    ],
    "notable_disagreements": [
        "Where papers conflict or disagree (methods, claims, results). If none, say Not specified."
    ],
    "gaps_and_open_questions": [
        "What seems missing/underexplored across the set (based strictly on extracted content)"
    ],
    "paper_rollup": [
        {
            "paper_id": "int",
            "arxiv_id": "str",
            "title": "str",
            "task": "str",
            "generation_framework": "str",
            "evaluation_method": "str",
            "metrics": ["list of str"],
            "datasets": ["list of str"],
        }
    ]
}


class SynthesisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_instruction=(
                "You are a careful research synthesis agent. "
                "You will be given structured extractions from multiple papers. "
                "Only use the provided fields. Do not invent datasets, metrics, numbers, or claims. "
                "If something is missing, write 'Not specified'. "
                "Return valid JSON only."
            )
        )

    def build_prompt(self, topic: str, papers: List[Dict[str, Any]]) -> str:
        # Keep input compact but informative.
        # We include evidence snippets if available to reduce hallucinations.
        compact = []
        for p in papers:
            compact.append({
                "paper_id": p.get("paper_id"),
                "arxiv_id": p.get("arxiv_id"),
                "title": p.get("title"),
                "task": p.get("task"),
                "generation_framework": p.get("generation_framework"),
                "evaluation_method": p.get("evaluation_method"),
                "datasets": p.get("datasets", []),
                "metrics": p.get("metrics", []),
                "key_results": p.get("key_results"),
                "limitations": p.get("limitations"),
                "evidence": p.get("evidence", {}),
            })

        return (
            "SYNTHESIS TASK\n"
            f"Topic: {topic}\n\n"
            "You are given structured extractions for multiple papers.\n"
            "Rules:\n"
            "- Do NOT invent anything not present in the inputs.\n"
            "- If a field is missing across papers, use 'Not specified'.\n"
            "- Prefer aggregation: count repeats, group similar items, identify common patterns.\n"
            "- Keep lists concise and non-redundant.\n\n"
            "Output JSON must follow this schema (keys must match):\n"
            f"{json.dumps(SYNTHESIS_SCHEMA, indent=2)}\n\n"
            "INPUT PAPERS (JSON list):\n"
            f"{json.dumps(compact, indent=2)}\n\n"
            "Return ONLY valid JSON."
        )

    def synthesize(self, topic: str, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = self.build_prompt(topic, papers)
        return self._generate_json(prompt)