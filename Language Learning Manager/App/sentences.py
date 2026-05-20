import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
from utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button,
                   create_scrollable_frame, get_status_color)


class SentencesPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="💬 Sentence Bank", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Add Sentence", self.show_add_dialog)
        btn.pack(side='right')

        # Info bar
        info_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        info_frame.pack(fill='x', pady=(0, 10))

        tk.Label(info_frame,
                 text="💡 Save useful phrases, patterns, and example sentences for review.",
                 font=FONTS['small'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted']).pack(side='left')

        # Stats
        self.stats_label = tk.Label(info_frame, text="", font=FONTS['small'],
                                    bg=COLORS['bg_medium'], fg=COLORS['text_secondary'])
        self.stats_label.pack(side='right')

        # Filter bar
        filter_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        filter_frame.pack(fill='x', pady=(0, 10))

        # Language filter
        languages = db.get_languages()
        lang_options = ["All Languages"] + [l['name'] for l in languages]
        self.lang_var = tk.StringVar(value="All Languages")

        tk.Label(filter_frame, text="Language:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        lang_combo = ttk.Combobox(filter_frame, textvariable=self.lang_var,
                                  values=lang_options, state='readonly', width=15)
        lang_combo.pack(side='left', padx=(5, 15))
        lang_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Category filter
        self.cat_var = tk.StringVar(value="All Categories")
        cat_options = ["All Categories", "Greeting", "Question", "Answer",
                       "Grammar Pattern", "Common Expression", "Idiom",
                       "Formal", "Informal", "Travel", "Work", "Daily Life", "Other"]
        tk.Label(filter_frame, text="Category:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        cat_combo = ttk.Combobox(filter_frame, textvariable=self.cat_var,
                                 values=cat_options, state='readonly', width=18)
        cat_combo.pack(side='left', padx=(5, 15))
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Status filter
        self.status_var = tk.StringVar(value="All Status")
        status_options = ["All Status", "Learning", "Reviewing", "Known"]
        tk.Label(filter_frame, text="Status:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                    values=status_options, state='readonly', width=12)
        status_combo.pack(side='left', padx=(5, 15))
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Search
        self.search_var = tk.StringVar()
        tk.Label(filter_frame, text="🔍", font=FONTS['body'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var,
                                font=FONTS['body'], bg=COLORS['input_bg'],
                                fg=COLORS['text_primary'], insertbackground=COLORS['text_primary'],
                                relief='flat', width=20)
        search_entry.pack(side='left', padx=5, ipady=4)
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_list())

        # Sentence list
        list_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('language', 'sentence', 'meaning', 'category', 'status', 'source')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)

        self.tree.heading('language', text='Lang')
        self.tree.heading('sentence', text='Sentence')
        self.tree.heading('meaning', text='Meaning / Translation')
        self.tree.heading('category', text='Category')
        self.tree.heading('status', text='Status')
        self.tree.heading('source', text='Source')

        self.tree.column('language', width=55, anchor='center')
        self.tree.column('sentence', width=280)
        self.tree.column('meaning', width=230)
        self.tree.column('category', width=130)
        self.tree.column('status', width=90, anchor='center')
        self.tree.column('source', width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        lang_filter = self.lang_var.get()
        cat_filter = self.cat_var.get()
        status_filter = self.status_var.get()
        search = self.search_var.get().strip().lower()

        language_id = None
        if lang_filter != "All Languages":
            languages = db.get_languages()
            for l in languages:
                if l['name'] == lang_filter:
                    language_id = l['id']
                    break

        sentences = db.get_sentences(language_id)

        count = 0
        for sentence in sentences:
            # Apply filters
            if cat_filter != "All Categories" and sentence['category'] != cat_filter:
                continue
            if status_filter != "All Status" and sentence['status'] != status_filter:
                continue
            if search:
                searchable = (
                    (sentence['sentence'] or '').lower() +
                    (sentence['meaning'] or '').lower() +
                    (sentence['tags'] or '').lower()
                )
                if search not in searchable:
                    continue

            lang = db.get_language_by_id(sentence['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'

            self.tree.insert('', 'end', iid=str(sentence['id']), values=(
                lang_icon,
                sentence['sentence'],
                sentence['meaning'] or '',
                sentence['category'] or '',
                sentence['status'],
                sentence['source'] or '',
            ), tags=(sentence['status'],))

            count += 1

        # Color by status
        self.tree.tag_configure('Learning', foreground=COLORS['warning'])
        self.tree.tag_configure('Reviewing', foreground=COLORS['info'])
        self.tree.tag_configure('Known', foreground=COLORS['success'])

        # Update stats
        total = len(db.get_sentences(language_id))
        self.stats_label.config(text=f"Showing {count} of {total} sentences")

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Sentence / Phrase")
        dialog.geometry("560x580")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 280
        y = (dialog.winfo_screenheight() // 2) - 290
        dialog.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(main, text="💬 Add Sentence / Phrase", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))

        tk.Label(main, text="Save useful sentences, patterns, and expressions.",
                 font=FONTS['small'], bg=COLORS['bg_card'],
                 fg=COLORS['text_muted']).pack(anchor='w', pady=(0, 15))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language *", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Sentence
        sentence_frame, sentence_text = create_text_area(main, "Sentence / Phrase *", 3, COLORS['bg_card'])
        sentence_frame.pack(fill='x', pady=5)

        # Meaning
        meaning_frame, meaning_text = create_text_area(main, "Meaning / Translation", 2, COLORS['bg_card'])
        meaning_frame.pack(fill='x', pady=5)

        # Category
        cat_options = ["Grammar Pattern", "Common Expression", "Idiom", "Greeting",
                       "Question", "Answer", "Formal", "Informal",
                       "Travel", "Work", "Daily Life", "Other"]
        cat_frame, cat_var, _ = create_dropdown(main, "Category", cat_options, COLORS['bg_card'])
        cat_frame.pack(fill='x', pady=5)

        # Tags
        tags_frame, tags_entry = create_input_field(main, "Tags (comma separated)", "", COLORS['bg_card'])
        tags_frame.pack(fill='x', pady=5)

        # Source
        source_frame, source_entry = create_input_field(main, "Source (book, lesson, etc.)", "",
                                                        COLORS['bg_card'])
        source_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_sentence():
            sentence = sentence_text.get("1.0", "end").strip()
            if not sentence:
                messagebox.showwarning("Warning", "Sentence is required!")
                return

            lang_name = lang_var.get()
            language_id = None
            for l in languages:
                if l['name'] == lang_name:
                    language_id = l['id']
                    break

            if not language_id:
                messagebox.showwarning("Warning", "Please select a language!")
                return

            db.add_sentence(
                language_id=language_id,
                sentence=sentence,
                meaning=meaning_text.get("1.0", "end").strip(),
                category=cat_var.get(),
                tags=tags_entry.get().strip(),
                source=source_entry.get().strip()
            )

            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Saved", "Sentence saved! 💬")

        save_btn = create_rounded_button(btn_frame, "💾 Save", save_sentence, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        sentence_id = int(selected[0])
        self.show_detail_dialog(sentence_id)

    def show_detail_dialog(self, sentence_id):
        conn = db.get_connection()
        sentence = conn.execute("SELECT * FROM sentences WHERE id=?", (sentence_id,)).fetchone()
        conn.close()

        if not sentence:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Sentence Details")
        dialog.geometry("560x550")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 280
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        lang = db.get_language_by_id(sentence['language_id'])
        lang_color = COLORS['english'] if lang and lang['name'] == 'English' else COLORS['german']

        # Language badge
        tk.Label(main, text=f"{lang['icon']} {lang['name']}" if lang else "🌐",
                 font=FONTS['body_bold'], bg=COLORS['bg_card'], fg=lang_color).pack(anchor='w')

        # Sentence
        tk.Label(main, text="Sentence:", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w', pady=(15, 3))

        sentence_display = tk.Frame(main, bg=COLORS['bg_light'], padx=15, pady=12)
        sentence_display.pack(fill='x')

        tk.Label(sentence_display, text=sentence['sentence'],
                 font=('Segoe UI', 16, 'bold'), bg=COLORS['bg_light'],
                 fg=COLORS['text_primary'], wraplength=480, justify='left').pack(anchor='w')

        # Meaning
        if sentence['meaning']:
            tk.Label(main, text="Meaning:", font=FONTS['small_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w', pady=(12, 3))

            meaning_display = tk.Frame(main, bg=COLORS['bg_card'],
                                       highlightthickness=1,
                                       highlightbackground=COLORS['border'])
            meaning_display.pack(fill='x')

            tk.Label(meaning_display, text=sentence['meaning'],
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['success'], wraplength=480,
                     justify='left', padx=15, pady=10).pack(anchor='w')

        # Category, Tags, Source
        meta_frame = tk.Frame(main, bg=COLORS['bg_card'])
        meta_frame.pack(fill='x', pady=(15, 0))

        meta_items = [
            ("Category", sentence['category'] or 'N/A'),
            ("Tags", sentence['tags'] or 'N/A'),
            ("Source", sentence['source'] or 'N/A'),
            ("Status", sentence['status']),
            ("Added", sentence['created_at'][:10] if sentence['created_at'] else 'N/A'),
        ]

        for label, value in meta_items:
            row = tk.Frame(meta_frame, bg=COLORS['bg_card'])
            row.pack(fill='x', pady=2)

            tk.Label(row, text=f"{label}:", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     width=10, anchor='w').pack(side='left')
            tk.Label(row, text=value, font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                     anchor='w').pack(side='left')

        # Edit section
        tk.Frame(main, bg=COLORS['border'], height=1).pack(fill='x', pady=(15, 10))

        # Status update
        status_frame = tk.Frame(main, bg=COLORS['bg_card'])
        status_frame.pack(fill='x', pady=5)

        tk.Label(status_frame, text="Update Status:", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='left')

        status_var = tk.StringVar(value=sentence['status'])
        status_options = ["Learning", "Reviewing", "Known"]
        status_combo = ttk.Combobox(status_frame, textvariable=status_var,
                                    values=status_options, state='readonly', width=12)
        status_combo.pack(side='left', padx=(10, 0))

        # Edit notes
        notes_frame, notes_text = create_text_area(main, "Edit Meaning / Notes", 3, COLORS['bg_card'])
        notes_frame.pack(fill='x', pady=5)
        if sentence['meaning']:
            notes_text.insert("1.0", sentence['meaning'])

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        def save_edit():
            conn = db.get_connection()
            conn.execute("""
                UPDATE sentences SET status=?, meaning=? WHERE id=?
            """, (status_var.get(), notes_text.get("1.0", "end").strip(), sentence_id))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.refresh_list()

        def delete_sentence():
            if messagebox.askyesno("Confirm", "Delete this sentence?"):
                conn = db.get_connection()
                conn.execute("DELETE FROM sentences WHERE id=?", (sentence_id,))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.refresh_list()

        save_btn = create_rounded_button(btn_frame, "💾 Save", save_edit, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 8))

        del_btn = create_rounded_button(btn_frame, "🗑️ Delete", delete_sentence, bg=COLORS['accent'])
        del_btn.pack(side='left', padx=(0, 8))

        close_btn = create_rounded_button(btn_frame, "Close", dialog.destroy, bg=COLORS['btn_secondary'])
        close_btn.pack(side='right')

    def show_context_menu(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        menu = tk.Menu(self.parent, tearoff=0, bg=COLORS['bg_card'],
                       fg=COLORS['text_primary'], font=FONTS['body'])
        menu.add_command(label="✏️ View / Edit", command=lambda: self.on_double_click(None))
        menu.add_separator()
        menu.add_command(label="✅ Mark as Known", command=lambda: self.quick_status('Known'))
        menu.add_command(label="🔄 Mark as Reviewing", command=lambda: self.quick_status('Reviewing'))
        menu.add_command(label="📖 Mark as Learning", command=lambda: self.quick_status('Learning'))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=self.delete_selected)

        menu.post(event.x_root, event.y_root)

    def quick_status(self, status):
        selected = self.tree.selection()
        if not selected:
            return

        conn = db.get_connection()
        for item_id in selected:
            conn.execute("UPDATE sentences SET status=? WHERE id=?",
                         (status, int(item_id)))
        conn.commit()
        conn.close()
        self.refresh_list()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm", f"Delete {len(selected)} sentence(s)?"):
            conn = db.get_connection()
            for item_id in selected:
                conn.execute("DELETE FROM sentences WHERE id=?", (int(item_id),))
            conn.commit()
            conn.close()
            self.refresh_list()