from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("RCIA_DATA_DIR", str(PROJECT_ROOT)))
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_DIR = DATA_DIR / "reports"
DATABASE_URL = os.getenv("RCIA_DATABASE_URL", f"sqlite:///{DATA_DIR / 'rcia.db'}")
MAX_UPLOAD_SIZE = int(os.getenv("RCIA_MAX_UPLOAD_MB", "10")) * 1024 * 1024

SCORING_WEIGHTS = {
    "semantic": float(os.getenv("RCIA_WEIGHT_SEMANTIC", "0.45")),
    "keywords": float(os.getenv("RCIA_WEIGHT_KEYWORDS", "0.25")),
    "dependency": float(os.getenv("RCIA_WEIGHT_DEPENDENCY", "0.20")),
    "explicit": float(os.getenv("RCIA_WEIGHT_EXPLICIT", "0.10")),
}
LOW_IMPACT_THRESHOLD = float(os.getenv("RCIA_LOW_THRESHOLD", "0.25"))
HIGH_IMPACT_THRESHOLD = float(os.getenv("RCIA_HIGH_THRESHOLD", "0.68"))
MODEL_NAME = os.getenv("RCIA_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
ALLOWED_ORIGINS = [item.strip() for item in os.getenv("RCIA_ALLOWED_ORIGINS", "*").split(",") if item.strip()]


def ensure_directories() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
