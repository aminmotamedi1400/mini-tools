import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import App.database as db
from App.utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button,
                   create_scrollable_frame, get_status_color)


class VocabularyPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="📝 Vocabulary Manager", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Add Word", self.show_add_dialog)
        btn.pack(side='right')

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

        # Status filter
        self.status_var = tk.StringVar(value="All Status")
        status_options = ["All Status", "New", "Learning", "Reviewing", "Mastered"]
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

        # Stats bar
        self.stats_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        self.stats_frame.pack(fill='x', pady=(0, 10))
        self.update_stats()

        # Word list with Treeview
        list_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('language', 'word', 'meaning', 'article', 'pos', 'status', 'difficulty', 'next_review')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)

        self.tree.heading('language', text='Lang')
        self.tree.heading('word', text='Word')
        self.tree.heading('meaning', text='Meaning')
        self.tree.heading('article', text='Article')
        self.tree.heading('pos', text='Part of Speech')
        self.tree.heading('status', text='Status')
        self.tree.heading('difficulty', text='Diff')
        self.tree.heading('next_review', text='Next Review')

        self.tree.column('language', width=50, anchor='center')
        self.tree.column('word', width=150)
        self.tree.column('meaning', width=200)
        self.tree.column('article', width=60, anchor='center')
        self.tree.column('pos', width=100)
        self.tree.column('status', width=90, anchor='center')
        self.tree.column('difficulty', width=70, anchor='center')
        self.tree.column('next_review', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)

        self.refresh_list()

    def update_stats(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        stats = db.get_vocabulary_stats()
        stats_text = (f"Total: {stats['total']}  |  "
                      f"🆕 New: {stats.get('new', 0)}  |  "
                      f"📖 Learning: {stats.get('learning', 0)}  |  "
                      f"🔄 Reviewing: {stats.get('reviewing', 0)}  |  "
                      f"✅ Mastered: {stats.get('mastered', 0)}")

        tk.Label(self.stats_frame, text=stats_text, font=FONTS['small'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        lang_filter = self.lang_var.get()
        status_filter = self.status_var.get()
        search = self.search_var.get().strip()

        language_id = None
        if lang_filter != "All Languages":
            languages = db.get_languages()
            for l in languages:
                if l['name'] == lang_filter:
                    language_id = l['id']
                    break

        status = None if status_filter == "All Status" else status_filter
        search_term = search if search else None

        words = db.get_vocabulary(language_id=language_id, status=status, search=search_term)

        for word in words:
            lang = db.get_language_by_id(word['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'
            difficulty_stars = "⭐" * word['difficulty']

            self.tree.insert('', 'end', iid=str(word['id']), values=(
                lang_icon,
                word['word'],
                word['meaning'] or '',
                word['article'] or '',
                word['part_of_speech'] or '',
                word['status'],
                difficulty_stars,
                word['next_review'] or ''
            ), tags=(word['status'],))

        self.tree.tag_configure('New', foreground=COLORS['info'])
        self.tree.tag_configure('Learning', foreground=COLORS['warning'])
        self.tree.tag_configure('Reviewing', foreground=COLORS['accent'])
        self.tree.tag_configure('Mastered', foreground=COLORS['success'])

        self.update_stats()

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Word")
        dialog.geometry("550x700")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 350
        dialog.geometry(f"+{x}+{y}")

        # Scrollable content
        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(main, text="📝 Add New Word", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Word
        word_frame, word_entry = create_input_field(main, "Word *", "", COLORS['bg_card'])
        word_frame.pack(fill='x', pady=5)

        # Meaning
        meaning_frame, meaning_entry = create_input_field(main, "Meaning *", "", COLORS['bg_card'])
        meaning_frame.pack(fill='x', pady=5)

        # Article (for German)
        article_frame, article_entry = create_input_field(main, "Article (der/die/das)", "", COLORS['bg_card'])
        article_frame.pack(fill='x', pady=5)

        # Plural
        plural_frame, plural_entry = create_input_field(main, "Plural", "", COLORS['bg_card'])
        plural_frame.pack(fill='x', pady=5)

        # Pronunciation
        pron_frame, pron_entry = create_input_field(main, "Pronunciation", "", COLORS['bg_card'])
        pron_frame.pack(fill='x', pady=5)

        # Part of Speech
        pos_options = ["Noun", "Verb", "Adjective", "Adverb", "Preposition",
                       "Conjunction", "Pronoun", "Article", "Interjection", "Phrase", "Other"]
        pos_frame, pos_var, _ = create_dropdown(main, "Part of Speech", pos_options, COLORS['bg_card'])
        pos_frame.pack(fill='x', pady=5)

        # Example
        example_frame, example_text = create_text_area(main, "Example Sentence", 3, COLORS['bg_card'])
        example_frame.pack(fill='x', pady=5)

        # Collocations
        colloc_frame, colloc_entry = create_input_field(main, "Collocations", "", COLORS['bg_card'])
        colloc_frame.pack(fill='x', pady=5)

        # Tags
        tags_frame, tags_entry = create_input_field(main, "Tags (comma separated)", "", COLORS['bg_card'])
        tags_frame.pack(fill='x', pady=5)

        # Difficulty
        diff_frame = tk.Frame(main, bg=COLORS['bg_card'])
        diff_frame.pack(fill='x', pady=5)
        tk.Label(diff_frame, text="Difficulty (1-5)", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        diff_var = tk.IntVar(value=3)
        diff_scale = tk.Scale(diff_frame, from_=1, to=5, orient='horizontal',
                              variable=diff_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                              highlightthickness=0, troughcolor=COLORS['input_bg'],
                              activebackground=COLORS['accent'])
        diff_scale.pack(fill='x')

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_word():
            word = word_entry.get().strip()
            meaning = meaning_entry.get().strip()

            if not word or not meaning:
                messagebox.showwarning("Warning", "Word and Meaning are required!")
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

            db.add_vocabulary(
                language_id=language_id,
                word=word,
                meaning=meaning,
                article=article_entry.get().strip(),
                plural=plural_entry.get().strip(),
                pronunciation=pron_entry.get().strip(),
                part_of_speech=pos_var.get(),
                example=example_text.get("1.0", "end").strip(),
                collocations=colloc_entry.get().strip(),
                tags=tags_entry.get().strip(),
                difficulty=diff_var.get()
            )

            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Success", f"Word '{word}' added successfully!")

        save_btn = create_rounded_button(btn_frame, "💾 Save Word", save_word, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item_id = int(selected[0])
        self.show_edit_dialog(item_id)

    def show_edit_dialog(self, vocab_id):
        conn = db.get_connection()
        word_data = conn.execute("SELECT * FROM vocabulary WHERE id=?", (vocab_id,)).fetchone()
        conn.close()

        if not word_data:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit: {word_data['word']}")
        dialog.geometry("550x750")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 375
        dialog.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(main, text=f"✏️ Edit: {word_data['word']}", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        # Language (readonly)
        lang = db.get_language_by_id(word_data['language_id'])
        tk.Label(main, text=f"Language: {lang['icon']} {lang['name']}", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['info']).pack(anchor='w', pady=5)

        # Word
        word_frame, word_entry = create_input_field(main, "Word", "", COLORS['bg_card'])
        word_frame.pack(fill='x', pady=5)
        word_entry.insert(0, word_data['word'] or '')

        # Meaning
        meaning_frame, meaning_entry = create_input_field(main, "Meaning", "", COLORS['bg_card'])
        meaning_frame.pack(fill='x', pady=5)
        meaning_entry.insert(0, word_data['meaning'] or '')

        # Article
        article_frame, article_entry = create_input_field(main, "Article", "", COLORS['bg_card'])
        article_frame.pack(fill='x', pady=5)
        article_entry.insert(0, word_data['article'] or '')

        # Plural
        plural_frame, plural_entry = create_input_field(main, "Plural", "", COLORS['bg_card'])
        plural_frame.pack(fill='x', pady=5)
        plural_entry.insert(0, word_data['plural'] or '')

        # Example
        example_frame, example_text = create_text_area(main, "Example", 3, COLORS['bg_card'])
        example_frame.pack(fill='x', pady=5)
        example_text.insert("1.0", word_data['example_sentence'] or '')

        # Status
        status_options = ["New", "Learning", "Reviewing", "Mastered"]
        status_frame, status_var, _ = create_dropdown(main, "Status", status_options, COLORS['bg_card'])
        status_frame.pack(fill='x', pady=5)
        status_var.set(word_data['status'])

        # Difficulty
        diff_frame = tk.Frame(main, bg=COLORS['bg_card'])
        diff_frame.pack(fill='x', pady=5)
        tk.Label(diff_frame, text="Difficulty", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        diff_var = tk.IntVar(value=word_data['difficulty'])
        diff_scale = tk.Scale(diff_frame, from_=1, to=5, orient='horizontal',
                              variable=diff_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                              highlightthickness=0, troughcolor=COLORS['input_bg'],
                              activebackground=COLORS['accent'])
        diff_scale.pack(fill='x')

        # Info
        info_frame = tk.Frame(main, bg=COLORS['bg_card'])
        info_frame.pack(fill='x', pady=10)
        tk.Label(info_frame, text=f"✅ Success: {word_data['success_count']}  |  "
                                  f"❌ Failures: {word_data['failure_count']}  |  "
                                  f"🔄 Reps: {word_data['repetitions']}",
                 font=FONTS['small'], bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_edit():
            conn = db.get_connection()
            conn.execute("""
                UPDATE vocabulary SET word=?, meaning=?, article=?, plural=?,
                example_sentence=?, status=?, difficulty=? WHERE id=?
            """, (word_entry.get().strip(), meaning_entry.get().strip(),
                  article_entry.get().strip(), plural_entry.get().strip(),
                  example_text.get("1.0", "end").strip(), status_var.get(),
                  diff_var.get(), vocab_id))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.refresh_list()

        def delete_word():
            if messagebox.askyesno("Confirm", f"Delete '{word_data['word']}'?"):
                conn = db.get_connection()
                conn.execute("DELETE FROM vocabulary WHERE id=?", (vocab_id,))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.refresh_list()

        save_btn = create_rounded_button(btn_frame, "💾 Save", save_edit, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        del_btn = create_rounded_button(btn_frame, "🗑️ Delete", delete_word, bg=COLORS['accent'])
        del_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def show_context_menu(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        menu = tk.Menu(self.parent, tearoff=0, bg=COLORS['bg_card'],
                       fg=COLORS['text_primary'], font=FONTS['body'])
        menu.add_command(label="✏️ Edit", command=lambda: self.on_double_click(None))
        menu.add_command(label="✅ Mark as Mastered", command=lambda: self.quick_status_change("Mastered"))
        menu.add_command(label="📖 Mark as Learning", command=lambda: self.quick_status_change("Learning"))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=self.delete_selected)

        menu.post(event.x_root, event.y_root)

    def quick_status_change(self, status):
        selected = self.tree.selection()
        if not selected:
            return

        conn = db.get_connection()
        for item_id in selected:
            conn.execute("UPDATE vocabulary SET status=? WHERE id=?", (status, int(item_id)))
        conn.commit()
        conn.close()
        self.refresh_list()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm", f"Delete {len(selected)} item(s)?"):
            conn = db.get_connection()
            for item_id in selected:
                conn.execute("DELETE FROM vocabulary WHERE id=?", (int(item_id),))
            conn.commit()
            conn.close()
            self.refresh_list()