import json
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.config import CRITIC_PROVIDER, CRITIC_GEMINI_API_KEY, CRITIC_GEMINI_MODEL


CRITIC_SCHEMA: Dict[str, Any] = {
    "overall_rating_10": "Integer 1-10 rating of synthesis quality",
    "strengths": ["What the synthesis did well (grounding, structure, coverage)"],
    "weaknesses": ["What is weak (vagueness, missed themes, Not specified overuse, noise)"],
    "repairs": [
        {
            "area": "e.g., dominant_tasks / evaluation_methods / gaps",
            "issue": "what's wrong",
            "fix": "how to rewrite it using only provided paper_rollup + extracted fields",
        }
    ],
    "improved_synthesis": "Rewrite the synthesis to be clearer and more abstract WITHOUT adding new facts.",
    "notes_on_hallucination_risk": "Call out any lines that look invented or ungrounded, if any."
}


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_instruction=(
                "You are a rigorous research reviewer. "
                "You will receive a synthesis JSON produced from extracted paper data. "
                "Your job is to critique and improve the synthesis WITHOUT adding new facts. "
                "You may only rephrase, group, abstract, and reorganize using content already present "
                "in the synthesis (especially paper_rollup and evidence). "
                "If something is missing from the synthesis inputs, do not invent it. "
                "Return valid JSON only."
            ),
            provider=CRITIC_PROVIDER,
            gemini_api_key=CRITIC_GEMINI_API_KEY,
            model_name=CRITIC_GEMINI_MODEL,
        )

    def build_prompt(self, synthesis_json: Dict[str, Any]) -> str:
        return (
            "You are given a synthesis JSON.\n"
            "Rules:\n"
            "- Do NOT add any new facts, datasets, metrics, frameworks, or claims.\n"
            "- You MAY: rewrite for clarity, group similar items, abstract to higher-level themes, "
            "remove noise, and improve 'gaps' into concrete research questions IF supported.\n"
            "- If the synthesis contains 'Not specified' but paper_rollup shows specifics, you may lift "
            "those specifics into the improved synthesis.\n\n"
            "Return JSON with this schema:\n"
            f"{json.dumps(CRITIC_SCHEMA, indent=2)}\n\n"
            "INPUT SYNTHESIS JSON:\n"
            f"{json.dumps(synthesis_json, indent=2)}\n\n"
            "Return ONLY valid JSON."
        )

    def critique(self, synthesis_json: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.build_prompt(synthesis_json)
        return self._generate_json(prompt)