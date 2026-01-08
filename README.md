# Research Copilot

**Research Copilot** is an **agentic literature analysis system** that automates the journey from raw research papers to structured insights, synthesis, and critique using Large Language Models (LLMs).

It is built to help researchers, students, and engineers **rapidly understand a research area**, identify trends, gaps, and evaluate the quality of synthesized conclusions.

---

##  What This Project Does

Given a research topic, Research Copilot:

1.  Searches arXiv for relevant papers  
2.  Downloads and parses PDFs  
3.  Extracts structured metadata using an LLM agent  
4.  Synthesizes insights across papers  
5.  Critiques the synthesis using a Critic Agent  
6.  Visualizes everything in a Streamlit UI  

All stages are **modular, inspectable, and agent-driven**.

---

##  Architecture Overview

Topic
│
▼
[ arXiv Ingestion ]
│
▼
[ PDF Parsing ]
│
▼
[ Extraction Agent ]
│   → task, method, datasets, metrics, results, limitations
▼
[ Synthesis Agent ]
│   → trends, dominant tasks, gaps, open questions
▼
[ Critic Agent ]
→ strengths, weaknesses, rating, suggested repairs

Each agent runs independently and writes outputs to **disk** and **SQLite**.

---

## Agents

### 🔍 Extraction Agent
Reads parsed paper sections and produces structured JSON:
- task
- method
- datasets
- metrics
- key results
- limitations

### Synthesis Agent
Aggregates extractions to identify:
- dominant research directions
- common metrics and datasets
- gaps and open problems

### Critic Agent
Evaluates synthesis quality and outputs:
- overall rating (out of 10)
- strengths & weaknesses
- suggested repairs
- improved synthesis draft

---

## Streamlit UI

The Streamlit app provides:

-  One-click pipeline execution
-  Browse extracted papers
-  View synthesis outputs
-  Inspect critic feedback
-  Live pipeline logs

Run it with:

python -m streamlit run app/ui/streamlit_app.py


⸻

⚙️ Tech Stack

Core
	•	Python 3.10+
	•	SQLite
	•	Streamlit

LLMs
	•	Ollama (local models like mistral)
	•	Gemini (optional, higher-quality synthesis & critique)

Parsing & Ingestion
	•	PyMuPDF (PDF parsing)
	•	feedparser (arXiv API)

⸻

📁 Project Structure

research-copilot/
├── app/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── extraction_agent.py
│   │   ├── synthesis_agent.py
│   │   └── critic_agent.py
│   ├── pipelines/
│   │   ├── run_extraction.py
│   │   ├── run_synthesis.py
│   │   ├── run_critic.py
│   │   └── run_full_pipeline.py
│   ├── ingestion/
│   ├── parsing/
│   └── ui/
│       └── streamlit_app.py
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   ├── extracted/
│   ├── synthesis/
│   └── critic/
├── research.db
├── .env.example
└── README.md


⸻

🔐 Configuration

Create one locally:

Example:

LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
OLLAMA_URL=http://localhost:11434

GEMINI_API_KEY=your_key_here
CRITIC_PROVIDER=gemini

DB_PATH=research.db


⸻

🚧 Known Limitations (v1)
	•	arXiv API rate limiting
	•	Occasional LLM JSON formatting errors
	•	No embedding / RAG layer yet

These are design-acknowledged, not architectural blockers.

⸻

🚀 Future Work
	•	Parallel RAG pipeline
	•	Embeddings over extracted sections
	•	Topic clustering & comparison
	•	Report export (Markdown / LaTeX)
	•	Cloud deployment



👤 Author

Deepanshu Dawande
MSc Data Science & AI
Agentic Systems · LLM Evaluation · Applied ML
