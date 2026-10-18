from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from types import SimpleNamespace

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ALLOWED_ORIGINS, MAX_UPLOAD_SIZE, UPLOAD_DIR, ensure_directories
from app.database import get_db, init_db
from app.models.database_models import Analysis, Document, ImpactResult, Requirement, TestCase
from app.models.schemas import AnalysisRequest, RequirementCreate, RequirementOut, RequirementUpdate
from app.services.document_parser import DocumentParseError, clean_text, file_hash, parse_document, validate_upload
from app.services.impact_analyzer import analyze
from app.services.report_generator import csv_bytes, html_report
from app.services.requirement_extractor import REF_PATTERN, extract_requirements


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Requirement Change Impact Analyzer", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Create the local runtime directories/tables at import as well as on ASGI startup.
# This keeps direct TestClient usage and simple scripts predictable.
ensure_directories()
init_db()

if ALLOWED_ORIGINS == ["*"]:
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
else:
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    ensure_directories()
    init_db()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.get("/results", include_in_schema=False)
def results_page() -> FileResponse:
    return FileResponse(BASE_DIR / "templates" / "results.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "Requirement Change Impact Analyzer"}


def _engine_requirement(req: Requirement):
    references = [re.sub(r"[ _]+", "-", item.upper()) for item in REF_PATTERN.findall(req.description) if item.upper() != req.requirement_code]
    return SimpleNamespace(id=req.id, code=req.requirement_code, requirement_code=req.requirement_code, description=req.description, category=req.category, module=req.module, references=references)


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    data = await file.read()
    try:
        suffix = validate_upload(file.filename or "", file.content_type, data, MAX_UPLOAD_SIZE)
        digest = file_hash(data)
        existing = db.scalar(select(Document).where(Document.file_hash == digest))
        if existing:
            return {"document": {"id": existing.id, "filename": existing.filename, "requirement_count": len(existing.requirements), "extraction_status": existing.extraction_status}, "message": "This document was already uploaded."}
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        path = UPLOAD_DIR / safe_name
        path.write_bytes(data)
        text = clean_text(parse_document(path, suffix))
        extracted = extract_requirements(text)
        if not extracted:
            path.unlink(missing_ok=True)
            raise DocumentParseError("No usable requirement statements were found. Add requirement IDs or clear requirement sentences to the SRS.")
        document = Document(filename=Path(file.filename or "document").name[:255], file_hash=digest, stored_path=str(path), extraction_status="completed")
        document.requirements = [Requirement(requirement_code=item.code, description=item.description, category=item.category, module=item.module, source_reference=item.source_reference) for item in extracted]
        db.add(document)
        db.commit()
        db.refresh(document)
        return {"document": {"id": document.id, "filename": document.filename, "requirement_count": len(document.requirements), "extraction_status": document.extraction_status}, "requirements": [RequirementOut.model_validate(item).model_dump() for item in document.requirements]}
    except DocumentParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="The document could not be processed safely.") from exc


@app.get("/api/documents/{document_id}/requirements", response_model=list[RequirementOut])
def get_requirements(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return list(document.requirements)


@app.put("/api/requirements/{requirement_id}", response_model=RequirementOut)
def update_requirement(requirement_id: int, payload: RequirementUpdate, db: Session = Depends(get_db)):
    requirement = db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    for key, value in payload.model_dump().items():
        setattr(requirement, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(requirement)
    return requirement


@app.post("/api/documents/{document_id}/requirements", response_model=RequirementOut)
def add_requirement(document_id: int, payload: RequirementCreate, db: Session = Depends(get_db)):
    if not db.get(Document, document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    exists = db.scalar(select(Requirement).where(Requirement.document_id == document_id, Requirement.requirement_code == payload.requirement_code))
    if exists:
        raise HTTPException(status_code=409, detail="That requirement ID already exists in this document.")
    requirement = Requirement(document_id=document_id, source_reference="Added during review", **payload.model_dump())
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@app.post("/api/analysis")
def run_analysis(payload: AnalysisRequest, db: Session = Depends(get_db)) -> dict:
    document = db.get(Document, payload.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    target = db.get(Requirement, payload.target_requirement_id) if payload.target_requirement_id else None
    if target and target.document_id != document.id:
        raise HTTPException(status_code=400, detail="The selected target requirement does not belong to this document.")
    try:
        result = analyze([_engine_requirement(item) for item in document.requirements], payload.proposed_change, payload.change_type, target.requirement_code if target else None)
        analysis = Analysis(document_id=document.id, change_type=payload.change_type, proposed_change=payload.proposed_change, target_requirement_id=target.id if target else None, overall_summary=result["summary"], overall_risk=result["overall_risk"], result_json=json.dumps(result))
        db.add(analysis)
        db.flush()
        for impact in result["impacts"]:
            db.add(ImpactResult(analysis_id=analysis.id, requirement_id=impact["requirement_id"], impact_type=impact["impact_type"], impact_score=impact["impact_score"], severity=impact["severity"], confidence=impact["confidence"], explanation=impact["explanation"], evidence=impact["evidence"], recommended_action=impact["recommended_action"], signal_details=json.dumps(impact["signals"])))
        for case in result["test_cases"]:
            db.add(TestCase(analysis_id=analysis.id, requirement_id=case.get("related_requirement_id"), test_case_code=case["test_case_id"], objective=case["objective"], preconditions=case["preconditions"], steps=case["steps"], expected_result=case["expected_result"], category=case["category"]))
        db.commit()
        return {"analysis_id": analysis.id, "document": {"id": document.id, "filename": document.filename}, "proposed_change": payload.proposed_change, "change_type": payload.change_type, "created_at": analysis.creation_timestamp.isoformat(), "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="The impact analysis could not be completed.") from exc


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> dict:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"analysis_id": analysis.id, "document_id": analysis.document_id, "proposed_change": analysis.proposed_change, "change_type": analysis.change_type, "created_at": analysis.creation_timestamp.isoformat(), "result": json.loads(analysis.result_json)}


@app.get("/api/analysis/{analysis_id}/export")
def export_analysis(analysis_id: int, format: str = Query(default="html", pattern="^(html|json)$"), db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    result = json.loads(analysis.result_json)
    if format == "json":
        return JSONResponse(content={"analysis_id": analysis.id, "document": analysis.document.filename, "proposed_change": analysis.proposed_change, "change_type": analysis.change_type, "result": result})
    return Response(content=html_report(analysis.document.filename, analysis.proposed_change, result), media_type="text/html", headers={"Content-Disposition": f'attachment; filename="rcia-analysis-{analysis.id}.html"'})


@app.get("/api/analysis/{analysis_id}/test-cases.csv")
def export_test_cases(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    result = json.loads(analysis.result_json)
    return Response(content=csv_bytes(result.get("test_cases", [])), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="rcia-test-cases-{analysis.id}.csv"'})


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    stored_path = Path(document.stored_path)
    db.delete(document)
    db.commit()
    stored_path.unlink(missing_ok=True)
    return {"message": "Document and associated analyses were deleted."}
