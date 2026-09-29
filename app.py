from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from analysis.pipeline import analyze_submissions
from ai.prompts import ANALYSIS_PROMPT
from ingestion.zip_handler import extract_submissions
from reports.renderer import render_report

st.set_page_config(page_title="Student Lab Notebook Analyzer", page_icon="📘", layout="wide")
st.title("Student Lab Notebook Analyzer")
st.caption("Extract evidence once, reuse it to regenerate student reports.")
tab_process, tab_regen = st.tabs(["Process a ZIP", "Regenerate from evidence"])

with tab_process:
    uploaded = st.file_uploader("Student submissions ZIP", type=["zip"])
    api_key = st.text_input("Gemini API key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    version = st.text_input("Analysis prompt version", value="2.0", key="analysis_version_v2")
    st.caption("Submitted totals are counted from the ZIP. Required and extra counts are left unspecified unless assignment evidence identifies them.")
    prompt = st.text_area("Analysis prompt", value=ANALYSIS_PROMPT, height=260, key="analysis_prompt_v2")

    if st.button("Generate reports", type="primary", disabled=uploaded is None):
        with tempfile.TemporaryDirectory(prefix="lab-analyzer-") as tmp:
            archive = Path(tmp) / "submissions.zip"
            archive.write_bytes(uploaded.getvalue())
            try:
                submissions = extract_submissions(archive, Path(tmp) / "extracted")
                if not submissions:
                    st.error("No student folders with source code were found.")
                else:
                    progress = st.progress(0)
                    with st.spinner("Checking which Gemini model responds and analyzing submissions…"):
                        result = analyze_submissions(
                            submissions,
                            Path("storage"),
                            api_key,
                            prompt_version=version,
                            progress_callback=lambda n, total: progress.progress(n / total),
                            analysis_prompt=prompt,
                        )
                    output = Path(tmp) / "reports"
                    output.mkdir()
                    for student_id, data in result["students"].items():
                        (output / f"{student_id}_observations.json").write_text(
                            json.dumps(data["handwriting"], indent=2), encoding="utf-8")
                        (output / f"{student_id}_code_evidence.json").write_text(
                            json.dumps(data["code"], indent=2), encoding="utf-8")
                        (output / f"{student_id}_analysis.json").write_text(
                            json.dumps(data["analysis"], indent=2), encoding="utf-8")
                        (output / f"{student_id}_lab_notebook.html").write_text(
                            render_report(data["analysis"]), encoding="utf-8")
                    (output / "similarity_results.json").write_text(
                        json.dumps(result["similarity"], indent=2), encoding="utf-8")
                    bundle = Path(tmp) / "lab_notebook_reports.zip"
                    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive_zip:
                        for path in output.iterdir():
                            archive_zip.write(path, path.name)
                    st.success(f"Processed {len(result['students'])} student submissions.")
                    st.download_button("Download reports and JSON", bundle.read_bytes(), bundle.name, "application/zip")
                    with st.expander("Review similarity flags"):
                        st.json(result["similarity"])
            except Exception as exc:
                st.exception(exc)

with tab_regen:
    st.write("Regenerate analysis from saved handwriting evidence without rereading the PDFs.")
    evidence_files = st.file_uploader("Handwriting evidence JSON", type=["json"], accept_multiple_files=True, key="evidence")
    regen_zip = st.file_uploader("Matching student ZIP", type=["zip"], key="regen_zip")
    regen_key = st.text_input("Gemini API key", value=os.getenv("GEMINI_API_KEY", ""), type="password", key="regen_key")
    regen_version = st.text_input("New analysis prompt version", value="2.0", key="regen_version_v2")
    regen_prompt = st.text_area("Updated analysis prompt", value=ANALYSIS_PROMPT, height=260, key="regen_prompt_v2")

    if evidence_files and regen_zip and st.button("Regenerate reports"):
        cached = {
            Path(file.name).stem.replace("_observations", ""): json.loads(file.getvalue())
            for file in evidence_files
        }
        with tempfile.TemporaryDirectory(prefix="lab-regen-") as tmp:
            archive = Path(tmp) / "input.zip"
            archive.write_bytes(regen_zip.getvalue())
            submissions = extract_submissions(archive, Path(tmp) / "input")
            result = analyze_submissions(
                submissions,
                Path("storage"),
                regen_key,
                prompt_version=regen_version,
                cached_evidence=cached,
                analysis_prompt=regen_prompt,
            )
            bundle = Path(tmp) / "reports.zip"
            with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive_zip:
                for student_id, data in result["students"].items():
                    archive_zip.writestr(f"{student_id}_analysis.json", json.dumps(data["analysis"], indent=2))
                    archive_zip.writestr(f"{student_id}_lab_notebook.html", render_report(data["analysis"]))
                archive_zip.writestr("similarity_results.json", json.dumps(result["similarity"], indent=2))
            st.download_button("Download regenerated reports", bundle.read_bytes(), bundle.name, "application/zip")
