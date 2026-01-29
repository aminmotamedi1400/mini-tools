# ui.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import platform
import json
import os
import urllib.parse
from pathlib import Path
from datetime import datetime
from indexer import PDFIndexer


class LicenseChecker:
    EXPIRY_DATE = datetime(2026, 3, 1, 0, 0, 0)
    
    @staticmethod
    def is_valid():
        return datetime.now() < LicenseChecker.EXPIRY_DATE
    
    @staticmethod
    def days_remaining():
        delta = LicenseChecker.EXPIRY_DATE - datetime.now()
        return max(0, delta.days)


class PDFOpener:
    """Handle PDF opening with different viewers"""
    
    SUMATRA_PATHS = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.expanduser(r"~\AppData\Local\SumatraPDF\SumatraPDF.exe"),
        r"C:\Users\Public\SumatraPDF\SumatraPDF.exe",
    ]
    
    EDGE_PATHS = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    
    @classmethod
    def find_sumatra(cls):
        """Find SumatraPDF installation"""
        for path in cls.SUMATRA_PATHS:
            if os.path.exists(path):
                return path
        
        # Check in PATH
        try:
            result = subprocess.run(
                ["where", "SumatraPDF.exe"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                if os.path.exists(path):
                    return path
        except:
            pass
        
        return None
    
    @classmethod
    def find_edge(cls):
        """Find Edge installation"""
        for path in cls.EDGE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    @classmethod
    def open_pdf(cls, pdf_path, page=1, search_query=""):
        """
        Open PDF with best available viewer
        Returns: (success: bool, message: str, viewer: str)
        """
        sumatra = cls.find_sumatra()
        
        if sumatra:
            return cls._open_with_sumatra(sumatra, pdf_path, page, search_query)
        else:
            edge = cls.find_edge()
            if edge:
                return cls._open_with_edge(edge, pdf_path, page, search_query)
            else:
                return cls._open_with_default(pdf_path)
    
    @classmethod
    def _open_with_sumatra(cls, sumatra_path, pdf_path, page, search_query):
        """
        Open PDF with SumatraPDF
        
        SumatraPDF command line options:
        -page <pagenum>     : open at specified page
        -search <text>      : search for text and highlight
        -reuse-instance     : reuse existing window
        -zoom <level>       : fit page, fit width, fit content, or percentage
        """
        try:
            cmd = [sumatra_path]
            
            # Add page number
            if page and page > 0:
                cmd.extend(["-page", str(page)])
            
            # Add search query
            if search_query:
                # Clean query for search
                clean_query = search_query.strip().strip('"')
                if clean_query:
                    cmd.extend(["-search", clean_query])
            
            # Reuse existing instance
            cmd.append("-reuse-instance")
            
            # Add PDF path (must be last)
            cmd.append(pdf_path)
            
            subprocess.Popen(cmd)
            
            msg = f"Opened with SumatraPDF at page {page}"
            if search_query:
                msg += f" (searching: '{search_query}')"
            
            return True, msg, "SumatraPDF"
            
        except Exception as e:
            return False, f"SumatraPDF error: {e}", "SumatraPDF"
    
    @classmethod
    def _open_with_edge(cls, edge_path, pdf_path, page, search_query):
        """Open PDF with Edge (fallback)"""
        try:
            # Build file URL
            path_normalized = pdf_path.replace('\\', '/')
            path_parts = path_normalized.split('/')
            encoded_parts = [urllib.parse.quote(part) for part in path_parts]
            encoded_path = '/'.join(encoded_parts)
            
            pdf_url = f"file:///{encoded_path}#page={page}"
            
            subprocess.Popen([edge_path, pdf_url])
            
            msg = f"Opened with Edge at page {page}"
            if search_query:
                msg += f" (use Ctrl+F to search: '{search_query}')"
            
            return True, msg, "Edge"
            
        except Exception as e:
            return False, f"Edge error: {e}", "Edge"
    
    @classmethod
    def _open_with_default(cls, pdf_path):
        """Open with system default (last resort)"""
        try:
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', pdf_path])
            else:
                subprocess.run(['xdg-open', pdf_path])
            
            return True, "Opened with default viewer (manual navigation needed)", "Default"
            
        except Exception as e:
            return False, f"Cannot open PDF: {e}", "None"
    
    @classmethod
    def get_viewer_status(cls):
        """Get status of available viewers"""
        sumatra = cls.find_sumatra()
        edge = cls.find_edge()
        
        status = []
        if sumatra:
            status.append(f"✓ SumatraPDF: {sumatra}")
        else:
            status.append("✗ SumatraPDF: Not found")
        
        if edge:
            status.append(f"✓ Edge: {edge}")
        else:
            status.append("✗ Edge: Not found")
        
        return "\n".join(status)


class PDFSearchUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Indexer & Search")
        self.root.geometry("1000x800")
        
        if not LicenseChecker.is_valid():
            messagebox.showerror(
                "License Expired",
                "Trial period has ended.\nExpired on 2026-03-01."
            )
            self.root.destroy()
            return
        
        self.indexer = None
        self.pdf_folder = ""
        self.search_history = []
        self.history_file = None
        self.current_results = []
        self.current_query = ""
        
        self._setup_ui()
        self._show_trial_warning()
        self._check_viewers()
    
    def _check_viewers(self):
        """Check available PDF viewers on startup"""
        sumatra = PDFOpener.find_sumatra()
        if sumatra:
            self._log(f"✓ SumatraPDF found: {sumatra}")
            self.viewer_label.config(text="PDF Viewer: SumatraPDF ✓", foreground="green")
        else:
            edge = PDFOpener.find_edge()
            if edge:
                self._log(f"⚠ SumatraPDF not found, using Edge")
                self.viewer_label.config(text="PDF Viewer: Edge (install SumatraPDF for better experience)", foreground="orange")
            else:
                self._log("⚠ No PDF viewer found")
                self.viewer_label.config(text="PDF Viewer: Default (limited features)", foreground="red")
    
    def _show_trial_warning(self):
        days = LicenseChecker.days_remaining()
        if days <= 7:
            messagebox.showwarning(
                "Trial Expiring Soon",
                f"Trial expires in {days} days.\nExpiry: 2026-03-01"
            )
    
    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Header with trial info and viewer status
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        days = LicenseChecker.days_remaining()
        trial_label = ttk.Label(
            header_frame,
            text=f"Trial: {days} days remaining",
            foreground="red",
            font=("Arial", 9, "bold")
        )
        trial_label.grid(row=0, column=0, sticky=tk.W)
        
        self.viewer_label = ttk.Label(
            header_frame,
            text="PDF Viewer: Checking...",
            foreground="gray",
            font=("Arial", 9)
        )
        self.viewer_label.grid(row=0, column=1, sticky=tk.E)
        
        # Indexing section
        index_frame = ttk.LabelFrame(main_frame, text="Indexing", padding="10")
        index_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        index_frame.columnconfigure(1, weight=1)
        
        ttk.Label(index_frame, text="PDF Folder:").grid(row=0, column=0, sticky=tk.W)
        
        self.folder_entry = ttk.Entry(index_frame, width=60)
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Button(index_frame, text="Browse", command=self._browse_folder).grid(row=0, column=2)
        
        btn_frame = ttk.Frame(index_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(btn_frame, text="Build Index", command=self._build_index).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Update Index", command=self._update_index).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Index", command=self._load_index).pack(side=tk.LEFT)
        
        self.index_status = ttk.Label(index_frame, text="Status: No index loaded", foreground="red")
        self.index_status.grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        # Search section
        search_frame = ttk.LabelFrame(main_frame, text='Search (use "quotes" for exact phrase)', padding="10")
        search_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Query:").grid(row=0, column=0, sticky=tk.W)
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 12))
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_entry.bind('<Return>', lambda e: self._search())
        
        ttk.Button(search_frame, text="Search", command=self._search).grid(row=0, column=2)
        
        # History dropdown
        ttk.Label(search_frame, text="History:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.history_combo = ttk.Combobox(search_frame, state="readonly")
        self.history_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        self.history_combo.bind('<<ComboboxSelected>>', self._on_history_select)
        
        # Results header
        results_header_frame = ttk.Frame(main_frame)
        results_header_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        results_header_frame.columnconfigure(0, weight=1)
        
        self.results_label = ttk.Label(results_header_frame, text="Results: None", font=("Arial", 10, "bold"))
        self.results_label.grid(row=0, column=0, sticky=tk.W)
        
        btn_export = ttk.Frame(results_header_frame)
        btn_export.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(btn_export, text="📋 Copy", command=self._copy_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_export, text="💾 Save", command=self._save_results).pack(side=tk.LEFT, padx=2)
        
        # Results info
        self.results_info = ttk.Label(
            main_frame,
            text="💡 Click on results to open PDF at exact page with search highlighting",
            foreground="gray",
            font=("Arial", 8)
        )
        self.results_info.grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        # Results text
        results_text_frame = ttk.Frame(main_frame)
        results_text_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_text_frame.columnconfigure(0, weight=1)
        results_text_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(
            results_text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            height=18,
            cursor="arrow",
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(results_text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure tags
        self.results_text.tag_config("title", font=("Consolas", 10, "bold"), foreground="#1a5f7a")
        self.results_text.tag_config("page_info", foreground="#666666")
        self.results_text.tag_config("score", foreground="#2e7d32", font=("Consolas", 9))
        self.results_text.tag_config("snippet", font=("Consolas", 9), lmargin1=20, lmargin2=20)
        self.results_text.tag_config("link", foreground="#0066cc", underline=True)
        self.results_text.tag_config("separator", foreground="#cccccc")
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 8),
            height=5,
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.pdf_folder = folder
            self._setup_paths()
            self._load_history()
            self._try_auto_load()
    
    def _setup_paths(self):
        index_dir = Path(self.pdf_folder) / ".index"
        index_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = index_dir / "search_history.json"
    
    def _try_auto_load(self):
        index_path = Path(self.pdf_folder) / ".index" / "pdf_index.json"
        if index_path.exists():
            self._load_index()
    
    def _log(self, message):
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _build_index(self):
        self._do_build(incremental=False)
    
    def _update_index(self):
        self._do_build(incremental=True)
    
    def _do_build(self, incremental):
        if not LicenseChecker.is_valid():
            messagebox.showerror("License Expired", "Trial period has ended")
            return
        
        if not self.folder_entry.get():
            messagebox.showwarning("Warning", "Please select a PDF folder")
            return
        
        self.pdf_folder = self.folder_entry.get()
        self._setup_paths()
        
        def build_thread():
            try:
                mode = "Updating" if incremental else "Building"
                self._log(f"{mode} index...")
                
                self.indexer = PDFIndexer(self.pdf_folder, "pdf_index.json")
                
                original_print = print
                def log_print(*args, **kwargs):
                    message = ' '.join(map(str, args))
                    self.root.after(0, lambda: self._log(message))
                
                import builtins
                builtins.print = log_print
                
                self.indexer.build_index(incremental=incremental)
                
                builtins.print = original_print
                
                self.root.after(0, lambda: self.index_status.config(
                    text=f"Status: Index ready ({self.indexer.index['metadata']['total_documents']} docs, {self.indexer.index['metadata']['total_pages']} pages)",
                    foreground="green"
                ))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Index built successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        thread = threading.Thread(target=build_thread, daemon=True)
        thread.start()
    
    def _load_index(self):
        if not LicenseChecker.is_valid():
            messagebox.showerror("License Expired", "Trial period has ended")
            return
        
        if not self.pdf_folder:
            self.pdf_folder = self.folder_entry.get()
        
        if not self.pdf_folder:
            messagebox.showwarning("Warning", "Please select a PDF folder first")
            return
        
        self._setup_paths()
        
        try:
            self.indexer = PDFIndexer(self.pdf_folder, "pdf_index.json")
            if self.indexer.load_index():
                self.index_status.config(
                    text=f"Status: Index loaded ({self.indexer.index['metadata']['total_documents']} docs, {self.indexer.index['metadata']['total_pages']} pages)",
                    foreground="green"
                )
                self._log("Index loaded successfully")
                self._load_history()
            else:
                self.index_status.config(text="Status: No index found", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Error loading index: {str(e)}")
    
    def _search(self):
        if not LicenseChecker.is_valid():
            messagebox.showerror("License Expired", "Trial period has ended")
            return
        
        if not self.indexer or not self.indexer.index:
            messagebox.showwarning("Warning", "Please load or build an index first")
            return
        
        query = self.search_entry.get().strip()
        if not query:
            return
        
        try:
            self.current_query = query
            self.current_results = self.indexer.search(query)
            self._add_to_history(query)
            self._display_results(query)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Search error: {str(e)}")
    
    def _display_results(self, query):
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        
        if not self.current_results:
            self.results_label.config(text="Results: No matches found")
            self.results_text.insert(tk.END, f'No results found for "{query}".\n\n')
            self.results_text.insert(tk.END, "Tips:\n")
            self.results_text.insert(tk.END, '  • Use "quotes" for exact phrase search\n')
            self.results_text.insert(tk.END, "  • Try different keywords\n")
            self.results_text.insert(tk.END, "  • Check spelling\n")
            self.results_text.config(state='disabled')
            return
        
        self.results_label.config(text=f"Results: {len(self.current_results)} matches found")
        
        for idx, result in enumerate(self.current_results):
            # Result number and document name
            self.results_text.insert(tk.END, f"{idx+1}. ", "title")
            self.results_text.insert(tk.END, f"{result['document']}\n", "title")
            
            # Page and score info
            self.results_text.insert(tk.END, f"   Page: {result['page']}", "page_info")
            self.results_text.insert(tk.END, f"  |  Score: {result['score']}\n", "score")
            
            # Snippet
            self.results_text.insert(tk.END, f"\n   {result['snippet']}\n\n", "snippet")
            
            # Clickable link
            link_tag = f"link_{idx}"
            self.results_text.insert(tk.END, "   ")
            self.results_text.insert(tk.END, f"📄 Open at page {result['page']} → Search: \"{query}\"", link_tag)
            self.results_text.insert(tk.END, "\n")
            
            # Configure link
            self.results_text.tag_config(link_tag, foreground="#0066cc", underline=True)
            self.results_text.tag_bind(
                link_tag, "<Button-1>",
                lambda e, p=result['path'], pg=result['page'], q=query: self._open_pdf(p, pg, q)
            )
            self.results_text.tag_bind(link_tag, "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
            self.results_text.tag_bind(link_tag, "<Leave>", lambda e: self.results_text.config(cursor="arrow"))
            
            # Separator
            self.results_text.insert(tk.END, "\n" + "─" * 80 + "\n\n", "separator")
        
        self.results_text.config(state='disabled')
        self._log(f"Found {len(self.current_results)} results for '{query}'")
    
    def _open_pdf(self, path, page, query):
        """Open PDF using best available viewer"""
        # Clean query for search
        search_query = query.strip().strip('"')
        
        success, message, viewer = PDFOpener.open_pdf(path, page, search_query)
        
        if success:
            self._log(f"✓ {message}")
        else:
            self._log(f"✗ {message}")
            messagebox.showerror("Error", message)
    
    def _add_to_history(self, query):
        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            self.search_history = self.search_history[:20]
            self.history_combo['values'] = self.search_history
            self._save_history()
    
    def _on_history_select(self, event):
        selected = self.history_combo.get()
        if selected:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, selected)
            self._search()
    
    def _load_history(self):
        if self.history_file and self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.search_history = json.load(f)
                    self.history_combo['values'] = self.search_history
            except:
                pass
    
    def _save_history(self):
        if self.history_file:
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.search_history, f, ensure_ascii=False)
            except:
                pass
    
    def _copy_results(self):
        if not self.current_results:
            messagebox.showinfo("Info", "No results to copy")
            return
        
        text = self._format_results_text()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log("Results copied to clipboard")
        messagebox.showinfo("Copied", "Results copied to clipboard!")
    
    def _save_results(self):
        if not self.current_results:
            messagebox.showinfo("Info", "No results to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
            initialdir=self.pdf_folder
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_results, f, ensure_ascii=False, indent=2)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self._format_results_text())
                self._log(f"Results saved: {file_path}")
                messagebox.showinfo("Saved", f"Results saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save: {e}")
    
    def _format_results_text(self):
        lines = [
            f"Search Results for: {self.current_query}",
            f"Total: {len(self.current_results)} matches",
            "=" * 60, ""
        ]
        
        for idx, r in enumerate(self.current_results, 1):
            lines.append(f"{idx}. {r['document']}")
            lines.append(f"   Page: {r['page']}  |  Score: {r['score']}")
            lines.append(f"   Path: {r['path']}")
            lines.append("")
            lines.append(f"   {r['snippet']}")
            lines.append("")
            lines.append("-" * 60)
            lines.append("")
        
        return "\n".join(lines)


def main():
    root = tk.Tk()
    app = PDFSearchUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()