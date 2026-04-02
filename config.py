"""Configuration settings for the coaching app"""
import os

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "coaching_app_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# API Keys
GROK_API_KEY = os.getenv("GROK_API_KEY", "")

# App Settings
DEFAULT_TOP_K = 5
MAX_RETRIEVE = 20