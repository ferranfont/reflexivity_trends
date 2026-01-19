import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Feature Flags ---
# Enable/Disable specific data sources
ENABLE_USE_GNEWS = True
ENABLE_USE_SERPAPI_TRENDS = False
ENABLE_USE_TWITTER = False  # Future implementation

# --- API Keys & Configuration ---
# SerpApi
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# Google News
GNEWS_LANGUAGE = 'en'
GNEWS_COUNTRY = 'US'
GNEWS_PERIOD = '1m'
GNEWS_MAX_RESULTS = 50

# Global Search Terms (can be overridden)
DEFAULT_SEARCH_TERMS = [
    "AI Threat Detection",
    "Continuous Threat Exposure Management",
    "Data Security Posture Management",
    "Identity Threat Detection and Response",
    "Human Risk Management cybersecurity",
    "AI Security Posture Management",
    "Passkeys authentication"
]
