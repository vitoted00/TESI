import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "llama-3.1-8b-instant")
    CODE_MODEL = os.getenv("CODE_MODEL", "llama-3.3-70b-versatile")

    # Output
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")