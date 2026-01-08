import re

def clean_text(text: str) -> str:
    """
    Light cleaning: remove repeated whitespace, page numbers, leftover latex.
    """
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove common page number patterns
    text = re.sub(r'\bPage\s+\d+\b', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # Strip weird unicode markers
    text = text.replace("\x00", "").strip()

    return text


def clean_pages(pages):
    """Apply clean_text to every page."""
    return [clean_text(p) for p in pages]