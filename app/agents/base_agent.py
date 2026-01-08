import json
from typing import Optional, Any, Dict

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_MODEL,
    OLLAMA_URL,
)


class BaseAgent:
    """
    Thin wrapper around an LLM provider.

    Supports:
    - Gemini via google.generativeai
    - Ollama via local HTTP

    Allows per-agent overrides for:
    - provider
    - API key
    - model name

    Other agents (ExtractionAgent, SynthesisAgent, CriticAgent) should subclass this
    and reuse _generate_text / _generate_json.
    """

    def __init__(
        self,
        system_instruction: Optional[str] = None,
        provider: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.system_instruction = system_instruction or ""

        # Resolve provider (agent override → global config → default)
        self.provider = (provider or LLM_PROVIDER or "gemini").strip().lower()

        if self.provider == "gemini":
            # Lazy import so Ollama-only users don't need the Gemini SDK
            import google.generativeai as genai  # type: ignore

            api_key = gemini_api_key or GEMINI_API_KEY
            if not api_key:
                raise RuntimeError(
                    "Gemini API key missing. Set GEMINI_API_KEY or pass gemini_api_key override."
                )

            genai.configure(api_key=api_key)

            self._genai = genai
            self.model_name = model_name or GEMINI_MODEL

            self.model = genai.GenerativeModel(
                self.model_name,
                system_instruction=self.system_instruction if self.system_instruction else None,
            )

        elif self.provider == "ollama":
            # Ollama is a local HTTP server (default http://localhost:11434)
            self.model_name = model_name or OLLAMA_MODEL
            self.ollama_generate_url = OLLAMA_URL.rstrip("/") + "/api/generate"

        else:
            raise ValueError(f"Unsupported provider: {self.provider!r}")

    def _generate_text(self, prompt: str) -> str:
        """
        Simple text generation used by agents.
        """
        if self.provider == "gemini":
            resp = self.model.generate_content(prompt)
            return (resp.text or "").strip()

        if self.provider == "ollama":
            import requests  # lazy import

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            }
            r = requests.post(self.ollama_generate_url, json=payload, timeout=180)
            if r.status_code != 200:
                raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")
            data = r.json()
            return (data.get("response") or "").strip()

        raise RuntimeError(f"Unknown provider: {self.provider!r}")

    def _generate_json(self, prompt: str) -> Dict[str, Any]:
            def _strip_to_json(s: str) -> str:
                """
                Make best effort to extract valid JSON text from model output.
                Handles common cases:
                - Markdown fenced blocks ```json ... ```
                - Leading/trailing commentary around JSON
                """
                if s is None:
                    return ""

                s = s.strip()

                # Remove common markdown code fences
                if s.startswith("```"):
                    # Drop the first fence line
                    lines = s.splitlines()
                    if lines:
                        # remove first line like ```json or ```
                        lines = lines[1:]
                    # remove last line if it's a closing fence
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    s = "\n".join(lines).strip()

                # If there's still junk around JSON, slice from first {/[ to last }/]
                first_obj = s.find("{")
                first_arr = s.find("[")
                if first_obj == -1 and first_arr == -1:
                    return s  # nothing to slice; will fail upstream with good error

                start = first_obj if first_arr == -1 else (first_arr if first_obj == -1 else min(first_obj, first_arr))

                last_obj = s.rfind("}")
                last_arr = s.rfind("]")
                end = max(last_obj, last_arr)

                if start != -1 and end != -1 and end > start:
                    s = s[start:end + 1].strip()

                return s

            text = self._generate_text(prompt)
            cleaned = _strip_to_json(text)

            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # One corrective retry
                fix_prompt = (
                    "Return ONLY valid JSON (no markdown, no code fences, no extra text). "
                    "Fix the following into valid JSON:\n\n" + (text or "")
                )
                text2 = self._generate_text(fix_prompt)
                cleaned2 = _strip_to_json(text2)

                try:
                    return json.loads(cleaned2)
                except json.JSONDecodeError as e:
                    snippet = (cleaned2 or text2 or "").strip()
                    raise ValueError(f"Failed to parse JSON output. Snippet: {snippet[:200]}") from e


if __name__ == "__main__":
    agent = BaseAgent(system_instruction="You are a concise assistant.")
    out = agent._generate_text("In one sentence, explain this project.")
    print(f"{agent.provider} response:\n{out}")