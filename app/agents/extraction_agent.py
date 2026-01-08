import json
from typing import Dict, Any

from app.agents.base_agent import BaseAgent


EXTRACTION_SCHEMA = {
    "task": "What problem does this paper try to solve?",
    "method": "What is the core method or approach proposed?",
    "datasets": "Which datasets are used? Return a list.",
    "metrics": "Which evaluation metrics are reported? Return a list.",
    "key_results": "What are the main quantitative or qualitative results?",
    "limitations": "What limitations or failure cases are mentioned?"
}


class ExtractionAgent(BaseAgent):
    """
    Agent responsible for extracting structured research information
    from a single processed paper (sections JSON).
    """

    def __init__(self):
        super().__init__(
            system_instruction=(
                "You are a precise research assistant. "
                "Extract factual information from academic papers. "
                "Do not hallucinate. If information is missing, say 'Not specified'. "
                "Return valid JSON only."
            )
        )

    def build_prompt(self, paper_json: Dict[str, Any]) -> str:
        """
        Build the extraction prompt given a processed paper JSON.
        """
        sections = paper_json.get("sections", {})

        sections_text = ""
        for name, content in sections.items():
            sections_text += f"\n\n## {name.upper()}\n{content}\n"

        schema_description = json.dumps(EXTRACTION_SCHEMA, indent=2)

        prompt = f"""
You are given sections from a research paper.

Your task is to extract the following fields strictly according to this schema:
{schema_description}

Rules:
- Use only the information present in the text.
- Do NOT guess or add external knowledge.
- If a field is not mentioned, use "Not specified".
- Return ONLY valid JSON. No markdown, no explanation.

PAPER SECTIONS:
{sections_text}
"""
        return prompt.strip()

    def extract(self, paper_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run extraction on a single paper.
        """
        prompt = self.build_prompt(paper_json)
        return self._generate_json(prompt)


if __name__ == "__main__":
    # Simple smoke test with a dummy paper
    dummy_paper = {
        "sections": {
            "abstract": "This paper proposes a new method for detecting jailbreak attacks in large language models.",
            "method": "We introduce a gradient-based detection mechanism.",
            "experiments": "Evaluated on JailbreakBench using accuracy and F1 score.",
            "limitations": "Our approach requires access to model gradients."
        }
    }

    agent = ExtractionAgent()
    result = agent.extract(dummy_paper)
    print(json.dumps(result, indent=2))