import os
import time
from typing import List, Tuple

import requests

from app.db import get_connection


RAW_PDF_DIR = os.path.join("data", "raw_pdfs")


def ensure_pdf_dir():
    os.makedirs(RAW_PDF_DIR, exist_ok=True)


def get_papers_needing_pdfs(limit: int = 20) -> List[Tuple[int, str, str]]:
    """
    Return list of (id, arxiv_id, pdf_url) for papers where pdf_path is NULL.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, arxiv_id, pdf_url
        FROM papers
        WHERE pdf_path IS NULL
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_pdf_path(paper_id: int, pdf_path: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE papers SET pdf_path = ? WHERE id = ?",
        (pdf_path, paper_id),
    )
    conn.commit()
    conn.close()


def download_pdf(paper_id: int, arxiv_id: str, pdf_url: str) -> str:
    """
    Download a single PDF and return the local path, or None on failure.
    """
    ensure_pdf_dir()
    # Nice file name: 12_2401.01234.pdf
    filename = f"{paper_id}_{arxiv_id.replace('/', '_')}.pdf"
    dest_path = os.path.join(RAW_PDF_DIR, filename)

    print(f"[pdf] Downloading {arxiv_id} from {pdf_url}")
    try:
        resp = requests.get(pdf_url, stream=True, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[pdf] Failed to download {arxiv_id}: {e}")
        return None

    try:
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        print(f"[pdf] Error writing file for {arxiv_id}: {e}")
        # cleanup partial
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return None

    print(f"[pdf] Saved to {dest_path}")
    return dest_path


def download_pdfs(batch_size: int = 10, delay_seconds: float = 3.0):
    """
    Download PDFs for all papers missing pdf_path, in batches.
    Delay between downloads to be nice to arXiv.
    """
    ensure_pdf_dir()
    total_downloaded = 0

    while True:
        rows = get_papers_needing_pdfs(limit=batch_size)
        if not rows:
            print("[pdf] No more papers needing PDFs.")
            break

        for paper_id, arxiv_id, pdf_url in rows:
            local_path = download_pdf(paper_id, arxiv_id, pdf_url)
            if local_path:
                update_pdf_path(paper_id, local_path)
                total_downloaded += 1
            time.sleep(delay_seconds)  # be polite to arXiv

    print(f"[pdf] Done. Total PDFs downloaded: {total_downloaded}")


if __name__ == "__main__":
    download_pdfs(batch_size=5, delay_seconds=3.0)