from __future__ import annotations
import re, shutil, subprocess
from pathlib import Path

def inspect_code(path: Path) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower(); language = {".c":"C", ".h":"C", ".cpp":"C++", ".cc":"C++", ".java":"Java", ".py":"Python"}.get(suffix, "Text")
    functions = re.findall(r"(?m)^\s*(?:[\w*\s]+)\s+([A-Za-z_]\w*)\s*\([^;\n]*\)\s*\{", source)
    includes = re.findall(r"(?m)^\s*#\s*include\s*[<\"]([^>\"]+)", source)
    result = {"file": path.name, "language": language, "source": source, "functions": functions, "includes": includes,
              "line_count": len(source.splitlines()), "compile_success": None, "errors": [], "warnings": [], "static_flags": []}
    if suffix in {".c", ".cpp", ".cc"} and shutil.which("gcc" if suffix == ".c" else "g++"):
        compiler = "gcc" if suffix == ".c" else "g++"
        try:
            proc = subprocess.run([compiler, "-fsyntax-only", "-Wall", "-Wextra", str(path)], capture_output=True, text=True, timeout=12)
            result["compile_success"] = proc.returncode == 0
            result["errors"] = [x for x in proc.stderr.splitlines() if "error:" in x]
            result["warnings"] = [x for x in proc.stderr.splitlines() if "warning:" in x]
        except subprocess.TimeoutExpired: result["errors"] = ["Compiler timed out"]
    elif suffix == ".c": result["compile_note"] = "gcc unavailable; compilation was not checked"
    for pattern, label in [(r"\bgets\s*\(", "uses unsafe/obsolete gets()"), (r"\bstrcpy\s*\(", "uses strcpy(); check destination capacity"), (r"\bscanf\s*\([^\n]*%s", "scanf %s may overflow its destination")]:
        if re.search(pattern, source): result["static_flags"].append(label)
    return result
