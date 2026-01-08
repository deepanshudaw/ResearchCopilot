import sys
import os
import time
import urllib.parse
from typing import List, Dict

import feedparser

import requests

from app.db import get_connection


ARXIV_API_URL = "http://export.arxiv.org/api/query"
RAW_PDF_DIR = os.path.join("data", "raw_pdfs")
os.makedirs(RAW_PDF_DIR, exist_ok=True)


def fetch_arxiv_entries(topic: str, max_results: int = 20):
    """
    Call the arXiv API and return parsed entries using feedparser.
    """
    query = f"all:{topic}"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
    }
    url = ARXIV_API_URL + "?" + urllib.parse.urlencode(params)
    print(f"[arxiv] GET {url}")

    feed = feedparser.parse(url)
    if feed.bozo:
        print("[arxiv] Warning: feedparser bozo flag set (malformed feed)")

    return feed.entries


def download_pdf(pdf_url: str, paper_id: int, arxiv_id: str) -> str:
    """
    Download arXiv PDF to data/raw_pdfs and return local path.
    """
    os.makedirs(RAW_PDF_DIR, exist_ok=True)
    filename = f"{paper_id}_{arxiv_id}.pdf"
    dest = os.path.join(RAW_PDF_DIR, filename)

    # Reuse if already downloaded
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest

    resp = requests.get(pdf_url, timeout=60)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        f.write(resp.content)

    return dest


def entry_to_row(entry, topic: str) -> Dict:
    """
    Convert a feedparser entry to a dict matching the `papers` table.
    """
    title = entry.title.strip().replace("\n", " ")
    abstract = entry.summary.strip().replace("\n", " ")
    published = getattr(entry, "published", None) or ""
    year = None
    if len(published) >= 4 and published[:4].isdigit():
        year = int(published[:4])

    # Authors
    authors = ", ".join(a.name for a in getattr(entry, "authors", []))

    # arXiv id
    # Example entry.id: 'http://arxiv.org/abs/2401.01234v1'
    raw_id = entry.id
    if "/abs/" in raw_id:
        arxiv_id = raw_id.split("/abs/")[-1]
    else:
        arxiv_id = raw_id.rsplit("/", 1)[-1]

    # PDF URL
    pdf_url = None
    for link in entry.links:
        # Some feeds label pdf with title='pdf', others type='application/pdf'
        if getattr(link, "title", "").lower() == "pdf" or getattr(link, "type", "") == "application/pdf":
            pdf_url = link.href
            break
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "pdf_url": pdf_url,
        "pdf_path": None,
        "arxiv_id": arxiv_id,
        "topic": topic,
    }


def insert_papers(rows: List[Dict]):
    """
    Insert rows into the papers table, skipping duplicates by arxiv_id.
    """
    if not rows:
        print("[db] No rows to insert.")
        return

    conn = get_connection()
    cur = conn.cursor()

    inserted = 0
    for row in rows:
        cur.execute("SELECT id FROM papers WHERE arxiv_id = ?", (row["arxiv_id"],))
        exists = cur.fetchone()
        if exists:
            print(f"[db] Skipping existing paper {row['arxiv_id']} – {row['title'][:60]}...")
            continue

        cur.execute(
            """
            INSERT INTO papers (title, authors, year, abstract, pdf_url, pdf_path, arxiv_id, topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["title"],
                row["authors"],
                row["year"],
                row["abstract"],
                row["pdf_url"],
                row["pdf_path"],
                row["arxiv_id"],
                row["topic"],
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"[db] Inserted {inserted} new papers.")


def ensure_pdfs_for_topic(topic: str, polite_delay_s: float = 1.0):
    """
    For all papers in DB with the given topic that are missing pdf_path,
    download their PDFs and update pdf_path.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, arxiv_id, pdf_url
        FROM papers
        WHERE topic = ?
          AND (pdf_path IS NULL OR trim(pdf_path) = '')
        ORDER BY id ASC
        """,
        (topic,),
    )
    rows = cur.fetchall()

    if not rows:
        conn.close()
        print("[pdf] No papers missing pdf_path for this topic.")
        return

    for paper_id, arxiv_id, pdf_url in rows:
        if not pdf_url:
            print(f"[pdf] Missing pdf_url for {arxiv_id}, skipping.")
            continue
        try:
            time.sleep(polite_delay_s)
            local_path = download_pdf(pdf_url, paper_id, arxiv_id)
            cur.execute("UPDATE papers SET pdf_path = ? WHERE id = ?", (local_path, paper_id))
            conn.commit()
            print(f"[pdf] Downloaded {arxiv_id} → {local_path}")
        except Exception as e:
            print(f"[pdf] Failed to download {arxiv_id}: {e}")

    conn.close()


def search_papers(topic: str, max_results: int = 20):
    """
    High-level function: topic -> arXiv -> DB.
    """
    print(f"[search] Searching arXiv for topic: {topic!r}, max_results={max_results}")
    entries = fetch_arxiv_entries(topic, max_results=max_results)
    print(f"[search] Got {len(entries)} entries from arXiv.")

    rows = [entry_to_row(e, topic=topic) for e in entries]
    insert_papers(rows)
    ensure_pdfs_for_topic(topic)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ingestion.search_papers \"topic string\" [max_results]")
        sys.exit(1)

    topic = sys.argv[1]
    max_results = 20
    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        max_results = int(sys.argv[2])

    search_papers(topic, max_results=max_results)