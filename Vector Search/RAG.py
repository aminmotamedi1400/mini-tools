import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ── وابستگی‌های اختیاری ──────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    FULL_MODE = True
except ImportError:
    FULL_MODE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# ── ثابت‌ها ───────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".scala",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".env.example", ".sh", ".bash", ".sql"
}

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "migrations"
}

MAX_FILE_SIZE_KB = 200
CHUNK_SIZE = 60
CHUNK_OVERLAP = 10

THEME = {
    "bg_dark":    "#1e1e2e",
    "bg_mid":     "#2a2a3e",
    "bg_light":   "#313145",
    "accent":     "#7c6af7",
    "accent2":    "#56cfb2",
    "text":       "#cdd6f4",
    "text_dim":   "#6c7086",
    "success":    "#a6e3a1",
    "warning":    "#f9e2af",
    "error":      "#f38ba8",
    "border":     "#45475a",
}


# ══════════════════════════════════════════════════════════════════════════════
#  لایه پردازش کد
# ══════════════════════════════════════════════════════════════════════════════

class CodeProcessor:
    """خواندن، تقسیم‌بندی و خلاصه‌سازی فایل‌های کد"""

    @staticmethod
    def read_file(path: str) -> str | None:
        if os.path.getsize(path) > MAX_FILE_SIZE_KB * 1024:
            return None
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                with open(path, encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, PermissionError):
                continue
        return None

    @staticmethod
    def chunk_code(content: str, file_path: str) -> list[dict]:
        lines = content.splitlines()
        ext = Path(file_path).suffix.lower()
        chunks = []

        # استخراج symbolها برای فایل‌های Python
        symbols = []
        if ext == ".py":
            symbols = CodeProcessor._extract_python_symbols(lines)

        if symbols:
            for sym in symbols:
                body = "\n".join(lines[sym["start"]:sym["end"]])
                chunks.append({
                    "text": f"# {sym['type']}: {sym['name']}\n{body}",
                    "metadata": {
                        "file": file_path,
                        "type": sym["type"],
                        "name": sym["name"],
                        "start_line": sym["start"],
                        "end_line": sym["end"],
                    }
                })
        else:
            # تقسیم ساده با overlap
            step = CHUNK_SIZE - CHUNK_OVERLAP
            for i in range(0, len(lines), step):
                body = "\n".join(lines[i: i + CHUNK_SIZE])
                if body.strip():
                    chunks.append({
                        "text": body,
                        "metadata": {
                            "file": file_path,
                            "type": "chunk",
                            "name": f"lines_{i}_{i + CHUNK_SIZE}",
                            "start_line": i,
                            "end_line": min(i + CHUNK_SIZE, len(lines)),
                        }
                    })

        return chunks

    @staticmethod
    def _extract_python_symbols(lines: list[str]) -> list[dict]:
        symbols = []
        stack = []

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if stripped.startswith(("def ", "class ", "async def ")):
                sym_type = "class" if stripped.startswith("class ") else "function"
                name_part = stripped.split("(")[0].split()[-1].rstrip(":")
                # بستن symbolهای هم‌رتبه
                while stack and stack[-1]["indent"] >= indent:
                    s = stack.pop()
                    s["end"] = i
                    symbols.append(s)
                stack.append({
                    "type": sym_type,
                    "name": name_part,
                    "start": i,
                    "end": len(lines),
                    "indent": indent,
                })

        while stack:
            s = stack.pop()
            s["end"] = len(lines)
            symbols.append(s)

        return symbols

    @staticmethod
    def summarize_file(content: str, file_path: str) -> str:
        lines = content.splitlines()
        ext = Path(file_path).suffix.lower()
        summary_lines = []

        if ext == ".py":
            for line in lines[:200]:
                s = line.strip()
                if s.startswith(("import ", "from ", "class ", "def ", "async def ")):
                    summary_lines.append(s[:120])

        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            for line in lines[:200]:
                s = line.strip()
                if any(s.startswith(k) for k in
                       ("import ", "export ", "const ", "function ", "class ", "interface ", "type ")):
                    summary_lines.append(s[:120])

        else:
            summary_lines = [l[:120] for l in lines[:30] if l.strip()]

        return "\n".join(summary_lines[:40])

    @staticmethod
    def count_tokens(text: str) -> int:
        if TIKTOKEN_AVAILABLE:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        return len(text) // 4  # تخمین ساده


