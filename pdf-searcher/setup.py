# setup.py
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": [
        "tkinter", 
        "json", 
        "re", 
        "pathlib", 
        "datetime", 
        "collections", 
        "threading", 
        "math", 
        "hashlib", 
        "PyPDF2",
        "subprocess",
        "platform",
        "webbrowser"
    ],
    "include_files": [],
    "excludes": ["matplotlib", "numpy", "scipy", "pandas", "PIL", "cv2"],
}

base = None
if sys.platform == "win32":
    base = "gui"

setup(
    name="PDFSearcher",
    version="1.0",
    description="PDF Indexer and Search Tool with BM25 - Trial Version (30 days)",
    options={"build_exe": build_exe_options},
    executables=[Executable("ui.py", base=base, target_name="PDFSearcher.exe")]
)