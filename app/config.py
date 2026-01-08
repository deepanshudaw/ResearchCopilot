import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# LLM provider config
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

# Ollama settings (only used when LLM_PROVIDER == "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Gemini config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use 1.5 Flash by default; if Google ever kills it for your account,
# you can switch this to "gemini-2.0-flash" in one place.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Critic agent config (can use a different provider/key/model than extraction & synthesis)
CRITIC_PROVIDER = os.getenv("CRITIC_PROVIDER", "gemini").strip().lower()

# Allow a separate Gemini API key for the CriticAgent; fallback to main key if not set
CRITIC_GEMINI_API_KEY = os.getenv("CRITIC_GEMINI_API_KEY", GEMINI_API_KEY)

# Use a stronger model for critique / abstraction by default
CRITIC_GEMINI_MODEL = os.getenv("CRITIC_GEMINI_MODEL", "gemini-1.5-pro")

# SQLite DB path
DB_PATH = os.getenv("DB_PATH", "research.db")