# ══════════════════════════════════════════════════════════════════════════════
#  موتور جستجو (دو حالت: embedding یا keyword)
# ══════════════════════════════════════════════════════════════════════════════

class SearchEngine:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.index_dir = Path(project_path) / ".rag_index"
        self.index_dir.mkdir(exist_ok=True)

        self.model = None
        self.collection = None
        self.keyword_index: dict[str, list[dict]] = {}  # fallback

        if FULL_MODE:
            self._init_chroma()

    # ── راه‌اندازی Chroma ──────────────────────────────────────────────────
    def _init_chroma(self):
        client = chromadb.PersistentClient(path=str(self.index_dir / "chroma"))
        col_name = "codebase_" + hashlib.md5(
            self.project_path.encode()).hexdigest()[:8]
        self.collection = client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"}
        )

    def load_model(self, progress_cb=None):
        if FULL_MODE and self.model is None:
            if progress_cb:
                progress_cb("در حال بارگذاری مدل embedding…")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # ── index سازی ────────────────────────────────────────────────────────
    def index_project(self, progress_cb=None, done_cb=None):
        files = self._collect_files()
        total = len(files)
        all_chunks = []
        file_hashes = self._load_hashes()
        new_hashes = {}

        for idx, fp in enumerate(files):
            rel = os.path.relpath(fp, self.project_path)
            if progress_cb:
                progress_cb(f"[{idx+1}/{total}] {rel}", idx / max(total, 1))

            content = CodeProcessor.read_file(fp)
            if not content:
                continue

            file_hash = hashlib.md5(content.encode()).hexdigest()
            new_hashes[fp] = file_hash

            if FULL_MODE and file_hashes.get(fp) == file_hash:
                continue  # بدون تغییر

            chunks = CodeProcessor.chunk_code(content, fp)
            summary = CodeProcessor.summarize_file(content, fp)
            if summary:
                chunks.insert(0, {
                    "text": f"FILE SUMMARY: {rel}\n{summary}",
                    "metadata": {"file": fp, "type": "summary", "name": rel,
                                 "start_line": 0, "end_line": 0}
                })
            all_chunks.extend(chunks)

        self._save_hashes(new_hashes)

        if FULL_MODE and all_chunks:
            self._add_to_chroma(all_chunks, progress_cb)
        else:
            # ساخت index کلمه‌کلیدی
            self._build_keyword_index(all_chunks)

        if done_cb:
            done_cb(total, len(all_chunks))

    def _add_to_chroma(self, chunks: list[dict], progress_cb=None):
        texts = [c["text"] for c in chunks]
        batch = 64
        ids, embeddings_list, metadatas, documents = [], [], [], []

        for i in range(0, len(texts), batch):
            sub = texts[i:i + batch]
            if progress_cb:
                progress_cb(
                    f"embedding بسته {i//batch+1}/{(len(texts)-1)//batch+1}…",
                    0.7 + 0.3 * i / len(texts)
                )
            embs = self.model.encode(sub, show_progress_bar=False).tolist()
            for j, (chunk, emb) in enumerate(zip(chunks[i:i+batch], embs)):
                uid = hashlib.md5(
                    (chunk["metadata"]["file"] + chunk["metadata"]["name"] +
                     str(chunk["metadata"]["start_line"])).encode()
                ).hexdigest()
                ids.append(uid)
                embeddings_list.append(emb)
                metadatas.append(chunk["metadata"])
                documents.append(chunk["text"][:500])

        if ids:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents
            )

    def _build_keyword_index(self, chunks: list[dict]):
        import re
        for chunk in chunks:
            words = set(re.findall(r'\b\w+\b', chunk["text"].lower()))
            for w in words:
                self.keyword_index.setdefault(w, []).append(chunk)

    # ── جستجو ─────────────────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 8) -> list[dict]:
        if FULL_MODE and self.collection:
            return self._semantic_search(query, top_k)
        return self._keyword_search(query, top_k)

    def _semantic_search(self, query: str, top_k: int) -> list[dict]:
        q_emb = self.model.encode([query]).tolist()
        res = self.collection.query(
            query_embeddings=q_emb,
            n_results=min(top_k, self.collection.count() or 1)
        )
        results = []
        for i in range(len(res["ids"][0])):
            meta = res["metadatas"][0][i]
            score = 1 - res["distances"][0][i]
            results.append({
                "file": meta["file"],
                "type": meta["type"],
                "name": meta["name"],
                "start_line": meta.get("start_line", 0),
                "end_line": meta.get("end_line", 0),
                "score": round(score, 3),
                "preview": res["documents"][0][i][:300]
            })
        return results

    def _keyword_search(self, query: str, top_k: int) -> list[dict]:
        import re
        words = set(re.findall(r'\b\w+\b', query.lower()))
        scores: dict[str, float] = {}
        chunk_map: dict[str, dict] = {}
        for w in words:
            for chunk in self.keyword_index.get(w, []):
                key = chunk["metadata"]["file"] + chunk["metadata"]["name"]
                scores[key] = scores.get(key, 0) + 1
                chunk_map[key] = chunk
        sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
        results = []
        for k in sorted_keys[:top_k]:
            c = chunk_map[k]
            results.append({
                "file": c["metadata"]["file"],
                "type": c["metadata"]["type"],
                "name": c["metadata"]["name"],
                "start_line": c["metadata"].get("start_line", 0),
                "end_line": c["metadata"].get("end_line", 0),
                "score": round(scores[k] / max(len(words), 1), 3),
                "preview": c["text"][:300]
            })
        return results

    # ── خواندن محتوای کامل فایل ───────────────────────────────────────────
    def get_file_content(self, file_path: str,
                         start: int = 0, end: int = 0) -> str:
        content = CodeProcessor.read_file(file_path)
        if not content:
            return ""
        if end > 0:
            lines = content.splitlines()
            return "\n".join(lines[start:end])
        return content

    # ── ابزارهای کمکی ─────────────────────────────────────────────────────
    def _collect_files(self) -> list[str]:
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fn in filenames:
                if Path(fn).suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(root, fn))
        return files

    def _hash_path(self) -> Path:
        return self.index_dir / "file_hashes.json"

    def _load_hashes(self) -> dict:
        if self._hash_path().exists():
            return json.loads(self._hash_path().read_text())
        return {}

    def _save_hashes(self, hashes: dict):
        self._hash_path().write_text(json.dumps(hashes, ensure_ascii=False))

    def get_indexed_count(self) -> int:
        if FULL_MODE and self.collection:
            return self.collection.count()
        return sum(len(v) for v in self.keyword_index.values())


