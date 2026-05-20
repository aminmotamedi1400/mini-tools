#!/usr/bin/env python3
"""
Merge PDFs using an existing shell script via a Tkinter GUI.

Command line that will ultimately be executed:
    ./merge_pdf.sh all_pages.pdf chapter1.pdf chapter2.pdf appendix.pdf

The GUI lets you:
    • Choose the output PDF name (first argument to the script)
    • Add any number of input PDF files
    • Click “Merge” and see a status message.
"""

import os
import subprocess
import sys
from pathlib import Path
from tkinter import (
    Tk, Button, Listbox, Entry, Label,
    END, SINGLE, MULTIPLE, DISABLED, NORMAL,
    filedialog, messagebox
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

SCRIPT_NAME = "merge_pdf.sh"           # the script that does the merging
SCRIPT_DIR  = Path(__file__).parent   # folder containing this .py file
SCRIPT_PATH = SCRIPT_DIR / SCRIPT_NAME

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def run_merge(output_file: str, input_files: list[str]) -> None:
    """
    Execute the merge_pdf.sh script with the given filenames.
    Raises subprocess.CalledProcessError on failure.
    """
    # Build command: ["./merge_pdf.sh", output.pdf, in1.pdf, in2.pdf, …]
    cmd = [str(SCRIPT_PATH), output_file] + input_files
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)  # will raise if non‑zero exit code


# --------------------------------------------------------------------------- #
# Tkinter Application class
# --------------------------------------------------------------------------- #

class MergeApp:
    def __init__(self, root: Tk):
        self.root = root
        root.title("PDF Merger")
        root.resizable(False, False)

        # ----- Output file -----
        Label(root, text="Output PDF:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.out_entry = Entry(root, width=40)
        self.out_entry.grid(row=0, column=1, padx=5, pady=5)

        Button(root, text="Browse…", command=self.choose_output).grid(
            row=0, column=2, padx=5, pady=5
        )

        # ----- Input files list -----
        Label(root, text="Input PDFs:").grid(row=1, column=0, sticky='nw', padx=5, pady=5)
        self.listbox = Listbox(
            root,
            width=55,
            height=8,
            selectmode=MULTIPLE
        )
        self.listbox.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        Button(root, text="Add PDFs…", command=self.add_files).grid(
            row=2, column=1, sticky='w', padx=5, pady=5
        )
        Button(root, text="Remove Selected", command=self.remove_selected).grid(
            row=2, column=1, sticky='e', padx=5, pady=5
        )

        # ----- Merge button -----
        self.merge_btn = Button(root, text="Merge PDFs", command=self.start_merge)
        self.merge_btn.grid(row=3, column=0, columnspan=3, pady=10)

    # ----------------------------------------------------------------------- #
    # UI callbacks
    # ----------------------------------------------------------------------- #

    def choose_output(self):
        """Open a Save‑As dialog to pick the output PDF name."""
        file_path = filedialog.asksaveasfilename(
            title="Select Output PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if file_path:
            self.out_entry.delete(0, END)
            self.out_entry.insert(0, file_path)

    def add_files(self):
        """Open a File dialog to pick one or more PDFs to merge."""
        paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf")],
        )
        for path in paths:
            if path not in self.listbox.get(0, END):
                self.listbox.insert(END, path)

    def remove_selected(self):
        """Remove the currently selected items from the listbox."""
        selected = list(self.listbox.curselection())
        for index in reversed(selected):  # reverse to avoid shifting indices
            self.listbox.delete(index)

    def start_merge(self):
        """Validate inputs and run the merge script in a subprocess."""
        out_file = self.out_entry.get().strip()
        if not out_file:
            messagebox.showerror("Error", "Please specify an output PDF file.")
            return

        input_files = list(self.listbox.get(0, END))
        if not input_files:
            messagebox.showerror("Error", "Add at least one input PDF file to merge.")
            return

        # Disable UI during processing
        self.merge_btn.config(state=DISABLED)
        try:
            run_merge(out_file, input_files)
            messagebox.showinfo(
                "Success",
                f"PDFs merged successfully into:\n{out_file}"
            )
        except subprocess.CalledProcessError as exc:
            # Capture stderr from the script if available
            msg = (
                f"An error occurred while merging PDFs.\n"
                f"Command exited with status {exc.returncode}."
            )
            messagebox.showerror("Merge Failed", msg)
        finally:
            self.merge_btn.config(state=NORMAL)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main():
    # Basic sanity check: is the merge script present and executable?
    if not SCRIPT_PATH.is_file() or not os.access(SCRIPT_PATH, os.X_OK):
        print(f"Error: Merge script '{SCRIPT_PATH}' not found or not executable.")
        sys.exit(1)

    root = Tk()
    app = MergeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
