import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3
import os
import subprocess
import time
from datetime import datetime, timedelta
import json

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH = "thesis_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS blocks (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        target_hours REAL,
        progress INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        duration_minutes REAL,
        description TEXT,
        FOREIGN KEY(block_id) REFERENCES blocks(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER,
        date TEXT,
        task_name TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        FOREIGN KEY(block_id) REFERENCES blocks(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        block_id INTEGER,
        log_text TEXT,
        mood TEXT,
        FOREIGN KEY(block_id) REFERENCES blocks(id)
    )''')
    c.execute("SELECT COUNT(*) FROM blocks")
    if c.fetchone()[0] == 0:
        blocks_data = [
            (1, "Block 1: FastAPI & PostgreSQL", "API Foundation & Relational Data Layer", 120),
            (2, "Block 2: Neo4j Graph Memory", "Graph Memory Integration & Decision Modeling", 120),
            (3, "Block 3: LangGraph Multi-Agent", "Multi-Agent Logic & Token Budgeting", 150),
            (4, "Block 4: Evaluation & Benchmarking", "Dataset Generation & Baseline Comparison", 130),
            (5, "Block 5: Docker Deployment", "Containerization & System Deployment", 80),
            (6, "Block 6: Thesis Writing & Defense", "Documentation, Writing & Final Defense", 100),
        ]
        c.executemany("INSERT INTO blocks (id, name, description, target_hours) VALUES (?, ?, ?, ?)", blocks_data)
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

class ThesisTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Thesis Project Tracker — Multi-Agent RAG System")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")

        self.timer_running = False
        self.timer_start = None
        self.elapsed_seconds = 0

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e1e2e")
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4",
                        padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")])
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TButton", background="#89b4fa", foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), padding=6)
        style.map("TButton", background=[("active", "#74c7ec")])
        style.configure("Accent.TButton", background="#a6e3a1", foreground="#1e1e2e")
        style.configure("Danger.TButton", background="#f38ba8", foreground="#1e1e2e")
        style.configure("TProgressbar", background="#89b4fa", troughcolor="#313244")
        style.configure("TCombobox", fieldbackground="#313244", foreground="#cdd6f4")
        style.configure("Treeview", background="#313244", foreground="#cdd6f4",
                        fieldbackground="#313244", font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#45475a", foreground="#cdd6f4",
                        font=("Segoe UI", 9, "bold"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.build_dashboard_tab()
        self.build_timer_tab()
        self.build_tasks_tab()
        self.build_log_tab()
        self.build_report_tab()
        self.build_history_tab()

        self.update_timer_display()

    # ─────────────────────────────────────────────────────────────────────
    # DASHBOARD TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_dashboard_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Dashboard  ")

        title = tk.Label(frame, text="PROJECT OVERVIEW", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        self.dashboard_frame = ttk.Frame(frame)
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.refresh_dashboard()

    def refresh_dashboard(self):
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM blocks ORDER BY id")
        blocks = c.fetchall()

        total_logged = 0
        total_target = 0

        for i, block in enumerate(blocks):
            bid, name, desc, target_hours, progress = block
            c.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM sessions WHERE block_id=?", (bid,))
            logged_minutes = c.fetchone()[0]
            logged_hours = logged_minutes / 60
            total_logged += logged_hours
            total_target += target_hours

            row_frame = tk.Frame(self.dashboard_frame, bg="#313244", highlightbackground="#45475a",
                                 highlightthickness=1)
            row_frame.pack(fill=tk.X, pady=4, ipady=6, ipadx=10)

            tk.Label(row_frame, text=name, font=("Segoe UI", 10, "bold"),
                     bg="#313244", fg="#cdd6f4", anchor="w").pack(side=tk.TOP, fill=tk.X, padx=10, pady=(6,0))

            info_text = f"Logged: {logged_hours:.1f}h / {target_hours:.0f}h target  |  Progress: {progress}%"
            tk.Label(row_frame, text=info_text, font=("Segoe UI", 9),
                     bg="#313244", fg="#a6adc8").pack(side=tk.TOP, fill=tk.X, padx=10)

            bar_frame = tk.Frame(row_frame, bg="#313244")
            bar_frame.pack(fill=tk.X, padx=10, pady=(4, 6))
            pb = ttk.Progressbar(bar_frame, value=progress, maximum=100, length=400)
            pb.pack(side=tk.LEFT, fill=tk.X, expand=True)

            prog_entry = tk.Entry(bar_frame, width=4, bg="#45475a", fg="#cdd6f4",
                                  insertbackground="#cdd6f4", font=("Segoe UI", 9))
            prog_entry.insert(0, str(progress))
            prog_entry.pack(side=tk.LEFT, padx=4)
            tk.Label(bar_frame, text="%", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)

            update_btn = tk.Button(bar_frame, text="Update", font=("Segoe UI", 8),
                                   bg="#89b4fa", fg="#1e1e2e",
                                   command=lambda b=bid, e=prog_entry: self.update_progress(b, e))
            update_btn.pack(side=tk.LEFT, padx=6)

        conn.close()

        summary_frame = tk.Frame(self.dashboard_frame, bg="#1e1e2e")
        summary_frame.pack(fill=tk.X, pady=10)
        tk.Label(summary_frame,
                 text=f"TOTAL: {total_logged:.1f} hours logged / {total_target:.0f} hours target",
                 font=("Segoe UI", 12, "bold"), bg="#1e1e2e", fg="#a6e3a1").pack()

    def update_progress(self, block_id, entry):
        try:
            val = int(entry.get())
            if 0 <= val <= 100:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE blocks SET progress=? WHERE id=?", (val, block_id))
                conn.commit()
                conn.close()
                self.refresh_dashboard()
            else:
                messagebox.showwarning("Invalid", "Progress must be between 0 and 100.")
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a valid number.")

    # ─────────────────────────────────────────────────────────────────────
    # TIMER TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_timer_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Timer  ")

        title = tk.Label(frame, text="WORK SESSION TIMER", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        sel_frame = ttk.Frame(frame)
        sel_frame.pack(pady=10)
        ttk.Label(sel_frame, text="Working on:").pack(side=tk.LEFT, padx=5)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name FROM blocks ORDER BY id")
        self.block_options = c.fetchall()
        conn.close()

        self.timer_block_var = tk.StringVar()
        block_names = [b[1] for b in self.block_options]
        self.timer_block_combo = ttk.Combobox(sel_frame, textvariable=self.timer_block_var,
                                              values=block_names, state="readonly", width=40)
        self.timer_block_combo.pack(side=tk.LEFT, padx=5)
        if block_names:
            self.timer_block_combo.current(0)

        self.timer_display = tk.Label(frame, text="00:00:00", font=("Consolas", 48, "bold"),
                                      bg="#1e1e2e", fg="#a6e3a1")
        self.timer_display.pack(pady=20)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="▶  START", font=("Segoe UI", 12, "bold"),
                                   bg="#a6e3a1", fg="#1e1e2e", width=12, command=self.start_timer)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="■  STOP", font=("Segoe UI", 12, "bold"),
                                  bg="#f38ba8", fg="#1e1e2e", width=12, command=self.stop_timer,
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        ttk.Label(frame, text="Session description (REQUIRED when stopping):").pack(pady=(20, 5))
        self.timer_desc = scrolledtext.ScrolledText(frame, height=5, width=70,
                                                    bg="#313244", fg="#cdd6f4",
                                                    insertbackground="#cdd6f4",
                                                    font=("Segoe UI", 10))
        self.timer_desc.pack(padx=20)

    def start_timer(self):
        if not self.timer_block_var.get():
            messagebox.showwarning("Select Block", "You must select which block you are working on.")
            return
        self.timer_running = True
        self.timer_start = datetime.now()
        self.elapsed_seconds = 0
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.timer_block_combo.config(state=tk.DISABLED)

    def stop_timer(self):
        desc = self.timer_desc.get("1.0", tk.END).strip()
        if len(desc) < 10:
            messagebox.showwarning("Description Required",
                                   "You MUST write at least 10 characters describing what you accomplished.\n\n"
                                   "This is mandatory for accurate progress tracking.")
            return

        self.timer_running = False
        end_time = datetime.now()
        duration_minutes = self.elapsed_seconds / 60

        block_name = self.timer_block_var.get()
        block_id = None
        for b in self.block_options:
            if b[1] == block_name:
                block_id = b[0]
                break

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO sessions (block_id, start_time, end_time, duration_minutes, description)
                     VALUES (?, ?, ?, ?, ?)''',
                  (block_id, self.timer_start.strftime("%Y-%m-%d %H:%M:%S"),
                   end_time.strftime("%Y-%m-%d %H:%M:%S"), duration_minutes, desc))
        conn.commit()
        conn.close()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.timer_block_combo.config(state="readonly")
        self.timer_desc.delete("1.0", tk.END)
        self.elapsed_seconds = 0
        self.timer_display.config(text="00:00:00")

        messagebox.showinfo("Session Saved",
                            f"Session saved!\nBlock: {block_name}\n"
                            f"Duration: {duration_minutes:.1f} minutes\n"
                            f"Description: {desc[:50]}...")
        self.refresh_dashboard()

    def update_timer_display(self):
        if self.timer_running:
            self.elapsed_seconds = (datetime.now() - self.timer_start).total_seconds()
        hours = int(self.elapsed_seconds // 3600)
        minutes = int((self.elapsed_seconds % 3600) // 60)
        seconds = int(self.elapsed_seconds % 60)
        self.timer_display.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_timer_display)

    # ─────────────────────────────────────────────────────────────────────
    # TASKS TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_tasks_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Tasks  ")

        title = tk.Label(frame, text="TASK MANAGEMENT", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        add_frame = tk.Frame(frame, bg="#313244", highlightbackground="#45475a", highlightthickness=1)
        add_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)

        tk.Label(add_frame, text="Add New Task", font=("Segoe UI", 11, "bold"),
                 bg="#313244", fg="#cdd6f4").pack(pady=(10, 5))

        row1 = tk.Frame(add_frame, bg="#313244")
        row1.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row1, text="Block:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.task_block_var = tk.StringVar()
        block_names = [b[1] for b in self.block_options]
        ttk.Combobox(row1, textvariable=self.task_block_var, values=block_names,
                     state="readonly", width=40).pack(side=tk.LEFT, padx=10)

        row2 = tk.Frame(add_frame, bg="#313244")
        row2.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row2, text="Task:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.task_name_entry = tk.Entry(row2, width=50, bg="#45475a", fg="#cdd6f4",
                                        insertbackground="#cdd6f4", font=("Segoe UI", 10))
        self.task_name_entry.pack(side=tk.LEFT, padx=10)

        row3 = tk.Frame(add_frame, bg="#313244")
        row3.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row3, text="Notes:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.task_notes_entry = tk.Entry(row3, width=50, bg="#45475a", fg="#cdd6f4",
                                         insertbackground="#cdd6f4", font=("Segoe UI", 10))
        self.task_notes_entry.pack(side=tk.LEFT, padx=10)

        tk.Button(add_frame, text="+ Add Task", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), command=self.add_task).pack(pady=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.task_tree = ttk.Treeview(tree_frame,
                                      columns=("date", "block", "task", "status", "notes"),
                                      show="headings", height=12)
        self.task_tree.heading("date", text="Date")
        self.task_tree.heading("block", text="Block")
        self.task_tree.heading("task", text="Task")
        self.task_tree.heading("status", text="Status")
        self.task_tree.heading("notes", text="Notes")
        self.task_tree.column("date", width=90)
        self.task_tree.column("block", width=200)
        self.task_tree.column("task", width=250)
        self.task_tree.column("status", width=80)
        self.task_tree.column("notes", width=200)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="✓ Mark Done", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), command=self.mark_task_done).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✗ Delete", bg="#f38ba8", fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), command=self.delete_task).pack(side=tk.LEFT, padx=5)

        self.refresh_tasks()

    def add_task(self):
        block_name = self.task_block_var.get()
        task_name = self.task_name_entry.get().strip()
        notes = self.task_notes_entry.get().strip()

        if not block_name or not task_name:
            messagebox.showwarning("Required", "Block and Task name are required.")
            return

        block_id = None
        for b in self.block_options:
            if b[1] == block_name:
                block_id = b[0]
                break

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (block_id, date, task_name, status, notes) VALUES (?, ?, ?, ?, ?)",
                  (block_id, datetime.now().strftime("%Y-%m-%d"), task_name, "pending", notes))
        conn.commit()
        conn.close()

        self.task_name_entry.delete(0, tk.END)
        self.task_notes_entry.delete(0, tk.END)
        self.refresh_tasks()

    def refresh_tasks(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT t.id, t.date, b.name, t.task_name, t.status, t.notes
                     FROM tasks t JOIN blocks b ON t.block_id = b.id
                     ORDER BY t.date DESC, t.id DESC''')
        for row in c.fetchall():
            self.task_tree.insert("", tk.END, iid=row[0],
                                 values=(row[1], row[2], row[3], row[4], row[5]))
        conn.close()

    def mark_task_done(self):
        selected = self.task_tree.selection()
        if not selected:
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for item in selected:
            c.execute("UPDATE tasks SET status='done' WHERE id=?", (int(item),))
        conn.commit()
        conn.close()
        self.refresh_tasks()

    def delete_task(self):
        selected = self.task_tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Confirm", "Delete selected task(s)?"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            for item in selected:
                c.execute("DELETE FROM tasks WHERE id=?", (int(item),))
            conn.commit()
            conn.close()
            self.refresh_tasks()

    # ─────────────────────────────────────────────────────────────────────
    # DAILY LOG TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_log_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Daily Log  ")

        title = tk.Label(frame, text="DAILY PROGRESS LOG", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        form_frame = tk.Frame(frame, bg="#313244", highlightbackground="#45475a", highlightthickness=1)
        form_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)

        row1 = tk.Frame(form_frame, bg="#313244")
        row1.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(row1, text="Block:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.log_block_var = tk.StringVar()
        block_names = [b[1] for b in self.block_options]
        ttk.Combobox(row1, textvariable=self.log_block_var, values=block_names,
                     state="readonly", width=40).pack(side=tk.LEFT, padx=10)

        row2 = tk.Frame(form_frame, bg="#313244")
        row2.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(row2, text="Mood:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.log_mood_var = tk.StringVar()
        moods = ["Focused & Productive", "Normal", "Tired but Working", "Struggling", "Blocked"]
        ttk.Combobox(row2, textvariable=self.log_mood_var, values=moods,
                     state="readonly", width=30).pack(side=tk.LEFT, padx=10)

        tk.Label(form_frame, text="What did you accomplish today? (Be specific)",
                 bg="#313244", fg="#a6adc8").pack(padx=20, anchor="w", pady=(10, 2))
        self.log_text = scrolledtext.ScrolledText(form_frame, height=6, width=70,
                                                  bg="#45475a", fg="#cdd6f4",
                                                  insertbackground="#cdd6f4",
                                                  font=("Segoe UI", 10))
        self.log_text.pack(padx=20, pady=5)

        tk.Button(form_frame, text="Save Daily Log", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), command=self.save_daily_log).pack(pady=10)

        self.log_history = scrolledtext.ScrolledText(frame, height=10, width=80,
                                                    bg="#313244", fg="#cdd6f4",
                                                    font=("Consolas", 9), state=tk.DISABLED)
        self.log_history.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.refresh_log_history()

    def save_daily_log(self):
        block_name = self.log_block_var.get()
        mood = self.log_mood_var.get()
        log_text = self.log_text.get("1.0", tk.END).strip()

        if not block_name or not log_text or len(log_text) < 20:
            messagebox.showwarning("Required",
                                   "You must select a block and write at least 20 characters.\n"
                                   "Be honest with yourself — what did you actually accomplish?")
            return

        block_id = None
        for b in self.block_options:
            if b[1] == block_name:
                block_id = b[0]
                break

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO daily_logs (date, block_id, log_text, mood) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d"), block_id, log_text, mood))
        conn.commit()
        conn.close()

        self.log_text.delete("1.0", tk.END)
        messagebox.showinfo("Saved", "Daily log saved successfully!")
        self.refresh_log_history()

    def refresh_log_history(self):
        self.log_history.config(state=tk.NORMAL)
        self.log_history.delete("1.0", tk.END)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT d.date, b.name, d.mood, d.log_text
                     FROM daily_logs d JOIN blocks b ON d.block_id = b.id
                     ORDER BY d.date DESC LIMIT 20''')
        for row in c.fetchall():
            self.log_history.insert(tk.END, f"[{row[0]}] {row[1]} | Mood: {row[2]}\n")
            self.log_history.insert(tk.END, f"  {row[3]}\n")
            self.log_history.insert(tk.END, "-" * 80 + "\n")
        conn.close()
        self.log_history.config(state=tk.DISABLED)

    # ─────────────────────────────────────────────────────────────────────
    # REPORT TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_report_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Report  ")

        title = tk.Label(frame, text="GENERATE PROGRESS REPORT", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        info = tk.Label(frame,
                        text="Generate a professional LaTeX report for your supervisor.\n"
                             "The report includes time logs, task completion, and progress per block.",
                        font=("Segoe UI", 10), bg="#1e1e2e", fg="#a6adc8", justify=tk.CENTER)
        info.pack(pady=5)

        opt_frame = tk.Frame(frame, bg="#313244", highlightbackground="#45475a", highlightthickness=1)
        opt_frame.pack(fill=tk.X, padx=20, pady=10, ipady=10)

        row1 = tk.Frame(opt_frame, bg="#313244")
        row1.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(row1, text="Report Period:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.report_period_var = tk.StringVar(value="Last 3 Months")
        ttk.Combobox(row1, textvariable=self.report_period_var,
                     values=["Last Month", "Last 3 Months", "Last 6 Months", "All Time"],
                     state="readonly", width=20).pack(side=tk.LEFT, padx=10)

        row2 = tk.Frame(opt_frame, bg="#313244")
        row2.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(row2, text="Student Name:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.student_name_entry = tk.Entry(row2, width=30, bg="#45475a", fg="#cdd6f4",
                                           insertbackground="#cdd6f4")
        self.student_name_entry.pack(side=tk.LEFT, padx=10)

        row3 = tk.Frame(opt_frame, bg="#313244")
        row3.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(row3, text="Supervisor Name:", bg="#313244", fg="#a6adc8").pack(side=tk.LEFT)
        self.supervisor_name_entry = tk.Entry(row3, width=30, bg="#45475a", fg="#cdd6f4",
                                              insertbackground="#cdd6f4")
        self.supervisor_name_entry.pack(side=tk.LEFT, padx=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Generate LaTeX Only", bg="#89b4fa", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), command=self.generate_latex).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Generate & Compile PDF", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), command=self.generate_and_compile).pack(side=tk.LEFT, padx=10)

        self.report_status = tk.Label(frame, text="", font=("Segoe UI", 10),
                                      bg="#1e1e2e", fg="#a6e3a1")
        self.report_status.pack(pady=5)

        self.latex_preview = scrolledtext.ScrolledText(frame, height=15, width=90,
                                                      bg="#313244", fg="#cdd6f4",
                                                      font=("Consolas", 9))
        self.latex_preview.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def get_report_data(self):
        period = self.report_period_var.get()
        if period == "Last Month":
            days = 30
        elif period == "Last 3 Months":
            days = 90
        elif period == "Last 6 Months":
            days = 180
        else:
            days = 9999

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT * FROM blocks ORDER BY id")
        blocks = c.fetchall()

        report_data = []
        for block in blocks:
            bid, name, desc, target_hours, progress = block

            c.execute('''SELECT COALESCE(SUM(duration_minutes), 0) FROM sessions
                         WHERE block_id=? AND start_time >= ?''', (bid, cutoff))
            period_minutes = c.fetchone()[0]

            c.execute('''SELECT COALESCE(SUM(duration_minutes), 0) FROM sessions WHERE block_id=?''', (bid,))
            total_minutes = c.fetchone()[0]

            c.execute('''SELECT COUNT(*) FROM tasks WHERE block_id=? AND status='done' AND date >= ?''',
                      (bid, cutoff))
            done_tasks = c.fetchone()[0]

            c.execute('''SELECT COUNT(*) FROM tasks WHERE block_id=?''', (bid,))
            total_tasks = c.fetchone()[0]

            c.execute('''SELECT description FROM sessions WHERE block_id=? AND start_time >= ?
                         ORDER BY start_time DESC LIMIT 5''', (bid, cutoff))
            recent_sessions = [r[0] for r in c.fetchall()]

            report_data.append({
                "name": name,
                "description": desc,
                "progress": progress,
                "period_hours": period_minutes / 60,
                "total_hours": total_minutes / 60,
                "target_hours": target_hours,
                "done_tasks": done_tasks,
                "total_tasks": total_tasks,
                "recent_sessions": recent_sessions
            })

        c.execute('''SELECT d.date, b.name, d.log_text FROM daily_logs d
                     JOIN blocks b ON d.block_id = b.id
                     WHERE d.date >= ? ORDER BY d.date DESC LIMIT 10''', (cutoff,))
        recent_logs = c.fetchall()

        conn.close()
        return report_data, recent_logs

    def generate_latex_content(self):
        student = self.student_name_entry.get().strip() or "[Student Name]"
        supervisor = self.supervisor_name_entry.get().strip() or "[Supervisor Name]"
        period = self.report_period_var.get()
        report_data, recent_logs = self.get_report_data()

        total_period_hours = sum(b["period_hours"] for b in report_data)
        total_all_hours = sum(b["total_hours"] for b in report_data)
        avg_progress = sum(b["progress"] for b in report_data) / len(report_data)

        latex = r"""\documentclass[11pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{amssymb}
\usepackage{hyperref}
\usepackage{tcolorbox}
\usepackage{titlesec}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{graphicx}

\definecolor{primary}{RGB}{41, 128, 185}
\definecolor{secondary}{RGB}{44, 62, 80}
\definecolor{success}{RGB}{39, 174, 96}
\definecolor{highlight}{RGB}{236, 240, 241}

\titleformat{\section}{\Large\bfseries\color{primary}}{\thesection}{1em}{}[\titlerule]
\titleformat{\subsection}{\large\bfseries\color{secondary}}{\thesubsection}{1em}{}

"""
        latex += r"\title{\textbf{\color{primary}Thesis Progress Report --- " + period + r"}}" + "\n"
        latex += r"\author{\textbf{Student:} " + student + r" \and \textbf{Supervisor:} " + supervisor + r"}" + "\n"
        latex += r"\date{Report Generated: " + datetime.now().strftime("%B %d, %Y") + r"}" + "\n"
        latex += r"""
\begin{document}
\maketitle

\begin{tcolorbox}[colback=highlight, colframe=primary, title=\textbf{Project Summary}]
\textbf{Thesis:} A Multi-Agent Framework for Budget-Based Decision Coordination in Information Seeking Conversational Systems.\\[6pt]
"""
        latex += r"\textbf{Total Hours This Period:} " + f"{total_period_hours:.1f} hours" + r"\\" + "\n"
        latex += r"\textbf{Total Hours (All Time):} " + f"{total_all_hours:.1f} hours" + r"\\" + "\n"
        latex += r"\textbf{Average Progress:} " + f"{avg_progress:.0f}\\%" + "\n"
        latex += r"""\end{tcolorbox}

\section{Progress Per Block}

\begin{tabularx}{\textwidth}{@{} l X r r r @{}}
\toprule
\textbf{\#} & \textbf{Block} & \textbf{Hours (Period)} & \textbf{Hours (Total)} & \textbf{Progress} \\
\midrule
"""
        for i, b in enumerate(report_data, 1):
            name_short = b["name"].replace("&", r"\&")
            latex += f"{i} & {name_short} & {b['period_hours']:.1f}h & {b['total_hours']:.1f}h / {b['target_hours']:.0f}h & {b['progress']}\\% \\\\\n"

        latex += r"""\bottomrule
\end{tabularx}

\section{Task Completion Summary}

\begin{tabularx}{\textwidth}{@{} X r r @{}}
\toprule
\textbf{Block} & \textbf{Tasks Done (Period)} & \textbf{Tasks Total} \\
\midrule
"""
        for b in report_data:
            name_short = b["name"].replace("&", r"\&")
            latex += f"{name_short} & {b['done_tasks']} & {b['total_tasks']} \\\\\n"
        latex += r"""\bottomrule
\end{tabularx}

\section{Recent Work Sessions (Last 5 per Block)}

"""
        for b in report_data:
            if b["recent_sessions"]:
                name_short = b["name"].replace("&", r"\&")
                latex += r"\subsection*{" + name_short + "}\n"
                latex += r"\begin{itemize}" + "\n"
                for s in b["recent_sessions"]:
                    s_clean = s.replace("&", r"\&").replace("#", r"\#").replace("_", r"\_").replace("%", r"\%")
                    latex += r"    \item " + s_clean + "\n"
                latex += r"\end{itemize}" + "\n\n"

        latex += r"\section{Recent Daily Logs}" + "\n\n"
        if recent_logs:
            latex += r"\begin{longtable}{@{} l l p{10cm} @{}}" + "\n"
            latex += r"\toprule" + "\n"
            latex += r"\textbf{Date} & \textbf{Block} & \textbf{Log} \\" + "\n"
            latex += r"\midrule" + "\n"
            latex += r"\endhead" + "\n"
            for log in recent_logs:
                date, block_name, text = log
                block_clean = block_name.replace("&", r"\&")
                text_clean = text.replace("&", r"\&").replace("#", r"\#").replace("_", r"\_").replace("%", r"\%")
                text_clean = text_clean[:150]
                latex += f"{date} & {block_clean} & {text_clean} \\\\\n"
            latex += r"\bottomrule" + "\n"
            latex += r"\end{longtable}" + "\n"
        else:
            latex += r"\textit{No logs recorded in this period.}" + "\n"

        latex += r"""
\section{Gantt Chart (Overall Timeline)}

\begin{tabularx}{\textwidth}{@{} l *{12}{>{\centering\arraybackslash}X} @{}}
\toprule
\textbf{Phase} & \textbf{M1} & \textbf{M2} & \textbf{M3} & \textbf{M4} & \textbf{M5} & \textbf{M6} & \textbf{M7} & \textbf{M8} & \textbf{M9} & \textbf{M10} & \textbf{M11} & \textbf{M12} \\
\midrule
API \& DB    & \cellcolor{primary} & \cellcolor{primary} & & & & & & & & & & \\
Graph Memory   & & & \cellcolor{primary} & \cellcolor{primary} & & & & & & & & \\
Multi-Agent       & & & & & \cellcolor{primary} & \cellcolor{primary} & & & & & & \\
Evaluation & & & & & & & \cellcolor{primary} & \cellcolor{primary} & & & & \\
Deployment      & & & & & & & & & \cellcolor{primary} & \cellcolor{primary} & & \\
Writing         & & & & & & \cellcolor{highlight} & \cellcolor{highlight} & \cellcolor{highlight} & \cellcolor{primary} & \cellcolor{primary} & \cellcolor{primary} & \\
Defense    & & & & & & & & & & & & \cellcolor{primary} \\
\bottomrule
\end{tabularx}

\vspace{1cm}
\begin{tcolorbox}[colback=white, colframe=success, title=\textbf{Academic Sign-off}]
\vspace{0.5cm}
\noindent
\textbf{Student Signature:} \hrulefill \hfill \textbf{Date:} \hrulefill \\
\vspace{0.5cm}
\noindent
\textbf{Supervisor Signature:} \hrulefill \hfill \textbf{Date:} \hrulefill
\end{tcolorbox}

\end{document}
"""
        return latex

    def generate_latex(self):
        latex_content = self.generate_latex_content()
        self.latex_preview.delete("1.0", tk.END)
        self.latex_preview.insert("1.0", latex_content)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX files", "*.tex")],
            initialfile=f"thesis_report_{datetime.now().strftime('%Y%m%d')}.tex"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(latex_content)
            self.report_status.config(text=f"LaTeX saved: {save_path}", fg="#a6e3a1")

    def generate_and_compile(self):
        latex_content = self.generate_latex_content()
        self.latex_preview.delete("1.0", tk.END)
        self.latex_preview.insert("1.0", latex_content)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX files", "*.tex")],
            initialfile=f"thesis_report_{datetime.now().strftime('%Y%m%d')}.tex"
        )
        if not save_path:
            return

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        directory = os.path.dirname(save_path)
        filename = os.path.basename(save_path)

        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", filename],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=60
            )
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", filename],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=60
            )

            pdf_path = save_path.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                self.report_status.config(text=f"PDF generated: {pdf_path}", fg="#a6e3a1")
                if os.name == "nt":
                    os.startfile(pdf_path)
                elif os.name == "posix":
                    subprocess.run(["xdg-open", pdf_path])
            else:
                self.report_status.config(text="Compilation failed. Check LaTeX log.", fg="#f38ba8")
                messagebox.showerror("LaTeX Error", result.stdout[-2000:] if result.stdout else "Unknown error")
        except FileNotFoundError:
            self.report_status.config(text="pdflatex not found. Install TeX distribution.", fg="#f38ba8")
            messagebox.showerror("Error", "pdflatex command not found.\nMake sure TeX Live or MiKTeX is installed and in PATH.")
        except subprocess.TimeoutExpired:
            self.report_status.config(text="Compilation timed out.", fg="#f38ba8")

    # ─────────────────────────────────────────────────────────────────────
    # HISTORY TAB
    # ─────────────────────────────────────────────────────────────────────

    def build_history_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  History  ")

        title = tk.Label(frame, text="SESSION HISTORY", font=("Segoe UI", 16, "bold"),
                         bg="#1e1e2e", fg="#89b4fa")
        title.pack(pady=10)

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(filter_frame, text="Filter by Block:").pack(side=tk.LEFT)
        self.hist_filter_var = tk.StringVar(value="All")
        block_names = ["All"] + [b[1] for b in self.block_options]
        ttk.Combobox(filter_frame, textvariable=self.hist_filter_var, values=block_names,
                     state="readonly", width=40).pack(side=tk.LEFT, padx=10)
        tk.Button(filter_frame, text="Refresh", bg="#89b4fa", fg="#1e1e2e",
                  command=self.refresh_history).pack(side=tk.LEFT, padx=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.hist_tree = ttk.Treeview(tree_frame,
                                      columns=("date", "block", "duration", "description"),
                                      show="headings", height=18)
        self.hist_tree.heading("date", text="Date & Time")
        self.hist_tree.heading("block", text="Block")
        self.hist_tree.heading("duration", text="Duration")
        self.hist_tree.heading("description", text="Description")
        self.hist_tree.column("date", width=150)
        self.hist_tree.column("block", width=200)
        self.hist_tree.column("duration", width=80)
        self.hist_tree.column("description", width=400)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=scrollbar.set)
        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_history()

    def refresh_history(self):
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        filter_val = self.hist_filter_var.get()
        if filter_val == "All":
            c.execute('''SELECT s.start_time, b.name, s.duration_minutes, s.description
                         FROM sessions s JOIN blocks b ON s.block_id = b.id
                         ORDER BY s.start_time DESC''')
        else:
            c.execute('''SELECT s.start_time, b.name, s.duration_minutes, s.description
                         FROM sessions s JOIN blocks b ON s.block_id = b.id
                         WHERE b.name = ?
                         ORDER BY s.start_time DESC''', (filter_val,))

        for row in c.fetchall():
            duration_str = f"{row[2]:.0f} min"
            desc_short = row[3][:80] if row[3] else ""
            self.hist_tree.insert("", tk.END, values=(row[0], row[1], duration_str, desc_short))
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# RUN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ThesisTracker(root)
    root.mainloop()