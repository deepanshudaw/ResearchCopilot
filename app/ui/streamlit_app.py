import streamlit as st
import json
import glob
import os

from app.pipelines.run_full_pipeline import run_pipeline
import shutil
from app.db import get_connection

import sys
from contextlib import redirect_stdout

class StreamlitLogWriter:
    """
    File-like object that captures stdout writes and updates a Streamlit placeholder live.
    """
    def __init__(self, placeholder, max_chars: int = 20000):
        self.placeholder = placeholder
        self.max_chars = max_chars
        self._buf: str = ""

    def write(self, s: str) -> int:
        if not s:
            return 0
        self._buf += s
        # Keep only the tail to avoid massive UI slowdown
        if len(self._buf) > self.max_chars:
            self._buf = self._buf[-self.max_chars:]
        # Render live (code block)
        self.placeholder.markdown("### Live Pipeline Logs")
        self.placeholder.code(self._buf)
        return len(s)

    def flush(self) -> None:
        # Streamlit doesn't need flush, but some libs call it
        return

def reset_workspace(wipe_raw_pdfs: bool = False) -> None:
    """
    Clears DB rows and pipeline artifacts so each run starts fresh (schema is preserved).
    """
    # Reset DB rows
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM paper_extractions;")
    cur.execute("DELETE FROM papers;")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('papers', 'paper_extractions');")
    conn.commit()
    conn.close()

    # Reset artifact folders
    for d in ["data/processed", "data/extracted", "data/synthesis", "data/critic"]:
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    # Optionally wipe raw PDFs
    if wipe_raw_pdfs:
        d = "data/raw_pdfs"
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

st.set_page_config(page_title="Research Copilot", layout="wide")

