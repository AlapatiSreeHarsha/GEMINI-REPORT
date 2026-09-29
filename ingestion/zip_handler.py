from __future__ import annotations
import shutil, zipfile
from pathlib import Path, PurePosixPath
from config.settings import MAX_ZIP_ENTRIES, MAX_ZIP_UNCOMPRESSED_BYTES
CODE_EXTENSIONS = {".c", ".h", ".cpp", ".cc", ".java", ".py"}

def _safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) > MAX_ZIP_ENTRIES: raise ValueError("ZIP contains too many files.")
        if sum(e.file_size for e in entries) > MAX_ZIP_UNCOMPRESSED_BYTES: raise ValueError("ZIP expands beyond 500 MB.")
        for entry in entries:
            name = entry.filename.replace("\\", "/"); rel = PurePosixPath(name)
            if rel.is_absolute() or ".." in rel.parts: raise ValueError(f"Unsafe ZIP path: {name}")
            if entry.is_dir(): continue
            target = (destination / Path(*rel.parts)).resolve()
            if destination.resolve() not in target.parents: raise ValueError(f"Unsafe ZIP path: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(entry) as src, target.open("wb") as dst: shutil.copyfileobj(src, dst)

def extract_submissions(archive: Path, destination: Path) -> list[dict]:
    destination.mkdir(parents=True, exist_ok=True); _safe_extract(Path(archive), destination)
    root = destination
    nested = [p for p in destination.iterdir() if p.is_dir()]
    if len(nested) == 1 and not any(p.is_file() and p.suffix.lower() in CODE_EXTENSIONS for p in destination.iterdir()): root = nested[0]
    out = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        files = list(folder.rglob("*")); code = sorted(p for p in files if p.is_file() and p.suffix.lower() in CODE_EXTENSIONS)
        pdfs = sorted(p for p in files if p.is_file() and p.suffix.lower() == ".pdf")
        if code or pdfs: out.append({"student_id": folder.name, "root": folder, "code_files": code, "pdf_files": pdfs})
    code = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in CODE_EXTENSIONS)
    pdfs = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    if code or pdfs: out.append({"student_id": root.name, "root": root, "code_files": code, "pdf_files": pdfs})
    return out
