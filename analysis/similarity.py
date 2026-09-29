from __future__ import annotations
import re
from difflib import SequenceMatcher
from itertools import combinations

def _normalize(code: str) -> str:
    code = re.sub(r"/\*.*?\*/|//[^\n]*", " ", code, flags=re.S)
    code = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "STR", code)
    return re.sub(r"\s+", "", code)

def compare_students(evidence_by_student: dict) -> list[dict]:
    items = [(sid, f["file"], f["source"]) for sid, data in evidence_by_student.items() for f in data["code"]]
    flags = []
    for a, b in combinations(items, 2):
        if a[0] == b[0]: continue
        left, right = _normalize(a[2]), _normalize(b[2])
        if min(len(left), len(right)) < 45: continue
        score = SequenceMatcher(None, left, right, autojunk=False).ratio()
        if score >= 0.72:
            flags.append({"student_a": a[0], "file_a": a[1], "student_b": b[0], "file_b": b[1],
                          "similarity": round(score, 3), "status": "manual_review", "method": "normalized_source"})
    return sorted(flags, key=lambda x: x["similarity"], reverse=True)