# --- Custom dark theme (CSS) ---
st.markdown(
    """
<style>
/* Base app background + text */
.stApp {
  background: radial-gradient(1200px 800px at 20% 10%, rgba(90, 103, 216, 0.18), rgba(0,0,0,0) 60%),
              radial-gradient(900px 700px at 80% 20%, rgba(16, 185, 129, 0.14), rgba(0,0,0,0) 55%),
              linear-gradient(180deg, #0B1020 0%, #070A12 100%);
  color: #E6E8F2;
}

/* General typography */
h1, h2, h3, h4, h5, h6, p, label, span, div {
  color: #E6E8F2;
}

/* Sidebar (if used later) */
section[data-testid="stSidebar"] {
  background: #0A0F1E;
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* Containers and cards */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMarkdownContainer"]) {
  border-radius: 14px;
}

/* Inputs */
div[data-baseweb="input"] > div {
  background-color: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
}

div[data-baseweb="textarea"] textarea {
  background-color: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  color: #E6E8F2 !important;
}

/* Select / radio / slider containers */
div[data-baseweb="select"] > div {
  background-color: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
}

div[data-testid="stSlider"] > div {
  padding: 8px 10px;
  border-radius: 12px;
  background-color: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
}

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, rgba(99,102,241,0.95), rgba(16,185,129,0.85)) !important;
  color: #0B1020 !important;
  border: 0 !important;
  border-radius: 12px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 700 !important;
}

.stButton > button:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

/* Tabs */
button[data-baseweb="tab"] {
  color: rgba(230,232,242,0.85) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
  color: #E6E8F2 !important;
  border-bottom: 2px solid rgba(99,102,241,0.9) !important;
}

/* Code blocks */
pre {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
}

/* Expanders */
div[data-testid="stExpander"] {
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  background: rgba(255,255,255,0.02) !important;
}

/* Success/info boxes */
div[data-testid="stAlert"] {
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  background: rgba(255,255,255,0.03) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

st.title("Research Copilot")
st.caption("Agentic pipeline for structured literature analysis")

tabs = st.tabs([
    "Run Pipeline",
    "Extraction Agent",
    "Synthesis Agent",
    "Critic Agent",
])

# --------------------
# TAB 1: RUN PIPELINE
# --------------------
with tabs[0]:
    st.subheader("Run Analysis")
    st.caption(
        "This page runs the full agentic pipeline end-to-end. "
        "You pick a topic and stages to execute; logs below show what each stage is doing in real time."
    )

    topic = st.text_input("Research topic", "LLM jailbreak defense")
    max_papers = st.slider("Number of papers", 3, 20, 5)

    col1, col2, col3 = st.columns(3)
    with col1:
        run_extraction_stage = st.checkbox("Run Extraction", value=True)
    with col2:
        run_synthesis_stage = st.checkbox("Run Synthesis", value=True)
    with col3:
        run_critic_stage = st.checkbox("Run Critic", value=True)

    start_fresh = st.checkbox("Start fresh (clear DB + artifacts before run)", value=False)
    wipe_raw_pdfs = st.checkbox(
        "Also delete downloaded PDFs (raw_pdfs)",
        value=False,
        disabled=not start_fresh,
    )
    st.caption(
        "Tip: Start fresh prevents old papers from polluting new topics. "
        "Delete PDFs only if you want a fully clean download."
    )

    log_placeholder = st.empty()

    if st.button("Run Pipeline"):
        writer = StreamlitLogWriter(log_placeholder)

        with st.spinner("Running pipeline..."):
            # Redirect all print() output to the live writer
            with redirect_stdout(writer):
                if start_fresh:
                    reset_workspace(wipe_raw_pdfs=wipe_raw_pdfs)

                run_pipeline(
                    topic=topic,
                    max_papers=max_papers,
                    run_extraction_stage=run_extraction_stage,
                    run_synthesis_stage=run_synthesis_stage,
                    run_critic_stage=run_critic_stage,
                )

        st.success("Pipeline completed successfully.")

# --------------------
# TAB 2: PAPERS
# --------------------
with tabs[1]:
    st.subheader("Extracted Papers")
    st.caption(
        "This page shows per-paper structured extractions produced by the Extraction Agent. "
        "Pick a file from the list to preview what the agent extracted (task, method, datasets, metrics, etc.)."
    )

    extracted_files = sorted(glob.glob("data/extracted/*.json"))
    if not extracted_files:
        st.info("No extracted papers found.")
    else:
        file_map = {os.path.basename(f): f for f in extracted_files}
        filenames = list(file_map.keys())

        col_list, col_view = st.columns([1, 3], gap="large")

        with col_list:
            st.markdown("#### Files")
            selected = st.radio(
                "Extracted paper files",
                filenames,
                label_visibility="collapsed",
            )

        with col_view:
            st.markdown("#### Preview")
            with open(file_map[selected]) as f:
                st.json(json.load(f))

# --------------------
# TAB 3: SYNTHESIS
# --------------------
with tabs[2]:
    st.subheader("Synthesis Output")
    st.caption(
        "This page shows the Synthesis Agent output: a topic-level summary built by aggregating multiple extractions. "
        "You’re looking at common tasks, metrics, and open questions across the selected topic."
    )

    synth_files = sorted(glob.glob("data/synthesis/*.json"))
    if not synth_files:
        st.info("No synthesis output found.")
    else:
        latest = synth_files[-1]
        with open(latest) as f:
            synthesis = json.load(f)

        st.markdown("### Dominant Tasks")
        st.write(synthesis.get("dominant_tasks", []))

        st.markdown("### Common Metrics")
        st.write(synthesis.get("common_metrics", []))

        st.markdown("### Gaps & Open Questions")
        st.write(synthesis.get("gaps_and_open_questions", []))

        with st.expander("View raw synthesis JSON"):
            st.json(synthesis)

# --------------------
# TAB 4: CRITIC
# --------------------
with tabs[3]:
    st.subheader("Critic Review")
    st.caption(
        "This page shows the Critic Agent’s evaluation of the synthesis. "
        "It scores quality, highlights strengths/weaknesses, and proposes repairs (including an improved synthesis draft)."
    )

    critic_files = sorted(glob.glob("data/critic/*.json"))
    if not critic_files:
        st.info("No critic output found.")
    else:
        latest = critic_files[-1]
        with open(latest) as f:
            critic = json.load(f)

        st.metric("Overall Rating", f"{critic['overall_rating_10']} / 10")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Strengths")
            st.write(critic["strengths"])
        with col2:
            st.markdown("### Weaknesses")
            st.write(critic["weaknesses"])

        st.markdown("### Suggested Repairs")
        st.write(critic["repairs"])

        with st.expander("Improved Synthesis"):
            st.json(critic["improved_synthesis"])