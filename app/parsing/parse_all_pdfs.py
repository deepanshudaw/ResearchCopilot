import os
import json

from app.db import get_connection
from app.parsing.pdf_loader import extract_text_by_page
from app.parsing.text_cleaner import clean_pages
from app.parsing.section_splitter import split_into_sections

PROCESSED_DIR = os.path.join("data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


def get_all_pdfs():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, arxiv_id, pdf_path FROM papers WHERE pdf_path IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    return rows


def parse_pdf(paper_id: int, arxiv_id: str, pdf_path: str):
    print(f"[parse] Processing {arxiv_id} from {pdf_path}")

    # 1. Load PDF
    pages = extract_text_by_page(pdf_path)

    # 2. Clean text
    cleaned_pages = clean_pages(pages)
    full_text = "\n".join(cleaned_pages)

    # 3. Split into sections
    sections = split_into_sections(full_text)

    # 4. Save JSON
    filename = f"{paper_id}_{arxiv_id}.json"
    dest = os.path.join(PROCESSED_DIR, filename)

    with open(dest, "w") as f:
        json.dump({
            "paper_id": paper_id,
            "arxiv_id": arxiv_id,
            "sections": sections
        }, f, indent=2)

    print(f"[parse] Saved processed file → {dest}")
    return dest


def parse_all():
    rows = get_all_pdfs()
    print(f"[parse] Found {len(rows)} PDFs to process.")

    for paper_id, arxiv_id, pdf_path in rows:
        parse_pdf(paper_id, arxiv_id, pdf_path)


if __name__ == "__main__":
    parse_all()