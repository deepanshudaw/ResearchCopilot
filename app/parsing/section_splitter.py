import re

SECTION_HEADERS = [
    "abstract",
    "introduction",
    "related work",
    "background",
    "method",
    "methodology",
    "approach",
    "experiments",
    "results",
    "analysis",
    "discussion",
    "conclusion",
    "limitations",
    "future work"
]

def split_into_sections(full_text: str):
    """
    Split paper text into sections based on common academic headers.
    Returns a dict: {section_name: content}
    """

    text = full_text.lower()

    pattern = r"(?=(" + "|".join([re.escape(h) for h in SECTION_HEADERS]) + r"))"

    # Find all header occurrences (positions)
    matches = list(re.finditer(pattern, text))

    if not matches:
        # fallback: return entire text as "full_text"
        return {"full_text": full_text}

    sections = {}
    for i, match in enumerate(matches):
        header = match.group(0)
        start = match.start()

        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = full_text[start:end].strip()

        sections[header] = content

    return sections