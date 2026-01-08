try:
    import fitz  # PyMuPDF
except Exception as e:
    raise ImportError(
        "PyMuPDF is not installed correctly. "
        "Run: pip uninstall fitz frontend -y && pip install pymupdf"
    ) from e


def extract_text_by_page(pdf_path: str):
    """
    Return list of strings, one per page.
    """
    if not hasattr(fitz, "open"):
        raise RuntimeError(
            "Incorrect fitz module loaded. "
            "Expected PyMuPDF with fitz.open()."
        )

    doc = fitz.open(pdf_path)
    pages = []

    for page in doc:
        pages.append(page.get_text("text"))

    doc.close()
    return pages