# ══════════════════════════════════════════════════════════════════════════════
#  رابط کاربری
# ══════════════════════════════════════════════════════════════════════════════

class RAGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CodeRAG — جستجوی هوشمند کدبیس")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=THEME["bg_dark"])

        self.engine: SearchEngine | None = None
        self.results: list[dict] = []
        self._index_thread: threading.Thread | None = None

        self._build_ui()
        self._check_deps()

    # ── بررسی وابستگی‌ها ──────────────────────────────────────────────────
    def _check_deps(self):
        if not FULL_MODE:
            self._log(
                "⚠  حالت پایه (keyword search) — برای جستجوی معنایی:\n"
                "   pip install sentence-transformers chromadb\n",
                THEME["warning"]
            )
        else:
            self._log("✓  حالت کامل (semantic search) فعال است\n", THEME["success"])

    # ══════════════════════════════════════════════════════════════════════
    #  ساخت UI
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── نوار بالا ──────────────────────────────────────────────────
        top = tk.Frame(self, bg=THEME["bg_dark"], pady=8, padx=12)
        top.pack(fill="x")

        tk.Label(top, text="⬡ CodeRAG",
                 bg=THEME["bg_dark"], fg=THEME["accent"],
                 font=("Segoe UI", 16, "bold")).pack(side="left")

        mode_txt = "🔮 Semantic" if FULL_MODE else "🔍 Keyword"
        tk.Label(top, text=mode_txt,
                 bg=THEME["bg_dark"], fg=THEME["accent2"],
                 font=("Segoe UI", 10)).pack(side="left", padx=14)

        # ── پانل اصلی (left + right) ────────────────────────────────
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=THEME["border"], sashwidth=4,
                               sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        left = self._build_left(paned)
        right = self._build_right(paned)

        paned.add(left, minsize=360, width=420)
        paned.add(right, minsize=420)

    # ── پانل چپ ───────────────────────────────────────────────────────
    def _build_left(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=THEME["bg_dark"])

        # انتخاب پوشه
        sec1 = self._section(f, "📁 پوشه پروژه")
        row = tk.Frame(sec1, bg=THEME["bg_mid"])
        row.pack(fill="x")
        self.path_var = tk.StringVar()
        path_entry = tk.Entry(row, textvariable=self.path_var,
                              bg=THEME["bg_light"], fg=THEME["text"],
                              insertbackground=THEME["text"],
                              relief="flat", font=("Consolas", 10), bd=0)
        path_entry.pack(side="left", fill="x", expand=True,
                        padx=(8, 4), pady=8)

        self._btn(row, "انتخاب", self._browse, small=True).pack(
            side="right", padx=(0, 8), pady=6)

        # Index
        idx_frame = self._section(f, "⚡ ایندکس‌سازی")
        self._btn(idx_frame, "▶  ایندکس / بروزرسانی پروژه",
                  self._start_index).pack(fill="x", pady=(0, 6))

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            idx_frame, variable=self.progress_var,
            maximum=1.0, mode="determinate",
            style="Accent.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x", pady=(0, 4))
        self._style_progressbar()

        self.progress_label = tk.Label(
            idx_frame, text="", bg=THEME["bg_mid"],
            fg=THEME["text_dim"], font=("Segoe UI", 9), anchor="w")
        self.progress_label.pack(fill="x")

        self.stats_label = tk.Label(
            idx_frame, text="هنوز ایندکسی ساخته نشده",
            bg=THEME["bg_mid"], fg=THEME["text_dim"],
            font=("Segoe UI", 9), anchor="w")
        self.stats_label.pack(fill="x", pady=(4, 0))

        # پرامپت
        p_sec = self._section(f, "✏  پرامپت شما")
        self.prompt_text = scrolledtext.ScrolledText(
            p_sec, height=7, wrap="word",
            bg=THEME["bg_light"], fg=THEME["text"],
            insertbackground=THEME["text"],
            font=("Segoe UI", 11), relief="flat", bd=0,
            selectbackground=THEME["accent"]
        )
        self.prompt_text.pack(fill="both", expand=True, pady=(0, 6))

        # تنظیمات
        cfg = self._section(f, "⚙  تنظیمات")
        cr = tk.Frame(cfg, bg=THEME["bg_mid"])
        cr.pack(fill="x")
        tk.Label(cr, text="تعداد نتیجه:", bg=THEME["bg_mid"],
                 fg=THEME["text_dim"], font=("Segoe UI", 9)).pack(
            side="left", padx=(4, 4))
        self.top_k = tk.IntVar(value=6)
        spn = tk.Spinbox(cr, from_=1, to=20, textvariable=self.top_k,
                         width=4, bg=THEME["bg_light"], fg=THEME["text"],
                         buttonbackground=THEME["bg_light"],
                         relief="flat", font=("Consolas", 10))
        spn.pack(side="left")

        self.include_full = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            cr, text="محتوای کامل فایل", variable=self.include_full,
            bg=THEME["bg_mid"], fg=THEME["text_dim"],
            selectcolor=THEME["bg_light"],
            activebackground=THEME["bg_mid"],
            font=("Segoe UI", 9)
        )
        chk.pack(side="left", padx=12)

        # دکمه جستجو
        self._btn(f, "🔍  جستجوی بخش‌های مرتبط",
                  self._search, accent=True).pack(
            fill="x", padx=10, pady=8)

        return f

    # ── پانل راست ─────────────────────────────────────────────────────
    def _build_right(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=THEME["bg_dark"])

        # تب‌ها
        tabs = ttk.Notebook(f, style="Dark.TNotebook")
        tabs.pack(fill="both", expand=True)
        self._style_notebook()

        # تب نتایج
        res_frame = tk.Frame(tabs, bg=THEME["bg_dark"])
        tabs.add(res_frame, text="  نتایج  ")
        self._build_results_tab(res_frame)

        # تب خروجی آماده
        out_frame = tk.Frame(tabs, bg=THEME["bg_dark"])
        tabs.add(out_frame, text="  📋 خروجی آماده  ")
        self._build_output_tab(out_frame)

        # تب لاگ
        log_frame = tk.Frame(tabs, bg=THEME["bg_dark"])
        tabs.add(log_frame, text="  لاگ  ")
        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg=THEME["bg_dark"], fg=THEME["text_dim"],
            font=("Consolas", 9), state="disabled", relief="flat",
            selectbackground=THEME["accent"]
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.log_text.tag_config("warn",    foreground=THEME["warning"])
        self.log_text.tag_config("success", foreground=THEME["success"])
        self.log_text.tag_config("error",   foreground=THEME["error"])

        return f

    def _build_results_tab(self, parent):
        # لیست نتایج
        list_frame = tk.Frame(parent, bg=THEME["bg_dark"])
        list_frame.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("فایل", "نوع", "نام", "امتیاز", "خطوط")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings",
                                 style="Dark.Treeview", height=8)
        widths = {"فایل": 220, "نوع": 70, "نام": 160, "امتیاز": 60, "خطوط": 80}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths[c], anchor="w")
        self._style_treeview()

        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # پیش‌نمایش
        prev_lbl = tk.Label(parent, text="پیش‌نمایش محتوا:",
                            bg=THEME["bg_dark"], fg=THEME["text_dim"],
                            font=("Segoe UI", 9), anchor="w")
        prev_lbl.pack(fill="x", padx=8)
        self.preview_text = scrolledtext.ScrolledText(
            parent, height=12, bg=THEME["bg_mid"], fg=THEME["text"],
            font=("Consolas", 10), relief="flat", state="disabled",
            selectbackground=THEME["accent"]
        )
        self.preview_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def _build_output_tab(self, parent):
        # نوار ابزار
        toolbar = tk.Frame(parent, bg=THEME["bg_dark"])
        toolbar.pack(fill="x", padx=6, pady=6)

        self._btn(toolbar, "📋 کپی همه",
                  self._copy_output, small=True).pack(side="left", padx=4)
        self._btn(toolbar, "💾 ذخیره فایل",
                  self._save_output, small=True).pack(side="left", padx=4)

        self.token_label = tk.Label(
            toolbar, text="", bg=THEME["bg_dark"],
            fg=THEME["text_dim"], font=("Segoe UI", 9))
        self.token_label.pack(side="right", padx=8)

        self.output_text = scrolledtext.ScrolledText(
            parent, bg=THEME["bg_mid"], fg=THEME["text"],
            font=("Consolas", 10), relief="flat",
            selectbackground=THEME["accent"]
        )
        self.output_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    # ══════════════════════════════════════════════════════════════════════
    #  رویدادها
    # ══════════════════════════════════════════════════════════════════════

    def _browse(self):
        d = filedialog.askdirectory(title="پوشه پروژه را انتخاب کنید")
        if d:
            self.path_var.set(d)
            self.engine = None
            self.stats_label.config(text="ایندکس نشده — لطفاً ابتدا ایندکس کنید")

    def _start_index(self):
        path = self.path_var.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("خطا", "لطفاً یک پوشه معتبر انتخاب کنید")
            return
        if self._index_thread and self._index_thread.is_alive():
            self._log("ایندکس‌سازی در حال اجرا است…\n", THEME["warning"])
            return

        self.engine = SearchEngine(path)
        self._index_thread = threading.Thread(
            target=self._run_index, daemon=True)
        self._index_thread.start()

    def _run_index(self):
        self._log("⏳ شروع بارگذاری مدل…\n")
        self.engine.load_model(self._set_progress_label)

        self._log("⏳ شروع ایندکس‌سازی پروژه…\n")

        def progress(msg, val=None):
            self._set_progress_label(msg)
            if val is not None:
                self.progress_var.set(val)

        def done(files_count, chunks_count):
            self.progress_var.set(1.0)
            self._set_progress_label("✓ ایندکس‌سازی تمام شد")
            self.stats_label.config(
                text=f"✓  {files_count} فایل  |  {chunks_count} قطعه  "
                     f"|  {self.engine.get_indexed_count()} در DB"
            )
            self._log(
                f"✓  ایندکس ساخته شد:  {files_count} فایل,"
                f" {chunks_count} قطعه\n",
                THEME["success"]
            )

        self.engine.index_project(
            progress_cb=progress,
            done_cb=done
        )

    def _search(self):
        if not self.engine:
            messagebox.showwarning("توجه", "ابتدا پروژه را ایندکس کنید")
            return
        query = self.prompt_text.get("1.0", "end").strip()
        if not query:
            messagebox.showwarning("توجه", "پرامپت را وارد کنید")
            return

        self._log(f"🔍 جستجو برای: {query[:80]}…\n")
        self.results = self.engine.search(query, self.top_k.get())

        # پر کردن جدول
        self.tree.delete(*self.tree.get_children())
        for r in self.results:
            rel = os.path.relpath(r["file"], self.engine.project_path)
            lines = f"{r['start_line']+1}–{r['end_line']}"
            self.tree.insert("", "end", values=(
                rel, r["type"], r["name"], r["score"], lines
            ))

        self._build_output(query)
        self._log(f"✓  {len(self.results)} نتیجه یافت شد\n", THEME["success"])

    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        r = self.results[idx]

        content = self.engine.get_file_content(
            r["file"], r["start_line"], r["end_line"])

        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        rel = os.path.relpath(r["file"], self.engine.project_path)
        header = f"# {rel}  |  {r['type']}: {r['name']}  |  score: {r['score']}\n"
        header += "─" * 60 + "\n"
        self.preview_text.insert("end", header + content)
        self.preview_text.config(state="disabled")

    def _build_output(self, prompt: str):
        lines = []
        lines.append("=" * 70)
        lines.append("PROMPT:")
        lines.append(prompt)
        lines.append("=" * 70)
        lines.append("RELEVANT CODE CONTEXT:")
        lines.append("")

        for i, r in enumerate(self.results, 1):
            rel = os.path.relpath(r["file"], self.engine.project_path)
            lines.append(f"## [{i}] {rel}  |  {r['type']}: {r['name']}")
            lines.append(f"##     score: {r['score']} | خطوط {r['start_line']+1}–{r['end_line']}")
            lines.append("")

            if self.include_full.get():
                content = self.engine.get_file_content(r["file"])
            else:
                content = self.engine.get_file_content(
                    r["file"], r["start_line"], r["end_line"])

            ext = Path(r["file"]).suffix.lstrip(".")
            lines.append(f"```{ext}")
            lines.append(content or r["preview"])
            lines.append("```")
            lines.append("")

        lines.append("=" * 70)
        lines.append("END OF CONTEXT")
        lines.append("=" * 70)

        output = "\n".join(lines)

        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", output)

        tokens = CodeProcessor.count_tokens(output)
        self.token_label.config(
            text=f"~{tokens:,} توکن",
            fg=THEME["warning"] if tokens > 8000 else THEME["success"]
        )

    def _copy_output(self):
        content = self.output_text.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(content)
        self._log("✓  کپی شد\n", THEME["success"])

    def _save_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"context_{datetime.now().strftime('%H%M%S')}.txt"
        )
        if path:
            Path(path).write_text(
                self.output_text.get("1.0", "end"), encoding="utf-8")
            self._log(f"✓  ذخیره شد: {path}\n", THEME["success"])

    # ══════════════════════════════════════════════════════════════════════
    #  ابزارهای کمکی UI
    # ══════════════════════════════════════════════════════════════════════

    def _section(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=THEME["bg_dark"])
        outer.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(outer, text=title,
                 bg=THEME["bg_dark"], fg=THEME["accent2"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        inner = tk.Frame(outer, bg=THEME["bg_mid"],
                         padx=8, pady=8,
                         highlightthickness=1,
                         highlightbackground=THEME["border"])
        inner.pack(fill="x")
        return inner

    def _btn(self, parent, text: str, cmd,
             accent: bool = False, small: bool = False) -> tk.Button:
        bg = THEME["accent"] if accent else THEME["bg_light"]
        fg = "#ffffff" if accent else THEME["text"]
        font = ("Segoe UI", 9) if small else ("Segoe UI", 10, "bold")
        return tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg=fg, activebackground=THEME["accent"],
            activeforeground="#ffffff",
            font=font, relief="flat", cursor="hand2",
            padx=12, pady=4
        )

    def _set_progress_label(self, msg: str):
        self.progress_label.config(text=msg[:80])

    def _log(self, msg: str, color: str = None):
        self.log_text.config(state="normal")
        tag = None
        if color == THEME["warning"]:  tag = "warn"
        elif color == THEME["success"]: tag = "success"
        elif color == THEME["error"]:   tag = "error"

        ts = datetime.now().strftime("%H:%M:%S")
        full = f"[{ts}] {msg}"
        if tag:
            self.log_text.insert("end", full, tag)
        else:
            self.log_text.insert("end", full)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ── استایل‌ها ─────────────────────────────────────────────────────────
    def _style_progressbar(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Accent.Horizontal.TProgressbar",
                    troughcolor=THEME["bg_light"],
                    background=THEME["accent"],
                    bordercolor=THEME["bg_light"],
                    lightcolor=THEME["accent"],
                    darkcolor=THEME["accent"])

    def _style_treeview(self):
        s = ttk.Style()
        s.configure("Dark.Treeview",
                    background=THEME["bg_mid"],
                    foreground=THEME["text"],
                    fieldbackground=THEME["bg_mid"],
                    rowheight=24,
                    font=("Consolas", 9))
        s.configure("Dark.Treeview.Heading",
                    background=THEME["bg_light"],
                    foreground=THEME["accent2"],
                    font=("Segoe UI", 9, "bold"))
        s.map("Dark.Treeview",
              background=[("selected", THEME["accent"])],
              foreground=[("selected", "#ffffff")])

    def _style_notebook(self):
        s = ttk.Style()
        s.configure("Dark.TNotebook",
                    background=THEME["bg_dark"],
                    borderwidth=0)
        s.configure("Dark.TNotebook.Tab",
                    background=THEME["bg_mid"],
                    foreground=THEME["text_dim"],
                    padding=(12, 5),
                    font=("Segoe UI", 9))
        s.map("Dark.TNotebook.Tab",
              background=[("selected", THEME["bg_light"])],
              foreground=[("selected", THEME["text"])])


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = RAGApp()
    app.mainloop()