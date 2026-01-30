# chat_ui.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import urllib.parse
import webbrowser
import os
from pathlib import Path
from datetime import datetime
from chat_indexer import ChatIndexer


class LicenseChecker:
    EXPIRY_DATE = datetime(2026, 3, 1, 0, 0, 0)
    
    @staticmethod
    def is_valid():
        return datetime.now() < LicenseChecker.EXPIRY_DATE
    
    @staticmethod
    def days_remaining():
        delta = LicenseChecker.EXPIRY_DATE - datetime.now()
        return max(0, delta.days)


class ObsidianOpener:
    """Handle opening files in Obsidian"""
    
    @staticmethod
    def detect_vault_name(file_path):
        """
        Try to detect Obsidian vault name from file path.
        Obsidian vaults typically have a .obsidian folder.
        """
        path = Path(file_path).resolve()
        
        # Walk up the directory tree to find .obsidian folder
        for parent in [path] + list(path.parents):
            obsidian_dir = parent / ".obsidian"
            if obsidian_dir.exists() and obsidian_dir.is_dir():
                return parent.name, parent
        
        return None, None
    
    @staticmethod
    def get_relative_path(file_path, vault_path):
        """Get file path relative to vault root (without .md extension for Obsidian)"""
        file_path = Path(file_path).resolve()
        vault_path = Path(vault_path).resolve()
        
        try:
            relative = file_path.relative_to(vault_path)
            # Remove .md extension for Obsidian URI
            relative_str = str(relative)
            if relative_str.endswith('.md'):
                relative_str = relative_str[:-3]
            return relative_str
        except ValueError:
            return None
    
    @classmethod
    def open_in_obsidian(cls, file_path, line_number=None):
        """
        Open a file in Obsidian using URI protocol.
        
        URI format: obsidian://open?vault=VaultName&file=path/to/note
        With line: obsidian://open?vault=VaultName&file=path/to/note&line=123
        
        Returns: (success: bool, message: str)
        """
        vault_name, vault_path = cls.detect_vault_name(file_path)
        
        if not vault_name:
            return False, "Could not detect Obsidian vault. Make sure the file is inside an Obsidian vault."
        
        relative_path = cls.get_relative_path(file_path, vault_path)
        
        if not relative_path:
            return False, "Could not determine relative path within vault."
        
        # Build Obsidian URI
        # Encode the file path for URL
        encoded_file = urllib.parse.quote(relative_path, safe='/')
        encoded_vault = urllib.parse.quote(vault_name)
        
        uri = f"obsidian://open?vault={encoded_vault}&file={encoded_file}"
        
        # Add line number if provided
        if line_number:
            uri += f"&line={line_number}"
        
        try:
            # Open URI using system default handler
            webbrowser.open(uri)
            return True, f"Opened in Obsidian: {relative_path}"
        except Exception as e:
            return False, f"Failed to open Obsidian: {e}"
    
    @classmethod
    def open_with_search(cls, file_path, search_query):
        """
        Open file in Obsidian and trigger search.
        Note: Obsidian URI doesn't support direct text search,
        so we open the file and user can use Ctrl+F.
        
        Alternative: Use obsidian://search?vault=X&query=Y for vault-wide search
        """
        vault_name, vault_path = cls.detect_vault_name(file_path)
        
        if not vault_name:
            return False, "Could not detect Obsidian vault."
        
        relative_path = cls.get_relative_path(file_path, vault_path)
        
        if not relative_path:
            return False, "Could not determine relative path."
        
        encoded_file = urllib.parse.quote(relative_path, safe='/')
        encoded_vault = urllib.parse.quote(vault_name)
        
        # Open the specific file
        uri = f"obsidian://open?vault={encoded_vault}&file={encoded_file}"
        
        try:
            webbrowser.open(uri)
            return True, f"Opened in Obsidian: {relative_path}\nUse Ctrl+F to search for: {search_query}"
        except Exception as e:
            return False, f"Failed to open: {e}"
    
    @classmethod
    def search_in_vault(cls, vault_name, search_query):
        """
        Open Obsidian's global search with a query.
        URI: obsidian://search?vault=VaultName&query=search+terms
        """
        encoded_vault = urllib.parse.quote(vault_name)
        encoded_query = urllib.parse.quote(search_query)
        
        uri = f"obsidian://search?vault={encoded_vault}&query={encoded_query}"
        
        try:
            webbrowser.open(uri)
            return True, f"Searching in vault '{vault_name}' for: {search_query}"
        except Exception as e:
            return False, f"Failed to search: {e}"


class ChatSearchUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat History Search - Obsidian Integration")
        self.root.geometry("950x750")
        
        if not LicenseChecker.is_valid():
            messagebox.showerror(
                "License Expired",
                "Trial period has ended.\nExpired on 2026-03-01."
            )
            self.root.destroy()
            return
        
        self.indexer = None
        self.index_file = "chat_index.json"
        self.chat_folder = ""
        self.vault_name = None
        self.current_results = []
        self.current_query = ""
        
        self._setup_ui()
        self._check_existing_index()
        self._show_trial_warning()
    
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
        main_frame.rowconfigure(4, weight=1)
        
        # Header
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
        
        self.vault_label = ttk.Label(
            header_frame,
            text="Vault: Not detected",
            foreground="gray",
            font=("Arial", 9)
        )
        self.vault_label.grid(row=0, column=1, sticky=tk.E)
        
        # Indexing section
        index_frame = ttk.LabelFrame(main_frame, text="Indexing", padding="10")
        index_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        index_frame.columnconfigure(1, weight=1)
        
        ttk.Label(index_frame, text="Chat Folder:").grid(row=0, column=0, sticky=tk.W)
        
        self.folder_entry = ttk.Entry(index_frame, width=55)
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Button(index_frame, text="Browse", command=self._browse_folder).grid(row=0, column=2)
        
        btn_frame = ttk.Frame(index_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(btn_frame, text="Build Index", command=self._build_index).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Load Index", command=self._load_index).pack(side=tk.LEFT, padx=5)
        
        self.index_status = ttk.Label(index_frame, text="Status: No index loaded", foreground="red")
        self.index_status.grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        # Search section
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding="10")
        search_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Query:").grid(row=0, column=0, sticky=tk.W)
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 12))
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_entry.bind('<Return>', lambda e: self._search())
        
        ttk.Button(search_frame, text="Search", command=self._search).grid(row=0, column=2)
        
        # Vault-wide search button
        ttk.Button(
            search_frame,
            text="🔍 Search in Obsidian",
            command=self._search_in_obsidian
        ).grid(row=0, column=3, padx=(5, 0))
        
        # Results header
        results_header = ttk.Frame(main_frame)
        results_header.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        results_header.columnconfigure(0, weight=1)
        
        self.results_label = ttk.Label(results_header, text="Results: None", font=("Arial", 10, "bold"))
        self.results_label.grid(row=0, column=0, sticky=tk.W)
        
        # Info label
        info_label = ttk.Label(
            results_header,
            text="💡 Click on results to open in Obsidian",
            foreground="gray",
            font=("Arial", 8)
        )
        info_label.grid(row=0, column=1, sticky=tk.E)
        
        # Results text with clickable links
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(
            results_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            height=18,
            cursor="arrow",
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure tags
        self.results_text.tag_config("title", font=("Consolas", 10, "bold"), foreground="#1a5f7a")
        self.results_text.tag_config("meta", foreground="#666666", font=("Consolas", 9))
        self.results_text.tag_config("role_user", foreground="#2e7d32", font=("Consolas", 9, "bold"))
        self.results_text.tag_config("role_assistant", foreground="#1565c0", font=("Consolas", 9, "bold"))
        self.results_text.tag_config("snippet", font=("Consolas", 9), lmargin1=20, lmargin2=20)
        self.results_text.tag_config("link", foreground="#7c3aed", underline=True)
        self.results_text.tag_config("separator", foreground="#cccccc")
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
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
            self.chat_folder = folder
            self._detect_vault(folder)
    
    def _detect_vault(self, folder):
        """Detect Obsidian vault from selected folder"""
        vault_name, vault_path = ObsidianOpener.detect_vault_name(folder)
        
        if vault_name:
            self.vault_name = vault_name
            self.vault_label.config(
                text=f"Vault: {vault_name} ✓",
                foreground="green"
            )
            self._log(f"✓ Detected Obsidian vault: {vault_name}")
        else:
            self.vault_name = None
            self.vault_label.config(
                text="Vault: Not an Obsidian vault",
                foreground="orange"
            )
            self._log("⚠ No .obsidian folder found. Files will open with default app.")
    
    def _check_existing_index(self):
        if Path(self.index_file).exists():
            self._load_index()
    
    def _log(self, message):
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _build_index(self):
        if not LicenseChecker.is_valid():
            messagebox.showerror("License Expired", "Trial period has ended")
            return
        
        if not self.folder_entry.get():
            messagebox.showwarning("Warning", "Please select a chat folder")
            return
        
        self.chat_folder = self.folder_entry.get()
        self._detect_vault(self.chat_folder)
        
        def build_thread():
            try:
                self._log("Building index...")
                self.indexer = ChatIndexer(self.chat_folder, self.index_file)
                
                original_print = print
                def log_print(*args, **kwargs):
                    message = ' '.join(map(str, args))
                    self.root.after(0, lambda: self._log(message))
                
                import builtins
                builtins.print = log_print
                
                self.indexer.build_index()
                
                builtins.print = original_print
                
                self.root.after(0, lambda: self.index_status.config(
                    text=f"Status: Index ready ({self.indexer.index['metadata']['total_conversations']} chats, {self.indexer.index['metadata']['total_messages']} messages)",
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
        
        try:
            self.indexer = ChatIndexer(".", self.index_file)
            if self.indexer.load_index():
                self.index_status.config(
                    text=f"Status: Index loaded ({self.indexer.index['metadata']['total_conversations']} chats)",
                    foreground="green"
                )
                self._log("Index loaded successfully")
                
                # Try to detect vault from first conversation
                if self.indexer.index["conversations"]:
                    first_conv = list(self.indexer.index["conversations"].values())[0]
                    self._detect_vault(first_conv["path"])
            else:
                self.index_status.config(text="Status: No index found", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Error: {str(e)}")
    
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
            self._display_results()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Search error: {str(e)}")
    
    def _display_results(self):
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        
        if not self.current_results:
            self.results_label.config(text="Results: No matches found")
            self.results_text.insert(tk.END, f'No results found for "{self.current_query}".\n')
            self.results_text.config(state='disabled')
            return
        
        self.results_label.config(text=f"Results: {len(self.current_results)} matches")
        
        for idx, result in enumerate(self.current_results):
            # Title
            self.results_text.insert(tk.END, f"{idx+1}. ", "title")
            self.results_text.insert(tk.END, f"{result['conversation']}\n", "title")
            
            # Meta info
            self.results_text.insert(tk.END, f"   Date: {result['date']}", "meta")
            
            # Role with color
            role_tag = "role_user" if result['role'] == 'user' else "role_assistant"
            self.results_text.insert(tk.END, f"  |  Message #{result['message_number']} (", "meta")
            self.results_text.insert(tk.END, f"{result['role']}", role_tag)
            self.results_text.insert(tk.END, ")\n", "meta")
            
            # Snippet
            self.results_text.insert(tk.END, f"\n   {result['snippet']}\n\n", "snippet")
            
            # Clickable link to open in Obsidian
            link_tag = f"link_{idx}"
            self.results_text.insert(tk.END, "   ")
            self.results_text.insert(tk.END, f"📝 Open in Obsidian", link_tag)
            self.results_text.insert(tk.END, "\n")
            
            # Configure link
            self.results_text.tag_config(link_tag, foreground="#7c3aed", underline=True)
            self.results_text.tag_bind(
                link_tag, "<Button-1>",
                lambda e, path=result['path']: self._open_in_obsidian(path)
            )
            self.results_text.tag_bind(link_tag, "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
            self.results_text.tag_bind(link_tag, "<Leave>", lambda e: self.results_text.config(cursor="arrow"))
            
            # Separator
            self.results_text.insert(tk.END, "\n" + "─" * 70 + "\n\n", "separator")
        
        self.results_text.config(state='disabled')
        self._log(f"Found {len(self.current_results)} results for '{self.current_query}'")
    
    def _open_in_obsidian(self, file_path):
        """Open a specific file in Obsidian"""
        success, message = ObsidianOpener.open_with_search(file_path, self.current_query)
        
        if success:
            self._log(f"✓ {message}")
        else:
            self._log(f"✗ {message}")
            # Fallback: try to open with default app
            try:
                import os
                os.startfile(file_path)
                self._log(f"Opened with default app: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open file:\n{message}\n\nFallback also failed: {e}")
    
    def _search_in_obsidian(self):
        """Open Obsidian's global search with current query"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showinfo("Info", "Please enter a search query first")
            return
        
        if not self.vault_name:
            messagebox.showwarning(
                "Vault Not Detected",
                "Could not detect Obsidian vault.\nPlease select a folder inside an Obsidian vault first."
            )
            return
        
        success, message = ObsidianOpener.search_in_vault(self.vault_name, query)
        
        if success:
            self._log(f"✓ {message}")
        else:
            self._log(f"✗ {message}")
            messagebox.showerror("Error", message)


def main():
    root = tk.Tk()
    app = ChatSearchUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()