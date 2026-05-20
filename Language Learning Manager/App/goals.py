import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
from utils import (COLORS, FONTS, create_card, create_input_field,
                   create_dropdown, create_text_area, create_rounded_button,
                   create_progress_bar)


class GoalsPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="🎯 Goals", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        btn = create_rounded_button(header, "+ Add Goal", self.show_add_dialog)
        btn.pack(side='right')

        # Filter
        filter_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        filter_frame.pack(fill='x', pady=(0, 10))

        self.status_var = tk.StringVar(value="Active")
        status_options = ["Active", "Completed", "All"]

        tk.Label(filter_frame, text="Show:", font=FONTS['small_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')

        for opt in status_options:
            rb = tk.Radiobutton(filter_frame, text=opt, variable=self.status_var, value=opt,
                                bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['bg_card'], font=FONTS['body'],
                                activebackground=COLORS['bg_medium'],
                                activeforeground=COLORS['text_primary'],
                                command=self.refresh_goals)
            rb.pack(side='left', padx=8)

        # Goals display area
        self.goals_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        self.goals_frame.pack(fill='both', expand=True, pady=(0, 20))

        self.refresh_goals()

    def refresh_goals(self):
        for widget in self.goals_frame.winfo_children():
            widget.destroy()

        status_filter = self.status_var.get()

        if status_filter == "All":
            active_goals = db.get_goals(status='Active')
            completed_goals = db.get_goals(status='Completed')
            goals = list(active_goals) + list(completed_goals)
        else:
            goals = db.get_goals(status=status_filter)

        if not goals:
            empty = tk.Frame(self.goals_frame, bg=COLORS['bg_medium'])
            empty.pack(expand=True)
            tk.Label(empty, text="🎯", font=('Segoe UI Emoji', 48),
                     bg=COLORS['bg_medium']).pack(pady=(40, 10))
            tk.Label(empty, text="No goals yet!", font=FONTS['subtitle'],
                     bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack()
            tk.Label(empty, text="Set some goals to track your progress.",
                     font=FONTS['body'], bg=COLORS['bg_medium'],
                     fg=COLORS['text_secondary']).pack(pady=5)
            return

        # Create scrollable area
        canvas = tk.Canvas(self.goals_frame, bg=COLORS['bg_medium'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.goals_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=COLORS['bg_medium'])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Display goals as cards
        for goal in goals:
            self.create_goal_card(scrollable, goal)

    def create_goal_card(self, parent, goal):
        card = tk.Frame(parent, bg=COLORS['bg_card'], padx=20, pady=15,
                        highlightthickness=1, highlightbackground=COLORS['border'])
        card.pack(fill='x', pady=8, padx=5)

        # Header row
        header = tk.Frame(card, bg=COLORS['bg_card'])
        header.pack(fill='x')

        # Language icon
        lang = db.get_language_by_id(goal['language_id']) if goal['language_id'] else None
        lang_text = f"{lang['icon']} " if lang else "🌐 "

        # Goal type badge
        type_color = COLORS['info'] if goal['goal_type'] == 'Short-term' else COLORS['accent']
        type_text = f"[{goal['goal_type']}]"

        tk.Label(header, text=f"{lang_text}{goal['title']}", font=FONTS['heading'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(side='left')

        # Status
        status_color = COLORS['success'] if goal['status'] == 'Completed' else COLORS['warning']
        tk.Label(header, text=f"{type_text} • {goal['status']}", font=FONTS['small'],
                 bg=COLORS['bg_card'], fg=status_color).pack(side='right')

        # Description
        if goal['description']:
            tk.Label(card, text=goal['description'], font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     wraplength=600, anchor='w', justify='left').pack(anchor='w', pady=(5, 0))

        # Progress
        if goal['target_value'] > 0:
            progress_frame = tk.Frame(card, bg=COLORS['bg_card'])
            progress_frame.pack(fill='x', pady=(10, 5))

            percentage = min(100, int((goal['current_value'] / goal['target_value']) * 100))
            color = COLORS['success'] if percentage >= 100 else COLORS['accent']

            progress = create_progress_bar(progress_frame, goal['current_value'],
                                           goal['target_value'], color)
            progress.pack(fill='x')

            tk.Label(progress_frame,
                     text=f"{goal['current_value']} / {goal['target_value']} {goal['unit'] or ''} ({percentage}%)",
                     font=FONTS['small'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(anchor='e', pady=(3, 0))

        # Deadline
        if goal['deadline']:
            deadline_frame = tk.Frame(card, bg=COLORS['bg_card'])
            deadline_frame.pack(fill='x', pady=(5, 0))

            days_left = (datetime.strptime(goal['deadline'], "%Y-%m-%d") - datetime.now()).days
            if days_left < 0:
                deadline_text = f"⚠️ Overdue by {abs(days_left)} days!"
                deadline_color = COLORS['accent']
            elif days_left == 0:
                deadline_text = "⏰ Due today!"
                deadline_color = COLORS['warning']
            elif days_left <= 7:
                deadline_text = f"⏰ {days_left} days left"
                deadline_color = COLORS['warning']
            else:
                deadline_text = f"📅 Due: {goal['deadline']} ({days_left} days left)"
                deadline_color = COLORS['text_muted']

            tk.Label(deadline_frame, text=deadline_text, font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=deadline_color).pack(side='left')

        # Action buttons
        btn_frame = tk.Frame(card, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(10, 0))

        if goal['status'] == 'Active':
            update_btn = create_rounded_button(btn_frame, "📈 Update Progress",
                                               lambda g=goal: self.update_progress_dialog(g),
                                               bg=COLORS['info'])
            update_btn.pack(side='left', padx=(0, 8))

            complete_btn = create_rounded_button(btn_frame, "✅ Complete",
                                                 lambda g=goal: self.complete_goal(g),
                                                 bg=COLORS['btn_success'])
            complete_btn.pack(side='left', padx=(0, 8))

        del_btn = create_rounded_button(btn_frame, "🗑️", lambda g=goal: self.delete_goal(g),
                                        bg=COLORS['btn_secondary'])
        del_btn.pack(side='right')

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Goal")
        dialog.geometry("500x550")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=COLORS['bg_card'], padx=25, pady=20)
        main.pack(fill='both', expand=True)

        tk.Label(main, text="🎯 Set a New Goal", font=FONTS['subtitle'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 20))

        # Language (optional)
        languages = db.get_languages()
        lang_names = ["General"] + [l['name'] for l in languages]
        lang_frame, lang_var, _ = create_dropdown(main, "Language (optional)", lang_names, COLORS['bg_card'])
        lang_frame.pack(fill='x', pady=5)

        # Title
        title_frame, title_entry = create_input_field(main, "Goal Title *", "", COLORS['bg_card'])
        title_frame.pack(fill='x', pady=5)

        # Description
        desc_frame, desc_text = create_text_area(main, "Description", 2, COLORS['bg_card'])
        desc_frame.pack(fill='x', pady=5)

        # Type
        type_options = ["Short-term", "Long-term"]
        type_frame, type_var, _ = create_dropdown(main, "Goal Type", type_options, COLORS['bg_card'])
        type_frame.pack(fill='x', pady=5)

        # Target value
        target_frame, target_entry = create_input_field(main, "Target Value (e.g., 100)", "", COLORS['bg_card'])
        target_frame.pack(fill='x', pady=5)

        # Unit
        unit_frame, unit_entry = create_input_field(main, "Unit (e.g., words, hours, lessons)", "", COLORS['bg_card'])
        unit_frame.pack(fill='x', pady=5)

        # Deadline
        deadline_frame, deadline_entry = create_input_field(main, "Deadline (YYYY-MM-DD)", "", COLORS['bg_card'])
        deadline_frame.pack(fill='x', pady=5)

        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(20, 0))

        def save_goal():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Goal title is required!")
                return

            lang_name = lang_var.get()
            language_id = None
            if lang_name != "General":
                for l in languages:
                    if l['name'] == lang_name:
                        language_id = l['id']
                        break

            try:
                target = int(target_entry.get().strip()) if target_entry.get().strip() else 0
            except ValueError:
                target = 0

            deadline = deadline_entry.get().strip() if deadline_entry.get().strip() else None

            db.add_goal(
                language_id=language_id,
                title=title,
                description=desc_text.get("1.0", "end").strip(),
                goal_type=type_var.get(),
                target_value=target,
                unit=unit_entry.get().strip(),
                deadline=deadline
            )

            dialog.destroy()
            self.refresh_goals()
            messagebox.showinfo("Success", f"Goal '{title}' created! 🎯")

        save_btn = create_rounded_button(btn_frame, "💾 Save Goal", save_goal, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def update_progress_dialog(self, goal):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Update Progress")
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

        tk.Label(main, text=f"📈 Update: {goal['title']}", font=FONTS['heading'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))

        tk.Label(main, text=f"Current: {goal['current_value']} / {goal['target_value']} {goal['unit'] or ''}",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))

        value_frame, value_entry = create_input_field(main, "New Current Value", "", COLORS['bg_card'])
        value_frame.pack(fill='x', pady=5)
        value_entry.insert(0, str(goal['current_value']))

        btn_frame = tk.Frame(main, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        def save_progress():
            try:
                new_value = int(value_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Warning", "Please enter a valid number!")
                return

            db.update_goal_progress(goal['id'], new_value)
            dialog.destroy()
            self.refresh_goals()

        save_btn = create_rounded_button(btn_frame, "💾 Save", save_progress, bg=COLORS['btn_success'])
        save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = create_rounded_button(btn_frame, "Cancel", dialog.destroy, bg=COLORS['btn_secondary'])
        cancel_btn.pack(side='left')

    def complete_goal(self, goal):
        if messagebox.askyesno("Complete Goal", f"Mark '{goal['title']}' as completed?"):
            conn = db.get_connection()
            conn.execute("UPDATE goals SET status='Completed', current_value=target_value WHERE id=?",
                         (goal['id'],))
            conn.commit()
            conn.close()
            self.refresh_goals()
            messagebox.showinfo("🎉 Congratulations!", f"Goal '{goal['title']}' completed!")

    def delete_goal(self, goal):
        if messagebox.askyesno("Confirm", f"Delete goal '{goal['title']}'?"):
            conn = db.get_connection()
            conn.execute("DELETE FROM goals WHERE id=?", (goal['id'],))
            conn.commit()
            conn.close()
            self.refresh_goals()