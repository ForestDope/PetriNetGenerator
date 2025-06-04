# src/config.py
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL_GEMINI = "gemini-2.5-flash-preview-05-20" 

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HAND_MADE_DIR = DATA_DIR / "hand_made"

SCHEMAS_DIR = BASE_DIR / "schemas"
OUTPUTS_DIR = BASE_DIR / "outputs"

SYNTHESIZED_PARENT_DIR = OUTPUTS_DIR / "synthesized_data"
SYNTHESIZED_APPROVED_DIR = SYNTHESIZED_PARENT_DIR / "approved"
SYNTHESIZED_REJECTED_MANUAL_DIR = SYNTHESIZED_PARENT_DIR / "rejected_manual"
INVALID_AUTO_REJECTED_DIR = SYNTHESIZED_PARENT_DIR / "invalid_auto_rejected"

REVIEW_TEMP_DIR = OUTPUTS_DIR / "review_temp"
# VISUALIZATIONS_DIR = OUTPUTS_DIR / "visualizations" # REMOVED if not used as default

PETRI_NET_SCHEMA_PATH = SCHEMAS_DIR / "petri_net_schema.json"

# Ensure Directories Exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
HAND_MADE_DIR.mkdir(parents=True, exist_ok=True)
SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True) # Parent output dir

SYNTHESIZED_PARENT_DIR.mkdir(parents=True, exist_ok=True)
SYNTHESIZED_APPROVED_DIR.mkdir(parents=True, exist_ok=True)
SYNTHESIZED_REJECTED_MANUAL_DIR.mkdir(parents=True, exist_ok=True)
INVALID_AUTO_REJECTED_DIR.mkdir(parents=True, exist_ok=True)

REVIEW_TEMP_DIR.mkdir(parents=True, exist_ok=True)

if not GOOGLE_API_KEY: print("CRITICAL ERROR: GOOGLE_API_KEY not found.")
if not PETRI_NET_SCHEMA_PATH.exists(): print(f"Warning: Schema file not found: {PETRI_NET_SCHEMA_PATH}")

print(f"Config loaded. Synthesized data root: {SYNTHESIZED_PARENT_DIR.resolve()}")