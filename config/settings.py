import os
APP_TITLE = "Student Lab Notebook Analyzer"
MAX_ZIP_UNCOMPRESSED_BYTES = 500 * 1024 * 1024
MAX_ZIP_ENTRIES = 5000
STORAGE_ROOT = os.getenv("LAB_ANALYZER_STORAGE", "storage")
