import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
from utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button,
                   create_progress_bar, get_status_color)


class GrammarPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="📐 Grammar Tracker", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Add Topic", self.show_add_dialog)
        btn.pack(side='right')

        # Filter
        filter_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        filter_frame.pack(fill='x', pady=(0, 10))

        languages = db.get_languages()
        lang_options = ["All Languages"] + [l['name'] for l in languages]
        self.lang_var = tk.StringVar(value="All Languages")

        tk.Label(filter_frame, text="Language:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')
        lang_combo = ttk.Combobox(filter_frame, textvariable=self.lang_var,
                                  values=lang_options, state='readonly', width=15)
        lang_combo.pack(side='left', padx=5)
        lang_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Grammar topics list
        list_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('language', 'title', 'category', 'status', 'mastery', 'review_count', 'last_reviewed')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)

        self.tree.heading('language', text='Lang')
        self.tree.heading('title', text='Topic')
        self.tree.heading('category', text='Category')
        self.tree.heading('status', text='Status')
        self.tree.heading('mastery', text='Mastery')
        self.tree.heading('review_count', text='Reviews')
        self.tree.heading('last_reviewed', text='Last Review')

        self.tree.column('language', width=50, anchor='center')
        self.tree.column('title', width=200)
        self.tree.column('category', width=120)
        self.tree.column('status', width=100, anchor='center')
        self.tree.column('mastery', width=100, anchor='center')
        self.tree.column('review_count', width=80, anchor='center')
        self.tree.column('last_reviewed', width=100)

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

        topics = db.get_grammar_topics(language_id)

        for topic in topics:
            lang = db.get_language_by_id(topic['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'

            mastery_bar = f"{topic['mastery_percent']}%"

            self.tree.insert('', 'end', iid=str(topic['id']), values=(
                lang_icon,
                topic['title'],
                topic['category'] or '',
                topic['status'],
                mastery_bar,
                topic['review_count'],
                topic['last_reviewed'] or 'Never'
            ), tags=(topic['status'],))

        self.tree.tag_configure('Not Started', foreground=COLORS['text_muted'])
        self.tree.tag_configure('Learning', foreground=COLORS['warning'])
        self.tree.tag_configure('Practicing', foreground=COLORS['info'])
        self.tree.tag_configure('Reviewing', foreground=COLORS['accent'])
        self.tree.tag_configure('Solid', foreground=COLORS['success'])

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Grammar Topic")
        dialog.geometry("550x650")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 325
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text="📐 Add Grammar Topic", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language *", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Title
        title_frame, title_entry = create_input_field(main, "Topic Title *", "", COLORS['bg_card'])
        title_frame.pack(fill='x', pady=5)

        # Category
        categories = ["Tenses", "Cases", "Articles", "Verbs", "Nouns", "Adjectives",
                      "Prepositions", "Sentence Structure", "Pronouns", "Modal Verbs",
                      "Passive", "Subjunctive", "Conditionals", "Other"]
        cat_frame, cat_var, _ = create_dropdown(main, "Category", categories, COLORS['bg_card'])
        cat_frame.pack(fill='x', pady=5)

        # Explanation
        expl_frame, expl_text = create_text_area(main, "Explanation / Rules", 4, COLORS['bg_card'])
        expl_frame.pack(fill='x', pady=5)

        # Examples
        example_frame, example_text = create_text_area(main, "Examples", 3, COLORS['bg_card'])
        example_frame.pack(fill='x', pady=5)

        # Resource
        resource_frame, resource_entry = create_input_field(main, "Source / Resource", "", COLORS['bg_card'])
        resource_frame.pack(fill='x', pady=5)

        # Notes
        notes_frame, notes_text = create_text_area(main, "Notes", 2, COLORS['bg_card'])
        notes_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_topic():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Topic title is required!")
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

            db.add_grammar_topic(
                language_id=language_id,
                title=title,
                category=cat_var.get(),
                explanation=expl_text.get("1.0", "end").strip(),
                examples=example_text.get("1.0", "end").strip(),
                rules="",
                resource=resource_entry.get().strip(),
                notes=notes_text.get("1.0", "end").strip()
            )

            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Success", f"Grammar topic '{title}' added!")

        save_btn = create_rounded_button(btn_frame, "💾 Save", save_topic, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        topic_id = int(selected[0])
        self.show_detail_dialog(topic_id)

    def show_detail_dialog(self, topic_id):
        conn = db.get_connection()
        topic = conn.execute("SELECT * FROM grammar_topics WHERE id=?", (topic_id,)).fetchone()
        conn.close()

        if not topic:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Grammar: {topic['title']}")
        dialog.geometry("600x650")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        canvas = tk.Canvas(dialog, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        main = tk.Frame(canvas, bg=COLORS['bg_card'], padx=25, pady=20)

        main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        lang = db.get_language_by_id(topic['language_id'])

        # Header
        tk.Label(main, text=f"{lang['icon']} {topic['title']}", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))

        tk.Label(main, text=f"Category: {topic['category'] or 'N/A'}  |  Status: {topic['status']}",
                 font=FONTS['small'], bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 15))

        # Mastery
        mastery_frame = tk.Frame(main, bg=COLORS['bg_card'])
        mastery_frame.pack(fill='x', pady=10)
        tk.Label(mastery_frame, text=f"Mastery: {topic['mastery_percent']}%", font=FONTS['body_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['success']).pack(anchor='w')
        progress = create_progress_bar(mastery_frame, topic['mastery_percent'], 100, COLORS['success'])
        progress.pack(fill='x', pady=(5, 0))

        # Explanation
        if topic['explanation']:
            tk.Label(main, text="📖 Explanation:", font=FONTS['heading'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(15, 5))
            tk.Label(main, text=topic['explanation'], font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     wraplength=500, justify='left').pack(anchor='w')

        # Examples
        if topic['examples']:
            tk.Label(main, text="💡 Examples:", font=FONTS['heading'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(15, 5))
            tk.Label(main, text=topic['examples'], font=FONTS['mono'],
                     bg=COLORS['bg_card'], fg=COLORS['info'],
                     wraplength=500, justify='left').pack(anchor='w')

        # Notes
        if topic['notes']:
            tk.Label(main, text="📝 Notes:", font=FONTS['heading'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(15, 5))
            tk.Label(main, text=topic['notes'], font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     wraplength=500, justify='left').pack(anchor='w')

        # Action buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(25, 0))

        # Update mastery
        mastery_update_frame = tk.Frame(main, bg=COLORS['bg_card'])
        mastery_update_frame.pack(fill='x', pady=10)

        tk.Label(mastery_update_frame, text="Update Mastery:", font=FONTS['small_bold'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='left')

        mastery_var = tk.IntVar(value=topic['mastery_percent'])
        mastery_scale = tk.Scale(mastery_update_frame, from_=0, to=100, orient='horizontal',
                                 variable=mastery_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                 highlightthickness=0, troughcolor=COLORS['input_bg'],
                                 activebackground=COLORS['success'], length=200)
        mastery_scale.pack(side='left', padx=10)

        # Status update
        status_options = ["Not Started", "Learning", "Practicing", "Reviewing", "Solid"]
        status_var = tk.StringVar(value=topic['status'])
        status_combo = ttk.Combobox(mastery_update_frame, textvariable=status_var,
                                    values=status_options, state='readonly', width=12)
        status_combo.pack(side='left', padx=5)

        def update_mastery():
            db.update_grammar_mastery(topic_id, mastery_var.get(), status_var.get())
            # Also update review count and last reviewed
            conn = db.get_connection()
            conn.execute("""
                UPDATE grammar_topics SET review_count=review_count+1, last_reviewed=? WHERE id=?
            """, (datetime.now().strftime("%Y-%m-%d"), topic_id))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Updated", "Mastery updated!")

        def delete_topic():
            if messagebox.askyesno("Confirm", f"Delete '{topic['title']}'?"):
                conn = db.get_connection()
                conn.execute("DELETE FROM grammar_topics WHERE id=?", (topic_id,))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.refresh_list()

        action_frame = tk.Frame(main, bg=COLORS['bg_card'])
        action_frame.pack(fill='x', pady=(10, 0))

        save_btn = create_rounded_button(action_frame, "💾 Update", update_mastery, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        del_btn = create_rounded_button(action_frame, "🗑️ Delete", delete_topic, bg=COLORS['accent'])
        del_btn.pack(side='left', padx=(0, 10))

        close_btn = create_rounded_button(action_frame, "Close", dialog.destroy, bg=COLORS['btn_secondary'])
        close_btn.pack(side='left')