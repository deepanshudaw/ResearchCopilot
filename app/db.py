import sqlite3
from app.config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Very minimal for now; we’ll extend later
    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            year INTEGER,
            abstract TEXT,
            pdf_url TEXT,
            pdf_path TEXT,
            arxiv_id TEXT,
            topic TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER NOT NULL,
            arxiv_id TEXT,
            model_provider TEXT,
            model_name TEXT,
            extracted_at TEXT DEFAULT (datetime('now')),
            task TEXT,
            method TEXT,
            datasets_json TEXT,
            metrics_json TEXT,
            key_results TEXT,
            limitations TEXT,
            raw_extraction_json TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        );
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_extractions_unique
        ON paper_extractions(paper_id, model_provider, model_name);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("DB initialised at", DB_PATH)