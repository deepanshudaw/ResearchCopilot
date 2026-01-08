# Research Copilot

Research Copilot is an agentic literature analysis system built around three cooperating AI agents. It automates the journey from raw research papers to structured insights, synthesis, and critical evaluation.

A key design choice in this project is model separation of concerns:
- Ollama (local LLM) performs primary extraction and synthesis
- Gemini (cloud LLM) is used as a Critic Agent to review, challenge, and improve Ollama’s outputs

This explicit generation → critique loop improves reliability, depth, and reasoning quality.

---

## Core Idea

Most tools retrieve papers.

Research Copilot reasons across them using agents.

The system is intentionally built to:
- Decompose research understanding into stages
- Make each stage inspectable
- Add external critical oversight using a stronger model

---

## Three-Agent Architecture

### 1. Extraction Agent (Ollama)

Role: Convert unstructured paper text into structured research metadata.

Input:
- Parsed paper sections from PDFs

Output (JSON):
- task
- method
- datasets
- metrics
- key results
- limitations

This agent runs locally using Ollama, making it cheap to iterate, fast for batch processing, and fully inspectable.

---

### 2. Synthesis Agent (Ollama)

Role: Aggregate extractions across papers to identify higher-level insights.

Input:
- Structured outputs from multiple Extraction Agents

Output:
- Dominant research tasks
- Common datasets and metrics
- Recurring methods
- Gaps and open research questions

This agent focuses on pattern discovery, not critique.

---

### 3. Critic Agent (Gemini)

Role: Critically evaluate the synthesis produced by Ollama.

This agent intentionally uses Gemini to avoid self-reinforcement and introduce external judgment.

Output:
- Overall quality rating (out of 10)
- Strengths of the synthesis
- Weaknesses and blind spots
- Suggested repairs
- Improved synthesis draft

This mirrors real-world workflows where one system produces and another reviews.

---

## Why Dual LLMs

Using the same model for generation and critique often leads to agreement bias and missed errors.

Research Copilot avoids this by:
- Letting Ollama generate
- Letting Gemini critique

This separation increases criticality, trustworthiness, and explainability.

---

## End-to-End Pipeline

Research Topic  
→ arXiv Ingestion  
→ PDF Parsing  
→ Extraction Agent (Ollama)  
→ Synthesis Agent (Ollama)  
→ Critic Agent (Gemini)

Each step writes intermediate artifacts to disk or database, making the system transparent and debuggable.

---

## Streamlit User Interface

The Streamlit UI allows users to:
- Run the full pipeline with one click
- Inspect extracted papers
- Explore synthesis outputs
- Review critic feedback
- Observe live pipeline logs

Run locally with:


python -m streamlit run app/ui/streamlit_app.py


⸻

Tech Stack

Languages and Frameworks:
	•	Python 3.10+
	•	Streamlit
	•	SQLite

LLMs:
	•	Ollama (local inference)
	•	Gemini (external critic model)

Data and Parsing:
	•	arXiv API (feedparser)
	•	PyMuPDF

⸻

Known Limitations (v1)
	•	arXiv API rate limits
	•	Occasional malformed LLM JSON outputs
	•	No embedding-based retrieval yet

These are engineering tradeoffs, not architectural constraints.

⸻

Why This Project Matters

This project demonstrates:
	•	Multi-agent system design
	•	Model orchestration
	•	Separation of generation and critique
	•	Practical LLM evaluation techniques
	•	End-to-end system thinking

It is intentionally designed to be explainable, demoable, and extensible.

⸻

Author

Deepanshu Dawande
MSc Data Science and AI
Agentic Systems, LLM Evaluation, Applied Machine Learning
