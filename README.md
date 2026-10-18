# Requirement Change Impact Analyzer (RCIA)

RCIA is a beginner-friendly, local-first FastAPI application for reasoning about the likely consequences of changing a software requirement. It extracts requirements from PDF/DOCX files, lets a reviewer correct them, and produces an evidence-backed impact report with dependency signals, risks, effort heuristics, recommendations, and regression tests.

## What is implemented

- PDF parsing with PyMuPDF and DOCX parsing with `python-docx`.
- ID preservation plus stable `AUTO-001` style IDs for requirements without IDs.
- Requirement review, filtering, editing, and manual insertion.
- Sentence Transformers semantic similarity when the model is available.
- Clearly labeled lexical fallback when the embedding model cannot be loaded.
- Configurable score weights and thresholds; signals are returned separately from confidence.
- Conservative NetworkX dependency graph from explicit references and same-module overlap.
- Rule-based risk and effort estimates with disclaimers.
- Generated test cases with HTML, JSON, and CSV exports.
- SQLite persistence through SQLAlchemy, including document/requirement/analysis/test tables.
- No authentication, paid LLM key, Docker, React, or Streamlit dependency.

## Quick start (Windows PowerShell)

```powershell
cd requirement-change-impact-analyzer
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. For a quick demonstration, upload `sample_data/sample_srs.md` and use: `Add OTP verification after password validation during login.`

The first Sentence Transformers analysis may download `all-MiniLM-L6-v2`. If that is unavailable, the app remains functional and labels the report as lexical fallback. PDF/DOCX support requires the corresponding packages in `requirements.txt`; scanned PDFs are intentionally rejected because OCR is not enabled in this initial version.

## Public deployment on Render

Push this `requirement-change-impact-analyzer` folder to GitHub, then create a Render **Web Service** from that repository. If it is inside a larger repository, set Render's Root Directory to `requirement-change-impact-analyzer`.

Use:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /api/health
```

Render requires a web service to listen on `0.0.0.0` and the assigned `PORT`; it then provides an `onrender.com` URL. The current app can run on the free plan for a demonstration, but its local SQLite database and uploaded documents will be lost when the service restarts or redeploys because the free filesystem is ephemeral. For persistence, attach a paid persistent disk mounted at `/var/data` and set:

```text
RCIA_DATA_DIR=/var/data
RCIA_DATABASE_URL=sqlite:////var/data/rcia.db
```

The data-directory setting stores the SQLite file, uploads, and generated reports together on that disk. This remains a single-instance academic deployment; SQLite should be replaced with a managed database before scaling to multiple instances.

## Project structure

```text
requirement-change-impact-analyzer/
├── app/
│   ├── main.py
│   ├── config.py, database.py
│   ├── models/              # SQLAlchemy and Pydantic models
│   ├── services/            # parsing, extraction, scoring, explanation, exports
│   ├── static/              # vanilla CSS and JavaScript
│   └── templates/            # upload/review and report pages
├── sample_data/sample_srs.md
├── tests/
├── uploads/                  # private runtime files, ignored by Git
└── rcia.db                   # generated SQLite database, ignored by Git
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service status |
| POST | `/api/documents/upload` | Validate, parse, and extract an SRS |
| GET | `/api/documents/{document_id}/requirements` | Retrieve extracted requirements |
| PUT | `/api/requirements/{requirement_id}` | Correct a requirement |
| POST | `/api/documents/{document_id}/requirements` | Add a reviewed requirement |
| POST | `/api/analysis` | Run and persist an impact analysis |
| GET | `/api/analysis/{analysis_id}` | Retrieve a saved analysis |
| GET | `/api/analysis/{analysis_id}/export?format=html\|json` | Download a report |
| GET | `/api/analysis/{analysis_id}/test-cases.csv` | Download test cases |
| DELETE | `/api/documents/{document_id}` | Delete a document and associated records |

## Scoring model

The default score is `0.45 × semantic + 0.25 × keyword/domain rule + 0.20 × dependency + 0.10 × explicit reference`. All components are normalized to 0–1. Default low/high thresholds are 0.25 and 0.68. These are transparent heuristics, not validated probabilities. Configure them with environment variables such as `RCIA_WEIGHT_SEMANTIC`, `RCIA_LOW_THRESHOLD`, and `RCIA_HIGH_THRESHOLD`.

Similarity and confidence are deliberately shown separately. A similarity match can indicate related language without proving that a requirement must change; the dependency and explicit-reference signals provide additional evidence.

## Tests

```powershell
pytest -q
```

The tests cover extraction, stable IDs, explicit references, fallback impact analysis, no-forced-impact behavior, upload validation, health, upload, and analysis APIs. API tests use the local SQLite database and should be run from this project directory.

## Limitations and future work

- OCR for scanned PDFs is not enabled.
- The default embedding model depends on its local cache/download availability.
- Dependency inference is intentionally conservative and should be reviewed by a domain owner.
- Effort estimates are illustrative; historical project data would be needed for calibrated forecasting.
- Optional LLM explanations are not enabled in this initial version; deterministic explanations keep the application offline-capable.
- A future version could add migrations, richer traceability from document sections, user consent for external LLM transmission, and an interactive graph visualization.
