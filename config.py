import os
from dotenv import load_dotenv
load_dotenv()

# --- Feature Flags ---
ENABLE_USE_GNEWS = True
ENABLE_USE_SERPAPI_TRENDS = False
ENABLE_USE_TWITTER = False

# --- API Keys ---
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# Google News Config
GNEWS_LANGUAGE = 'en'
GNEWS_COUNTRY = 'US'
GNEWS_PERIOD = '1m'
GNEWS_MAX_RESULTS = 50

# --- Investing Theses Configuration ---
INVESTING_THEMES = {
    "cybersecurity_ai": {
        "enabled": True,  # ACTIVE
        "name": "AI Driven Cybersecurity",
        "description": "Impact of GenAI on defense and attack vectors.",
        "keywords": [
            "AI Threat Detection",
            "Continuous Threat Exposure Management",
            "Data Security Posture Management",
            "Identity Threat Detection and Response",
            "Human Risk Management cybersecurity",
            "AI Security Posture Management",
            "Passkeys authentication"
        ],
        "system_prompt_context": "Eres un analista experto en Ciberseguridad e Inteligencia Artificial, especializado en detectar hype vs utilidad real en nuevas tecnologías de defensa y ataque.",
        "categories": [
            "AI Threat Detection", "CTEM", "DSPM", "ITDR", "Human Risk Management", 
            "AI-SPM", "Passkeys/Passwordless", "General Cybersecurity", "Vendor News", "Other"
        ]
    },
    "china_real_estate": {
        "enabled": False,  # DISABLED
        "name": "China Property Crisis",
        "description": "Debt crisis in Chinese real estate sector.",
        "keywords": [
            "Evergrande liquidation",
            "China property debt",
            "Country Garden default",
            "China housing market"
        ],
        "system_prompt_context": "Eres un economista experto en Mercados Asiáticos y Crisis de Deuda Soberana. Analizas el impacto sistémico del sector inmobiliario chino en la economía global.",
        "categories": [
            "Developer Default", "Government Policy", "Banking Contagion", 
            "Social Unrest", "International Impact", "Market Data", "Other"
        ]
    },
    "quantum_computing": {
         "enabled": False, # DISABLED
         "name": "Quantum Supremacy",
         "keywords": ["Quantum Qubit", "Post-quantum cryptography"],
         "system_prompt_context": "Eres un físico teórico y consultor tecnológico experto en Computación Cuántica y Criptografía.",
         "categories": ["Hardware Breakthrough", "Algorithm Development", "Security Threat", "Investment/Funding", "Other"]
    }
}

# --- Output Directories (Dynamic) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_ROOT = os.path.join(BASE_DIR, "outputs")

def get_theme_dirs(theme_id):
    """Generates independent folder structure for a given theme."""
    theme_root_out = os.path.join(OUTPUTS_ROOT, theme_id)
    theme_data_dir = os.path.join(BASE_DIR, "data", theme_id)
    
    dirs = {
        "ROOT": theme_root_out,
        "TRENDS_CSV": os.path.join(theme_root_out, "serapi_trends"),
        "CHARTS_HTML": os.path.join(theme_root_out, "charts_html"),
        "CHARTS_PNG": os.path.join(theme_root_out, "charts_png"),
        "DATA": theme_data_dir,
    }
    
    # Auto-create folders
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
        
    return dirs

# Legacy fallback (optional)
DIRS = get_theme_dirs("general_legacy")