from __future__ import annotations
import json
from pathlib import Path
from google import genai
from ai.prompts import ANALYSIS_PROMPT
from code_analysis.analyzer import inspect_code
from handwriting.cache import load_or_extract
from analysis.similarity import compare_students
from utils.hashing import sha256_file
from ai.model_selector import select_available_model, generate_content_resilient

def _cached_code(path: Path, student_id: str, storage: Path) -> dict:
    digest = sha256_file(path)
    folder = storage / "code_json" / student_id
    folder.mkdir(parents=True, exist_ok=True)
    cache = folder / f"{digest}.json"
    if cache.exists():
        try:
            saved = json.loads(cache.read_text(encoding="utf-8"))
            if saved.get("source_hash") == digest:
                return saved
        except (ValueError, OSError):
            pass
    result = inspect_code(path)
    result["source_hash"] = digest
    cache.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

def _analysis(client, model: str, student_id: str, code: list[dict], handwriting: dict, version: str, required_count: int | None, analysis_prompt: str) -> dict:
    evidence = {"student_id": student_id, "course": "C Programming Lab", "week": "Week 4", "topic": "Functions & Recursion",
                "required_count": required_count, "code": [{k:v for k,v in f.items() if k != "source"} | {"source": f["source"]} for f in code],
                "handwriting": handwriting}
    prompt = analysis_prompt + f"\nPrompt version: {version}\n" + json.dumps(evidence, ensure_ascii=False)
    response = generate_content_resilient(client, model, contents=prompt, config={"response_mime_type":"application/json"})
    result = json.loads(response.text); result["student_id"] = student_id; result["prompt_version"] = version
    return result

def analyze_submissions(submissions: list[dict], storage: Path, api_key: str, prompt_version: str,
                        cached_evidence: dict | None = None, progress_callback=None, required_count: int | None = None,
                        analysis_prompt: str | None = None) -> dict:
    if not api_key: raise ValueError("Enter a Gemini API key to run handwriting extraction or student analysis.")
    client = genai.Client(api_key=api_key)
    model = select_available_model(client)
    storage = Path(storage); storage.mkdir(parents=True, exist_ok=True)
    students = {}; evidence = {}
    for index, submission in enumerate(submissions):
        sid = submission["student_id"]
        code = [_cached_code(path, sid, storage) for path in submission["code_files"]]
        pdfs = submission["pdf_files"]
        if cached_evidence and sid in cached_evidence:
            handwriting = cached_evidence[sid]
        elif pdfs:
            # One canonical extraction per PDF; multiple PDFs are recorded together without losing provenance.
            extracted = [load_or_extract(pdf, sid, storage, client, model) for pdf in pdfs]
            handwriting = extracted[0] if len(extracted) == 1 else {"student_id": sid, "source_pdfs": extracted,
                "observations": [o for e in extracted for o in e.get("observations", [])], "unreadable_sections": [u for e in extracted for u in e.get("unreadable_sections", [])]}
        else:
            handwriting = {"student_id": sid, "source_pdf": None, "observations": [], "unreadable_sections": [], "note": "No handwritten PDF found."}
        analysis = _analysis(client, model, sid, code, handwriting, prompt_version, required_count, analysis_prompt or ANALYSIS_PROMPT)
        analysis["model"] = model
        if required_count is None:
            analysis["required_count"] = None
            analysis["extra_count"] = None
        students[sid] = {"handwriting": handwriting, "analysis": analysis, "code": code}; evidence[sid] = {"code": code}
        out = storage / "analysis_json"; out.mkdir(parents=True, exist_ok=True)
        (out / f"{sid}_{prompt_version}.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        if progress_callback: progress_callback(index + 1, len(submissions))
    return {"students": students, "similarity": compare_students(evidence)}
