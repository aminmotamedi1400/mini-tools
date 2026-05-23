import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import App.database as db
from App.utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button)


class ErrorsPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="❌ Error Log", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Log Error", self.show_add_dialog)
        btn.pack(side='right')

        # Info bar
        info_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        info_frame.pack(fill='x', pady=(0, 10))

        errors_due = db.get_errors_for_review()
        total_errors = db.get_errors()

        info_text = f"📊 Total Errors: {len(total_errors)}"
        if errors_due:
            info_text += f"  |  ⚠️ {len(errors_due)} due for review"

        tk.Label(info_frame, text=info_text, font=FONTS['body'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')

        tk.Label(info_frame,
                 text="💡 Track mistakes to avoid repeating them!",
                 font=FONTS['small'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_muted']).pack(side='right')

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

        # Category filter
        self.cat_var = tk.StringVar(value="All Categories")
        cat_options = ["All Categories", "Vocabulary", "Grammar", "Article", "Plural",
                       "Word Order", "Tense", "Pronunciation", "Preposition", "Spelling", "Other"]
        tk.Label(filter_frame, text="Category:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left', padx=(15, 0))
        cat_combo = ttk.Combobox(filter_frame, textvariable=self.cat_var,
                                 values=cat_options, state='readonly', width=15)
        cat_combo.pack(side='left', padx=5)
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

        # Error list
        list_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('language', 'category', 'wrong', 'correct', 'explanation', 'frequency', 'status', 'next_review')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=16)

        self.tree.heading('language', text='Lang')
        self.tree.heading('category', text='Category')
        self.tree.heading('wrong', text='❌ Wrong')
        self.tree.heading('correct', text='✅ Correct')
        self.tree.heading('explanation', text='Explanation')
        self.tree.heading('frequency', text='Freq')
        self.tree.heading('status', text='Status')
        self.tree.heading('next_review', text='Next Review')

        self.tree.column('language', width=50, anchor='center')
        self.tree.column('category', width=100)
        self.tree.column('wrong', width=150)
        self.tree.column('correct', width=150)
        self.tree.column('explanation', width=200)
        self.tree.column('frequency', width=50, anchor='center')
        self.tree.column('status', width=80, anchor='center')
        self.tree.column('next_review', width=100)

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

        language_id = None
        if lang_filter != "All Languages":
            languages = db.get_languages()
            for l in languages:
                if l['name'] == lang_filter:
                    language_id = l['id']
                    break

        errors = db.get_errors(language_id)

        for error in errors:
            # Apply category filter
            if cat_filter != "All Categories" and error['category'] != cat_filter:
                continue

            lang = db.get_language_by_id(error['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'

            self.tree.insert('', 'end', iid=str(error['id']), values=(
                lang_icon,
                error['category'] or '',
                error['wrong_form'],
                error['correct_form'],
                error['explanation'] or '',
                error['frequency'],
                error['status'],
                error['next_review'] or ''
            ), tags=(error['status'],))

        self.tree.tag_configure('Active', foreground=COLORS['accent'])
        self.tree.tag_configure('Resolved', foreground=COLORS['success'])

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Log Error")
        dialog.geometry("550x550")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text="❌ Log a Mistake", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        tk.Label(main, text="Learning from mistakes is the fastest way to improve!",
                 font=FONTS['small'], bg=COLORS['bg_card'],
                 fg=COLORS['text_muted']).pack(anchor='w', pady=(0, 15))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language *", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Category
        categories = ["Vocabulary", "Grammar", "Article", "Plural", "Word Order",
                      "Tense", "Pronunciation", "Preposition", "Spelling", "Other"]
        cat_frame, cat_var, _ = create_dropdown(main, "Category", categories, COLORS['bg_card'])
        cat_frame.pack(fill='x', pady=5)

        # Wrong form
        wrong_frame, wrong_entry = create_input_field(main, "❌ What I said/wrote (Wrong) *", "", COLORS['bg_card'])
        wrong_frame.pack(fill='x', pady=5)

        # Correct form
        correct_frame, correct_entry = create_input_field(main, "✅ Correct form *", "", COLORS['bg_card'])
        correct_frame.pack(fill='x', pady=5)

        # Explanation
        expl_frame, expl_text = create_text_area(main, "Why is it wrong? / Explanation", 3, COLORS['bg_card'])
        expl_frame.pack(fill='x', pady=5)

        # Source
        source_frame, source_entry = create_input_field(main, "Source (where did you make this error?)", "",
                                                        COLORS['bg_card'])
        source_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_error():
            wrong = wrong_entry.get().strip()
            correct = correct_entry.get().strip()

            if not wrong or not correct:
                messagebox.showwarning("Warning", "Wrong and Correct forms are required!")
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

            db.add_error(
                language_id=language_id,
                category=cat_var.get(),
                wrong_form=wrong,
                correct_form=correct,
                explanation=expl_text.get("1.0", "end").strip(),
                source=source_entry.get().strip()
            )

            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Logged", "Error logged! You'll be reminded to review it. 💪")

        save_btn = create_rounded_button(btn_frame, "💾 Save Error", save_error, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        error_id = int(selected[0])
        self.show_detail_dialog(error_id)

    def show_detail_dialog(self, error_id):
        conn = db.get_connection()
        error = conn.execute("SELECT * FROM error_log WHERE id=?", (error_id,)).fetchone()
        conn.close()

        if not error:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Error Details")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        lang = db.get_language_by_id(error['language_id'])

        tk.Label(main, text="❌ Error Details", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        # Info
        info_items = [
            ("Language", f"{lang['icon']} {lang['name']}" if lang else "Unknown"),
            ("Category", error['category'] or 'N/A'),
            ("Wrong", error['wrong_form']),
            ("Correct", error['correct_form']),
            ("Explanation", error['explanation'] or 'N/A'),
            ("Source", error['source'] or 'N/A'),
            ("Frequency", str(error['frequency'])),
            ("Status", error['status']),
            ("Next Review", error['next_review'] or 'N/A'),
            ("Created", error['created_at'] or 'N/A'),
        ]

        for label, value in info_items:
            row = tk.Frame(main, bg=COLORS['bg_card'])
            row.pack(fill='x', pady=3)

            fg_color = COLORS['accent'] if label == "Wrong" else (
                COLORS['success'] if label == "Correct" else COLORS['text_primary'])

            tk.Label(row, text=f"{label}:", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     width=12, anchor='w').pack(side='left')
            tk.Label(row, text=value, font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=fg_color,
                     wraplength=350, anchor='w', justify='left').pack(side='left', fill='x')

        # Action buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def mark_resolved():
            conn = db.get_connection()
            conn.execute("UPDATE error_log SET status='Resolved' WHERE id=?", (error_id,))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.refresh_list()

        def increment_frequency():
            conn = db.get_connection()
            conn.execute("UPDATE error_log SET frequency=frequency+1 WHERE id=?", (error_id,))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Updated", "Frequency increased. Keep working on this! 💪")

        def delete_error():
            if messagebox.askyesno("Confirm", "Delete this error?"):
                conn = db.get_connection()
                conn.execute("DELETE FROM error_log WHERE id=?", (error_id,))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.refresh_list()

        resolve_btn = create_rounded_button(btn_frame, "✅ Resolved", mark_resolved, bg=COLORS['btn_success'])
        resolve_btn.pack(side='left', padx=(0, 8))

        freq_btn = create_rounded_button(btn_frame, "🔄 Made Again", increment_frequency, bg=COLORS['warning'])
        freq_btn.pack(side='left', padx=(0, 8))

        del_btn = create_rounded_button(btn_frame, "🗑️ Delete", delete_error, bg=COLORS['accent'])
        del_btn.pack(side='left', padx=(0, 8))

        close_btn = create_rounded_button(btn_frame, "Close", dialog.destroy, bg=COLORS['btn_secondary'])
        close_btn.pack(side='right')

    def show_context_menu(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        menu = tk.Menu(self.parent, tearoff=0, bg=COLORS['bg_card'],
                       fg=COLORS['text_primary'], font=FONTS['body'])
        menu.add_command(label="✏️ View Details", command=lambda: self.on_double_click(None))
        menu.add_command(label="✅ Mark Resolved", command=self.mark_selected_resolved)
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=self.delete_selected)

        menu.post(event.x_root, event.y_root)

    def mark_selected_resolved(self):
        selected = self.tree.selection()
        if not selected:
            return

        conn = db.get_connection()
        for item_id in selected:
            conn.execute("UPDATE error_log SET status='Resolved' WHERE id=?", (int(item_id),))
        conn.commit()
        conn.close()
        self.refresh_list()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm", f"Delete {len(selected)} error(s)?"):
            conn = db.get_connection()
            for item_id in selected:
                conn.execute("DELETE FROM error_log WHERE id=?", (int(item_id),))
            conn.commit()
            conn.close()
            self.refresh_list()