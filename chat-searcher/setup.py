# setup.py
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["tkinter", "json", "re", "pathlib", "datetime", "collections", "threading"],
    "include_files": [],
    "excludes": ["matplotlib", "numpy", "scipy"],
}

base = None
if sys.platform == "win32":
    base = "gui"

setup(
    name="ChatSearcher",
    version="1.0",
    description="Chat History Indexer and Search Tool - Trial Version",
    options={"build_exe": build_exe_options},
    executables=[Executable("chat_ui.py", base=base, target_name="ChatSearcher.exe")]
)