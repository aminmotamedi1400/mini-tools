import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import App.database as db
from App.utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button,
                   format_duration)


class SessionsPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="📚 Study Sessions", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Log Session", self.show_add_dialog)
        btn.pack(side='right')

        # Quick stats
        stats_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        stats_frame.pack(fill='x', pady=(0, 15))

        total_time = db.get_total_study_time()
        today_sessions = db.get_today_sessions()
        today_time = sum(s['duration_minutes'] for s in today_sessions)
        streak = db.get_streak()

        stats_text = (f"🔥 Streak: {streak} days  |  "
                      f"📅 Today: {format_duration(today_time)}  |  "
                      f"⏱️ Total: {format_duration(total_time)}")

        tk.Label(stats_frame, text=stats_text, font=FONTS['body'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')

        # Filter
        filter_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        filter_frame.pack(fill='x', pady=(0, 10))

        languages = db.get_languages()
        lang_options = ["All Languages"] + [l['name'] for l in languages]
        self.lang_var = tk.StringVar(value="All Languages")

        tk.Label(filter_frame, text="Filter:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        lang_combo = ttk.Combobox(filter_frame, textvariable=self.lang_var,
                                  values=lang_options, state='readonly', width=15)
        lang_combo.pack(side='left', padx=5)
        lang_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Sessions list
        list_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('date', 'language', 'duration', 'resource', 'topic', 'skills', 'difficulty', 'feeling')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)

        self.tree.heading('date', text='Date')
        self.tree.heading('language', text='Language')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('resource', text='Resource')
        self.tree.heading('topic', text='Topic')
        self.tree.heading('skills', text='Skills')
        self.tree.heading('difficulty', text='Difficulty')
        self.tree.heading('feeling', text='Feeling')

        self.tree.column('date', width=100)
        self.tree.column('language', width=80, anchor='center')
        self.tree.column('duration', width=80, anchor='center')
        self.tree.column('resource', width=150)
        self.tree.column('topic', width=150)
        self.tree.column('skills', width=120)
        self.tree.column('difficulty', width=80, anchor='center')
        self.tree.column('feeling', width=80, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.on_double_click)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        lang_filter = self.lang_var.get()
        language_id = None

        if lang_filter != "All Languages":
            languages = db.get_languages()
            for l in languages:
                if l['name'] == lang_filter:
                    language_id = l['id']
                    break

        sessions = db.get_study_sessions(language_id=language_id, limit=100)

        for session in sessions:
            lang = db.get_language_by_id(session['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'

            # Get resource name
            resource_name = ""
            if session['resource_id']:
                resources = db.get_resources()
                for r in resources:
                    if r['id'] == session['resource_id']:
                        resource_name = r['name']
                        break

            difficulty_map = {1: "😊 Easy", 2: "🙂 OK", 3: "😐 Medium", 4: "😰 Hard", 5: "🤯 Very Hard"}
            feeling_map = {1: "😞", 2: "😕", 3: "😐", 4: "🙂", 5: "😄"}

            self.tree.insert('', 'end', iid=str(session['id']), values=(
                session['date'],
                f"{lang_icon} {lang['name']}" if lang else '',
                f"{session['duration_minutes']} min",
                resource_name,
                session['topic'] or '',
                session['skills'] or '',
                difficulty_map.get(session['difficulty'], ''),
                feeling_map.get(session['feeling'], ''),
            ))

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Log Study Session")
        dialog.geometry("550x700")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 350
        dialog.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(main, text="📚 Log Study Session", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, lang_combo = create_dropdown(main, "Language *", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Resource (dynamic based on language)
        resource_frame = tk.Frame(main, bg=COLORS['bg_card'])
        resource_frame.pack(fill='x', pady=5)
        tk.Label(resource_frame, text="Resource", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
        resource_var = tk.StringVar()
        resource_combo = ttk.Combobox(resource_frame, textvariable=resource_var, state='readonly')
        resource_combo.pack(fill='x', ipady=4)

        def update_resources(*args):
            selected_lang = lang_var.get()
            for l in languages:
                if l['name'] == selected_lang:
                    resources = db.get_resources(l['id'])
                    resource_combo['values'] = [r['name'] for r in resources]
                    if resources:
                        resource_var.set(resources[0]['name'])
                    break

        lang_var.trace('w', update_resources)
        if lang_names:
            update_resources()

        # Date
        date_frame, date_entry = create_input_field(main, "Date", datetime.now().strftime("%Y-%m-%d"),
                                                    COLORS['bg_card'])
        date_frame.pack(fill='x', pady=5)
        date_entry.delete(0, 'end')
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Duration
        dur_frame, dur_entry = create_input_field(main, "Duration (minutes) *", "", COLORS['bg_card'])
        dur_frame.pack(fill='x', pady=5)

        # Unit/Lesson
        unit_frame, unit_entry = create_input_field(main, "Unit / Lesson", "", COLORS['bg_card'])
        unit_frame.pack(fill='x', pady=5)

        # Topic
        topic_frame, topic_entry = create_input_field(main, "Topic", "", COLORS['bg_card'])
        topic_frame.pack(fill='x', pady=5)

        # Skills
        skills_frame = tk.Frame(main, bg=COLORS['bg_card'])
        skills_frame.pack(fill='x', pady=5)
        tk.Label(skills_frame, text="Skills Practiced", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))

        skills_vars = {}
        skills_inner = tk.Frame(skills_frame, bg=COLORS['bg_card'])
        skills_inner.pack(fill='x')
        for skill in ['Reading', 'Listening', 'Writing', 'Speaking', 'Grammar', 'Vocabulary']:
            var = tk.BooleanVar()
            skills_vars[skill] = var
            cb = tk.Checkbutton(skills_inner, text=skill, variable=var,
                                bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['input_bg'], font=FONTS['body'],
                                activebackground=COLORS['bg_card'],
                                activeforeground=COLORS['text_primary'])
            cb.pack(side='left', padx=5)

        # New words count
        words_frame, words_entry = create_input_field(main, "New Words Learned", "0", COLORS['bg_card'])
        words_frame.pack(fill='x', pady=5)
        words_entry.delete(0, 'end')
        words_entry.insert(0, "0")

        # Difficulty
        diff_frame = tk.Frame(main, bg=COLORS['bg_card'])
        diff_frame.pack(fill='x', pady=5)
        tk.Label(diff_frame, text="Difficulty (1=Easy, 5=Very Hard)", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        diff_var = tk.IntVar(value=3)
        diff_scale = tk.Scale(diff_frame, from_=1, to=5, orient='horizontal',
                              variable=diff_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                              highlightthickness=0, troughcolor=COLORS['input_bg'],
                              activebackground=COLORS['accent'])
        diff_scale.pack(fill='x')

        # Feeling
        feel_frame = tk.Frame(main, bg=COLORS['bg_card'])
        feel_frame.pack(fill='x', pady=5)
        tk.Label(feel_frame, text="How do you feel? (1=Bad, 5=Great)", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        feel_var = tk.IntVar(value=3)
        feel_scale = tk.Scale(feel_frame, from_=1, to=5, orient='horizontal',
                              variable=feel_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                              highlightthickness=0, troughcolor=COLORS['input_bg'],
                              activebackground=COLORS['success'])
        feel_scale.pack(fill='x')

        # Notes
        notes_frame, notes_text = create_text_area(main, "Notes", 3, COLORS['bg_card'])
        notes_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_session():
            try:
                duration = int(dur_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Warning", "Duration must be a number!")
                return

            if duration <= 0:
                messagebox.showwarning("Warning", "Duration must be positive!")
                return

            # Get language id
            lang_name = lang_var.get()
            language_id = None
            for l in languages:
                if l['name'] == lang_name:
                    language_id = l['id']
                    break

            if not language_id:
                messagebox.showwarning("Warning", "Please select a language!")
                return

            # Get resource id
            resource_id = None
            res_name = resource_var.get()
            if res_name:
                resources = db.get_resources(language_id)
                for r in resources:
                    if r['name'] == res_name:
                        resource_id = r['id']
                        break

            # Get skills
            selected_skills = [s for s, v in skills_vars.items() if v.get()]
            skills_str = ", ".join(selected_skills)

            try:
                new_words = int(words_entry.get().strip())
            except ValueError:
                new_words = 0

            db.add_study_session(
                language_id=language_id,
                resource_id=resource_id,
                date=date_entry.get().strip(),
                duration=duration,
                unit_lesson=unit_entry.get().strip(),
                topic=topic_entry.get().strip(),
                skills=skills_str,
                new_words=new_words,
                new_grammar=0,
                difficulty=diff_var.get(),
                feeling=feel_var.get(),
                notes=notes_text.get("1.0", "end").strip()
            )

            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Success", "Study session logged! 🎉")

        save_btn = create_rounded_button(btn_frame, "💾 Save Session", save_session, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        session_id = int(selected[0])
        conn = db.get_connection()
        session = conn.execute("SELECT * FROM study_sessions WHERE id=?", (session_id,)).fetchone()
        conn.close()

        if not session:
            return

        # Show details dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Session Details")
        dialog.geometry("450x500")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        lang = db.get_language_by_id(session['language_id'])

        tk.Label(main, text=f"📚 Session Details", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        details = [
            ("Language", f"{lang['icon']} {lang['name']}" if lang else "Unknown"),
            ("Date", session['date']),
            ("Duration", f"{session['duration_minutes']} minutes"),
            ("Unit/Lesson", session['unit_lesson'] or 'N/A'),
            ("Topic", session['topic'] or 'N/A'),
            ("Skills", session['skills'] or 'N/A'),
            ("New Words", str(session['new_words_count'])),
            ("Difficulty", f"{session['difficulty']}/5"),
            ("Feeling", f"{session['feeling']}/5"),
            ("Notes", session['notes'] or 'N/A'),
        ]

        for label, value in details:
            row = tk.Frame(main, bg=COLORS['bg_card'])
            row.pack(fill='x', pady=3)
            tk.Label(row, text=f"{label}:", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'], width=12, anchor='w').pack(side='left')
            tk.Label(row, text=value, font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary'], wraplength=300, anchor='w').pack(side='left')

        # Delete button
        def delete_session():
            if messagebox.askyesno("Confirm", "Delete this session?"):
                conn = db.get_connection()
                conn.execute("DELETE FROM study_sessions WHERE id=?", (session_id,))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.refresh_list()

        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))
        del_btn = create_rounded_button(btn_frame, "🗑️ Delete", delete_session, bg=COLORS['accent'])
        del_btn.pack(side='left')
        close_btn = create_rounded_button(btn_frame, "Close", dialog.destroy, bg=COLORS['btn_secondary'])
        close_btn.pack(side='right')