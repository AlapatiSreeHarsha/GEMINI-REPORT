from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from utils.hashing import sha256_file
from ai.model_selector import generate_content_resilient

EXTRACTION_VERSION = "1.0"
def load_or_extract(pdf: Path, student_id: str, storage: Path, client, model: str) -> dict:
    digest = sha256_file(pdf); folder = storage / "handwriting_json"; folder.mkdir(parents=True, exist_ok=True)
    cache = folder / f"{student_id}_{pdf.stem}.json"
    if cache.exists():
        try:
            saved = json.loads(cache.read_text(encoding="utf-8"))
            if saved.get("source_hash") == digest and saved.get("extraction_version") == EXTRACTION_VERSION: return saved
        except (ValueError, OSError): pass
    from google.genai import types
    prompt = "Read this student's handwritten programming-lab observation PDF. Extract only claims actually written. Return JSON object with student_id, source_pdf, pages (array of page numbers), observations (array of {problem,text,page,confidence}), unreadable_sections (array). Do not infer missing writing. confidence must be high, medium, or low."
    response = generate_content_resilient(client, model, contents=[prompt, types.Part.from_bytes(data=pdf.read_bytes(), mime_type="application/pdf")], config=types.GenerateContentConfig(response_mime_type="application/json"))
    data = json.loads(response.text)
    data.update({"student_id": student_id, "source_pdf": pdf.name, "source_hash": digest,
                 "extraction_version": EXTRACTION_VERSION, "model": model, "created_at": datetime.now(timezone.utc).isoformat()})
    cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
