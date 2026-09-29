# Student Lab Notebook Analyzer

Streamlit application for analyzing a ZIP of student programming submissions. The pipeline separates reusable evidence extraction from prompt-driven analysis and HTML rendering.

## Run

1. Use Python 3.10 or newer.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` (or enter the key in the app).
4. Start the UI: `streamlit run app.py`

The app accepts student folders containing C/C++/Java/Python source files and optional handwritten PDF observations. It automatically probes available Gemini models in preference order and uses the first model that successfully responds to a small request. If `gcc`/`g++` is installed, C/C++ syntax and compiler warnings are collected. Other static findings are heuristic and should be reviewed.

## Evidence and cache

PDF evidence is stored in `storage/handwriting_json/`. Each entry records the PDF SHA-256, extraction version, model, and timestamp. A cache hit requires both a matching hash and extraction version. Changed PDFs are re-extracted. Code evidence is cached under `storage/code_json/` by source SHA-256. Analysis outputs are stored separately in `storage/analysis_json/` and named by prompt version. The HTML renderer is deterministic and makes no Gemini call.

To regenerate analysis, use the app's second tab, upload saved `*_observations.json` files and the matching ZIP, then select a new analysis prompt version. This runs the analysis stage without passing PDFs back to the handwriting extractor.

## Output

The report ZIP contains per-student handwriting JSON, analysis JSON, and HTML, plus `similarity_results.json`. Similarity uses normalized source-text comparison as a review aid; it is not a plagiarism verdict. Configure required program counts and richer AST/token comparison for the course before relying on similarity results operationally.

## Limitations

The model prompt provides a general Week 4 / functions and recursion rubric; assignment-specific counts, course metadata, and grading criteria should be configured for each class. The reference examples are advisory reports, not ground truth. Review AI findings and similarity flags before sharing them with students.
