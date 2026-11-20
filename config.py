import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")
ASR_MODEL = os.getenv("ASR_MODEL", "openai/whisper-small")
DB_PATH = os.getenv("DB_PATH", "progress.db")

LANGS = {"en": "inglés", "fr": "francés"}
WHISPER_LANG = {"en": "english", "fr": "french"}
LEVELS = ["A1", "A2", "B1", "B2", "C1"]
