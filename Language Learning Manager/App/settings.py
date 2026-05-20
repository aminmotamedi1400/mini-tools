import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from datetime import datetime
import json
import os
import database as db
from utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button)


class SettingsPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="⚙️ Settings", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        # Scrollable content
        canvas = tk.Canvas(self.parent, bg=COLORS['bg_medium'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        self.main = tk.Frame(canvas, bg=COLORS['bg_medium'], padx=30, pady=10)

        self.main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.main, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Sections
        self.build_languages_section()
        self.build_resources_section()
        self.build_data_section()
        self.build_about_section()

    def build_languages_section(self):
        card = create_card(self.main, "🌐 Languages")
        card.pack(fill='x', pady=10)

        languages = db.get_languages()

        for lang in languages:
            lang_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=8)
            lang_frame.pack(fill='x')

            # Language info
            info_frame = tk.Frame(lang_frame, bg=COLORS['bg_card'])
            info_frame.pack(fill='x')

            color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']

            tk.Label(info_frame, text=f"{lang['icon']} {lang['name']}",
                     font=FONTS['heading'], bg=COLORS['bg_card'], fg=color).pack(side='left')

            tk.Label(info_frame, text=f"Level: {lang['level']}",
                     font=FONTS['small'], bg=COLORS['bg_card'],
                     fg=COLORS['text_secondary']).pack(side='right')

            # Edit button
            edit_btn = create_rounded_button(lang_frame, "✏️ Edit",
                                             lambda l=lang: self.edit_language_dialog(l),
                                             bg=COLORS['btn_secondary'])
            edit_btn.pack(anchor='w', pady=(5, 0))

            tk.Frame(lang_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=(8, 0))

        # Add language button
        add_btn = create_rounded_button(card, "+ Add Language", self.add_language_dialog,
                                        bg=COLORS['btn_primary'])
        add_btn.pack(anchor='w', pady=(10, 0))

    def build_resources_section(self):
        card = create_card(self.main, "📚 Resources / Books")
        card.pack(fill='x', pady=10)

        resources = db.get_resources()

        for res in resources:
            res_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=5)
            res_frame.pack(fill='x')

            lang = db.get_language_by_id(res['language_id'])
            lang_icon = lang['icon'] if lang else '🌐'
            color = COLORS['english'] if lang and lang['name'] == 'English' else COLORS['german']

            info = tk.Frame(res_frame, bg=COLORS['bg_card'])
            info.pack(fill='x')

            tk.Label(info, text=f"{lang_icon} {res['name']}", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(side='left')

            progress_text = f"{res['completed_units']}/{res['total_units']} units"
            tk.Label(info, text=progress_text, font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='right')

            # Progress update
            prog_frame = tk.Frame(res_frame, bg=COLORS['bg_card'])
            prog_frame.pack(fill='x', pady=(3, 0))

            if res['total_units'] > 0:
                pct = int((res['completed_units'] / res['total_units']) * 100)
                from utils import create_progress_bar
                bar = create_progress_bar(prog_frame, res['completed_units'],
                                          res['total_units'], color)
                bar.pack(fill='x')

            # Quick update
            quick_frame = tk.Frame(res_frame, bg=COLORS['bg_card'])
            quick_frame.pack(fill='x', pady=(5, 0))

            update_btn = create_rounded_button(quick_frame, "📈 Update Progress",
                                               lambda r=res: self.update_resource_dialog(r),
                                               bg=COLORS['btn_secondary'])
            update_btn.pack(side='left')

            tk.Frame(res_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=(8, 0))

        # Add resource
        add_btn = create_rounded_button(card, "+ Add Resource", self.add_resource_dialog,
                                        bg=COLORS['btn_primary'])
        add_btn.pack(anchor='w', pady=(10, 0))

    def build_data_section(self):
        card = create_card(self.main, "💾 Data Management")
        card.pack(fill='x', pady=10)

        # Export
        export_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=5)
        export_frame.pack(fill='x')

        tk.Label(export_frame, text="Export your data as JSON for backup or transfer.",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 8))

        btn_row = tk.Frame(export_frame, bg=COLORS['bg_card'])
        btn_row.pack(fill='x')

        export_btn = create_rounded_button(btn_row, "📤 Export Data", self.export_data,
                                           bg=COLORS['info'])
        export_btn.pack(side='left', padx=(0, 10))

        import_btn = create_rounded_button(btn_row, "📥 Import Data", self.import_data,
                                           bg=COLORS['warning'])
        import_btn.pack(side='left', padx=(0, 10))

        tk.Frame(card, bg=COLORS['border'], height=1).pack(fill='x', pady=10)

        # Reset
        reset_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=5)
        reset_frame.pack(fill='x')

        tk.Label(reset_frame, text="⚠️ Danger Zone", font=FONTS['heading'],
                 bg=COLORS['bg_card'], fg=COLORS['accent']).pack(anchor='w', pady=(0, 5))

        tk.Label(reset_frame, text="Reset all data. This action cannot be undone!",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_muted']).pack(anchor='w', pady=(0, 8))

        reset_btn = create_rounded_button(reset_frame, "🗑️ Reset All Data", self.reset_data,
                                          bg=COLORS['accent'])
        reset_btn.pack(anchor='w')

    def build_about_section(self):
        card = create_card(self.main, "ℹ️ About")
        card.pack(fill='x', pady=10)

        about_text = """Language Learning Manager v1.0.0

A comprehensive tool for managing your language learning journey.
Track vocabulary, grammar, study sessions, and more!

Features:
• Multi-language support (English, German, and more)
• Spaced repetition for vocabulary review
• Grammar tracking with mastery levels
• Error logging to learn from mistakes
• Goal setting and progress tracking
• Detailed reports and statistics
• Activity heatmap

Built with Python & Tkinter
Made with ❤️ for language learners"""

        tk.Label(card, text=about_text, font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                 justify='left', anchor='w').pack(anchor='w')

    def edit_language_dialog(self, lang):
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit {lang['name']}")
        dialog.geometry("400x350")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 175
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text=f"✏️ Edit {lang['name']}", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        # Name
        name_frame, name_entry = create_input_field(main, "Language Name", "", COLORS['bg_card'])
        name_frame.pack(fill='x', pady=5)
        name_entry.insert(0, lang['name'])

        # Icon
        icon_frame, icon_entry = create_input_field(main, "Icon (emoji)", "", COLORS['bg_card'])
        icon_frame.pack(fill='x', pady=5)
        icon_entry.insert(0, lang['icon'])

        # Level
        levels = ["Beginner", "Elementary", "Intermediate", "Upper-Intermediate", "Advanced"]
        level_frame, level_var, _ = create_dropdown(main, "Level", levels, COLORS['bg_card'])
        level_frame.pack(fill='x', pady=5)
        level_var.set(lang['level'])

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save():
            conn = db.get_connection()
            conn.execute("UPDATE languages SET name=?, icon=?, level=? WHERE id=?",
                         (name_entry.get().strip(), icon_entry.get().strip(),
                          level_var.get(), lang['id']))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.app.show_page("settings") if hasattr(self.app, 'show_page') else None
            messagebox.showinfo("Updated", "Language updated!")

        save_btn = create_rounded_button(btn_frame, "💾 Save", save, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def add_language_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Language")
        dialog.geometry("400x350")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 175
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text="🌐 Add New Language", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        # Name
        name_frame, name_entry = create_input_field(main, "Language Name *", "", COLORS['bg_card'])
        name_frame.pack(fill='x', pady=5)

        # Icon
        icon_frame, icon_entry = create_input_field(main, "Icon (emoji, e.g., 🇫🇷)", "", COLORS['bg_card'])
        icon_frame.pack(fill='x', pady=5)

        # Level
        levels = ["Beginner", "Elementary", "Intermediate", "Upper-Intermediate", "Advanced"]
        level_frame, level_var, _ = create_dropdown(main, "Level", levels, COLORS['bg_card'])
        level_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Language name is required!")
                return

            icon = icon_entry.get().strip() or '🌐'

            conn = db.get_connection()
            try:
                conn.execute("INSERT INTO languages (name, icon, level) VALUES (?, ?, ?)",
                             (name, icon, level_var.get()))
                conn.commit()
                dialog.destroy()
                messagebox.showinfo("Success", f"Language '{name}' added!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not add language: {e}")
            finally:
                conn.close()

        save_btn = create_rounded_button(btn_frame, "💾 Save", save, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def add_resource_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Resource")
        dialog.geometry("450x400")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text="📚 Add New Resource", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        # Language
        languages = db.get_languages()
        lang_names = [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language *", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Name
        name_frame, name_entry = create_input_field(main, "Resource Name *", "", COLORS['bg_card'])
        name_frame.pack(fill='x', pady=5)

        # Type
        types = ["Book", "Course", "App", "Video Series", "Podcast", "Website", "Other"]
        type_frame, type_var, _ = create_dropdown(main, "Type", types, COLORS['bg_card'])
        type_frame.pack(fill='x', pady=5)

        # Total units
        units_frame, units_entry = create_input_field(main, "Total Units/Chapters", "12", COLORS['bg_card'])
        units_frame.pack(fill='x', pady=5)
        units_entry.delete(0, 'end')
        units_entry.insert(0, "12")

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Resource name is required!")
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

            try:
                total_units = int(units_entry.get().strip())
            except ValueError:
                total_units = 0

            conn = db.get_connection()
            conn.execute("""
                INSERT INTO resources (language_id, name, type, total_units, status)
                VALUES (?, ?, ?, ?, 'Not Started')
            """, (language_id, name, type_var.get(), total_units))
            conn.commit()
            conn.close()

            dialog.destroy()
            messagebox.showinfo("Success", f"Resource '{name}' added!")

        save_btn = create_rounded_button(btn_frame, "💾 Save", save, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def update_resource_dialog(self, resource):
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Update: {resource['name']}")
        dialog.geometry("400x250")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 125
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text=f"📈 {resource['name']}", font=FONTS['heading'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 10))

        tk.Label(main,
                 text=f"Current: {resource['completed_units']} / {resource['total_units']} units completed",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))

        units_frame, units_entry = create_input_field(main, "Completed Units", "", COLORS['bg_card'])
        units_frame.pack(fill='x', pady=5)
        units_entry.insert(0, str(resource['completed_units']))

        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        def save():
            try:
                completed = int(units_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Warning", "Please enter a valid number!")
                return

            db.update_resource_progress(resource['id'], completed)

            # Update status
            conn = db.get_connection()
            if completed >= resource['total_units']:
                conn.execute("UPDATE resources SET status='Completed' WHERE id=?", (resource['id'],))
            elif completed > 0:
                conn.execute("UPDATE resources SET status='In Progress' WHERE id=?", (resource['id'],))
            conn.commit()
            conn.close()

            dialog.destroy()
            messagebox.showinfo("Updated", "Resource progress updated!")

        save_btn = create_rounded_button(btn_frame, "💾 Save", save, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def export_data(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"language_data_backup_{datetime.now().strftime('%Y%m%d')}.json"
        )

        if not filepath:
            return

        conn = db.get_connection()

        data = {
            'export_date': datetime.now().isoformat(),
            'version': '1.0.0',
            'languages': [dict(row) for row in conn.execute("SELECT * FROM languages").fetchall()],
            'resources': [dict(row) for row in conn.execute("SELECT * FROM resources").fetchall()],
            'vocabulary': [dict(row) for row in conn.execute("SELECT * FROM vocabulary").fetchall()],
            'grammar_topics': [dict(row) for row in conn.execute("SELECT * FROM grammar_topics").fetchall()],
            'study_sessions': [dict(row) for row in conn.execute("SELECT * FROM study_sessions").fetchall()],
            'error_log': [dict(row) for row in conn.execute("SELECT * FROM error_log").fetchall()],
            'goals': [dict(row) for row in conn.execute("SELECT * FROM goals").fetchall()],
            'sentences': [dict(row) for row in conn.execute("SELECT * FROM sentences").fetchall()],
            'notes': [dict(row) for row in conn.execute("SELECT * FROM notes").fetchall()],
        }

        conn.close()

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def import_data(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )

        if not filepath:
            return

        if not messagebox.askyesno("Confirm Import",
                                   "This will ADD imported data to your existing data.\n"
                                   "Duplicates may occur. Continue?"):
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            conn = db.get_connection()

            # Import vocabulary
            for word in data.get('vocabulary', []):
                try:
                    conn.execute("""
                        INSERT INTO vocabulary (language_id, word, meaning, article, plural,
                        pronunciation, part_of_speech, example_sentence, collocations, tags,
                        difficulty, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (word.get('language_id', 1), word.get('word', ''),
                          word.get('meaning', ''), word.get('article', ''),
                          word.get('plural', ''), word.get('pronunciation', ''),
                          word.get('part_of_speech', ''), word.get('example_sentence', ''),
                          word.get('collocations', ''), word.get('tags', ''),
                          word.get('difficulty', 3), word.get('status', 'New')))
                except:
                    pass

            # Import grammar
            for topic in data.get('grammar_topics', []):
                try:
                    conn.execute("""
                        INSERT INTO grammar_topics (language_id, title, category, explanation,
                        examples, rules, resource, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (topic.get('language_id', 1), topic.get('title', ''),
                          topic.get('category', ''), topic.get('explanation', ''),
                          topic.get('examples', ''), topic.get('rules', ''),
                          topic.get('resource', ''), topic.get('notes', '')))
                except:
                    pass

            # Import errors
            for error in data.get('error_log', []):
                try:
                    conn.execute("""
                        INSERT INTO error_log (language_id, category, wrong_form, correct_form,
                        explanation, source) VALUES (?, ?, ?, ?, ?, ?)
                    """, (error.get('language_id', 1), error.get('category', ''),
                          error.get('wrong_form', ''), error.get('correct_form', ''),
                          error.get('explanation', ''), error.get('source', '')))
                except:
                    pass

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Data imported successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def reset_data(self):
        if not messagebox.askyesno("⚠️ WARNING",
                                   "Are you SURE you want to delete ALL data?\n"
                                   "This cannot be undone!\n\n"
                                   "Consider exporting your data first."):
            return

        if not messagebox.askyesno("⚠️ FINAL WARNING",
                                   "This will permanently delete:\n"
                                   "• All vocabulary\n"
                                   "• All study sessions\n"
                                   "• All grammar topics\n"
                                   "• All errors\n"
                                   "• All goals\n"
                                   "• All notes\n\n"
                                   "Are you absolutely sure?"):
            return

        conn = db.get_connection()
        tables = ['vocabulary', 'study_sessions', 'grammar_topics',
                  'error_log', 'goals', 'sentences', 'notes', 'daily_checklist']
        for table in tables:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()

        messagebox.showinfo("Done", "All data has been reset.")