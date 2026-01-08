import json
import os
from datetime import datetime
from typing import Any, Dict

from app.agents.critic_agent import CriticAgent

CRITIC_DIR = os.path.join("data", "critic")
os.makedirs(CRITIC_DIR, exist_ok=True)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def run(synthesis_path: str):
    syn = load_json(synthesis_path)
    agent = CriticAgent()
    out = agent.critique(syn)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(synthesis_path).replace(".json", "")
    out_path = os.path.join(CRITIC_DIR, f"critic_{base}_{ts}.json")
    save_json(out_path, out)

    print(f"[critic] Saved critique → {out_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m app.pipelines.run_critic data/synthesis/<file>.json")
        raise SystemExit(1)
    run(sys.argv[1])