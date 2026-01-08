PAPER_SCHEMA = {
    "title": str,
    "year": int,
    "venue": str,
    "tasks": list,        # e.g. ["LLM jailbreak defense"]
    "methods": list,      # list[dict]
    "datasets": list,     # e.g. ["AdvBench", "HarmBench"]
    "metrics": list,      # list[dict]
    "key_results": list,  # list[str]
    "limitations": list,  # list[str]
    "url": str,
    "arxiv_id": str,
}