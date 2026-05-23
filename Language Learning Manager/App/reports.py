import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import App.database as db
from App.utils import (COLORS, FONTS, create_card, create_rounded_button,
                   create_progress_bar, format_duration, create_scrollable_frame)


class ReportsPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="📈 Reports & Statistics", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        # Time range selector
        range_frame = tk.Frame(header, bg=COLORS['bg_medium'])
        range_frame.pack(side='right')

        self.range_var = tk.StringVar(value="30")
        ranges = [("7 Days", "7"), ("30 Days", "30"), ("90 Days", "90"), ("All Time", "all")]
        for text, value in ranges:
            rb = tk.Radiobutton(range_frame, text=text, variable=self.range_var, value=value,
                                bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['bg_card'], font=FONTS['small'],
                                activebackground=COLORS['bg_medium'],
                                activeforeground=COLORS['text_primary'],
                                command=self.refresh_reports)
            rb.pack(side='left', padx=5)

        # Scrollable content
        container, self.scroll_frame, self.canvas = create_scrollable_frame(self.parent)
        container.pack(fill='both', expand=True)

        self.refresh_reports()

    def get_date_from(self):
        range_val = self.range_var.get()
        if range_val == "all":
            return "2000-01-01"
        return (datetime.now() - timedelta(days=int(range_val))).strftime("%Y-%m-%d")

    def refresh_reports(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        main = self.scroll_frame
        main.config(padx=30, pady=10)

        date_from = self.get_date_from()

        self.build_overview(main, date_from)
        self.build_language_comparison(main, date_from)
        self.build_activity_heatmap(main, date_from)
        self.build_vocabulary_breakdown(main)
        self.build_grammar_progress(main)
        self.build_skill_distribution(main, date_from)
        self.build_error_analysis(main)
        self.build_goals_summary(main)

    def build_overview(self, parent, date_from):
        card = create_card(parent, "📊 Overview")
        card.pack(fill='x', pady=10)

        conn = db.get_connection()

        total_sessions = conn.execute(
            "SELECT COUNT(*) FROM study_sessions WHERE date >= ?", (date_from,)).fetchone()[0]
        total_time = conn.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE date >= ?",
            (date_from,)).fetchone()[0]

        range_val = self.range_var.get()
        days = int(range_val) if range_val != "all" else max(1, (
                datetime.now() - datetime(2000, 1, 1)).days)
        avg_per_day = total_time / max(1, days)

        new_words = conn.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE created_at >= ?", (date_from,)).fetchone()[0]
        mastered_words = conn.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE status='Mastered'").fetchone()[0]
        total_vocab = conn.execute(
            "SELECT COUNT(*) FROM vocabulary").fetchone()[0]
        errors_logged = conn.execute(
            "SELECT COUNT(*) FROM error_log WHERE created_at >= ?", (date_from,)).fetchone()[0]
        grammar_topics = conn.execute(
            "SELECT COUNT(*) FROM grammar_topics").fetchone()[0]

        conn.close()

        streak = db.get_streak()

        # Stats grid
        stats_grid = tk.Frame(card, bg=COLORS['bg_card'])
        stats_grid.pack(fill='x', pady=5)

        stats = [
            ("📚", str(total_sessions), "Sessions", COLORS['info']),
            ("⏱️", format_duration(total_time), "Total Time", COLORS['success']),
            ("📅", f"{avg_per_day:.0f} min", "Avg / Day", COLORS['warning']),
            ("🔥", str(streak), "Day Streak", COLORS['accent']),
            ("📝", str(new_words), "New Words", COLORS['info']),
            ("✅", str(mastered_words), "Mastered", COLORS['success']),
            ("📐", str(grammar_topics), "Grammar", COLORS['warning']),
            ("❌", str(errors_logged), "Errors", COLORS['accent']),
        ]

        for i, (icon, value, label, color) in enumerate(stats):
            row = i // 4
            col = i % 4

            cell = tk.Frame(stats_grid, bg=COLORS['bg_card'], padx=15, pady=10)
            cell.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

            tk.Label(cell, text=icon, font=('Segoe UI Emoji', 18),
                     bg=COLORS['bg_card'], fg=color).pack()
            tk.Label(cell, text=value, font=('Segoe UI', 20, 'bold'),
                     bg=COLORS['bg_card'], fg=color).pack()
            tk.Label(cell, text=label, font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()

        for i in range(4):
            stats_grid.columnconfigure(i, weight=1)

    def build_language_comparison(self, parent, date_from):
        card = create_card(parent, "🌐 Language Comparison")
        card.pack(fill='x', pady=10)

        languages = db.get_languages()
        conn = db.get_connection()

        for lang in languages:
            lang_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=10)
            lang_frame.pack(fill='x')

            color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']

            # Language header
            header = tk.Frame(lang_frame, bg=COLORS['bg_card'])
            header.pack(fill='x')

            tk.Label(header, text=f"{lang['icon']} {lang['name']}",
                     font=FONTS['heading'], bg=COLORS['bg_card'], fg=color).pack(side='left')

            # Stats for this language
            sessions = conn.execute(
                "SELECT COUNT(*) FROM study_sessions WHERE language_id=? AND date >= ?",
                (lang['id'], date_from)).fetchone()[0]
            time_spent = conn.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE language_id=? AND date >= ?",
                (lang['id'], date_from)).fetchone()[0]
            vocab_count = conn.execute(
                "SELECT COUNT(*) FROM vocabulary WHERE language_id=?", (lang['id'],)).fetchone()[0]
            vocab_mastered = conn.execute(
                "SELECT COUNT(*) FROM vocabulary WHERE language_id=? AND status='Mastered'",
                (lang['id'],)).fetchone()[0]

            tk.Label(header, text=f"{sessions} sessions • {format_duration(time_spent)} • {vocab_count} words",
                     font=FONTS['small'], bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='right')

            # Progress bars
            if vocab_count > 0:
                mastery_pct = int((vocab_mastered / vocab_count) * 100)
            else:
                mastery_pct = 0

            progress_frame = tk.Frame(lang_frame, bg=COLORS['bg_card'])
            progress_frame.pack(fill='x', pady=(5, 0))

            tk.Label(progress_frame, text=f"Vocabulary Mastery: {mastery_pct}%",
                     font=FONTS['small'], bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')

            bar = create_progress_bar(progress_frame, vocab_mastered, max(1, vocab_count), color)
            bar.pack(fill='x', pady=(3, 0))

            # Separator
            tk.Frame(lang_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=(10, 0))

        conn.close()

    def build_activity_heatmap(self, parent, date_from):
        card = create_card(parent, "📅 Activity (Last 30 Days)")
        card.pack(fill='x', pady=10)

        activity = db.get_monthly_activity()
        activity_dict = {}
        for row in activity:
            activity_dict[row['date']] = row['total_time']

        # Build text-based heatmap
        heatmap_frame = tk.Frame(card, bg=COLORS['bg_card'])
        heatmap_frame.pack(fill='x', pady=5)

        # Day labels
        days_label = tk.Frame(heatmap_frame, bg=COLORS['bg_card'])
        days_label.pack(fill='x')

        today = datetime.now().date()

        # Show last 30 days
        for i in range(30):
            day = today - timedelta(days=29 - i)
            day_str = day.strftime("%Y-%m-%d")
            minutes = activity_dict.get(day_str, 0)

            # Color based on intensity
            if minutes == 0:
                color = COLORS['bg_medium']
            elif minutes < 20:
                color = '#1a4a3a'
            elif minutes < 40:
                color = '#1e6e4e'
            elif minutes < 60:
                color = '#22926a'
            elif minutes < 90:
                color = '#27ae60'
            else:
                color = '#2ecc71'

            cell = tk.Frame(days_label, bg=color, width=22, height=22,
                            highlightthickness=1, highlightbackground=COLORS['border'])
            cell.pack(side='left', padx=1, pady=1)
            cell.pack_propagate(False)

            # Tooltip on hover
            tooltip_text = f"{day_str}: {minutes} min" if minutes > 0 else f"{day_str}: No study"

            def make_enter(widget, text):
                def on_enter(e):
                    widget._tooltip = tk.Toplevel()
                    widget._tooltip.wm_overrideredirect(True)
                    widget._tooltip.wm_geometry(f"+{e.x_root+10}+{e.y_root+10}")
                    lbl = tk.Label(widget._tooltip, text=text, bg=COLORS['bg_card'],
                                   fg=COLORS['text_primary'], font=FONTS['small'],
                                   padx=8, pady=4, relief='solid', borderwidth=1)
                    lbl.pack()
                return on_enter

            def make_leave(widget):
                def on_leave(e):
                    if hasattr(widget, '_tooltip'):
                        widget._tooltip.destroy()
                return on_leave

            cell.bind('<Enter>', make_enter(cell, tooltip_text))
            cell.bind('<Leave>', make_leave(cell))

        # Legend
        legend_frame = tk.Frame(card, bg=COLORS['bg_card'])
        legend_frame.pack(fill='x', pady=(10, 0))

        tk.Label(legend_frame, text="Less", font=FONTS['small'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side='left')

        for color in [COLORS['bg_medium'], '#1a4a3a', '#1e6e4e', '#22926a', '#27ae60', '#2ecc71']:
            cell = tk.Frame(legend_frame, bg=color, width=14, height=14,
                            highlightthickness=1, highlightbackground=COLORS['border'])
            cell.pack(side='left', padx=1)
            cell.pack_propagate(False)

        tk.Label(legend_frame, text="More", font=FONTS['small'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side='left', padx=(5, 0))

    def build_vocabulary_breakdown(self, parent):
        card = create_card(parent, "📝 Vocabulary Breakdown")
        card.pack(fill='x', pady=10)

        languages = db.get_languages()

        for lang in languages:
            lang_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=8)
            lang_frame.pack(fill='x')

            color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']
            stats = db.get_vocabulary_stats(lang['id'])

            tk.Label(lang_frame, text=f"{lang['icon']} {lang['name']} ({stats['total']} words)",
                     font=FONTS['body_bold'], bg=COLORS['bg_card'], fg=color).pack(anchor='w')

            # Status breakdown
            breakdown_frame = tk.Frame(lang_frame, bg=COLORS['bg_card'])
            breakdown_frame.pack(fill='x', pady=(5, 0))

            statuses = [
                ("New", stats.get('new', 0), COLORS['info']),
                ("Learning", stats.get('learning', 0), COLORS['warning']),
                ("Reviewing", stats.get('reviewing', 0), COLORS['accent']),
                ("Mastered", stats.get('mastered', 0), COLORS['success']),
            ]

            total = max(1, stats['total'])

            for status_name, count, s_color in statuses:
                pct = int((count / total) * 100)
                row = tk.Frame(breakdown_frame, bg=COLORS['bg_card'])
                row.pack(fill='x', pady=2)

                tk.Label(row, text=f"{status_name}: {count} ({pct}%)", font=FONTS['small'],
                         bg=COLORS['bg_card'], fg=COLORS['text_secondary'], width=25, anchor='w').pack(side='left')

                bar_bg = tk.Frame(row, bg=COLORS['progress_bg'], height=10)
                bar_bg.pack(side='left', fill='x', expand=True)

                bar_width = max(1, pct)
                bar_fill = tk.Frame(bar_bg, bg=s_color, width=bar_width * 3, height=10)
                bar_fill.place(x=0, y=0)

    def build_grammar_progress(self, parent):
        card = create_card(parent, "📐 Grammar Progress")
        card.pack(fill='x', pady=10)

        topics = db.get_grammar_topics()

        if not topics:
            tk.Label(card, text="No grammar topics tracked yet.",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=10)
            return

        # Summary
        total = len(topics)
        solid = sum(1 for t in topics if t['status'] == 'Solid')
        learning = sum(1 for t in topics if t['status'] in ['Learning', 'Practicing'])
        avg_mastery = sum(t['mastery_percent'] for t in topics) / max(1, total)

        summary_frame = tk.Frame(card, bg=COLORS['bg_card'])
        summary_frame.pack(fill='x', pady=5)

        tk.Label(summary_frame, text=f"Total: {total}  |  Solid: {solid}  |  "
                                     f"Learning: {learning}  |  Avg Mastery: {avg_mastery:.0f}%",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w')

        # Top topics needing work
        weak_topics = sorted(topics, key=lambda t: t['mastery_percent'])[:5]

        if weak_topics:
            tk.Label(card, text="⚠️ Topics Needing Attention:", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['warning']).pack(anchor='w', pady=(10, 5))

            for topic in weak_topics:
                lang = db.get_language_by_id(topic['language_id'])
                topic_frame = tk.Frame(card, bg=COLORS['bg_card'])
                topic_frame.pack(fill='x', pady=2)

                tk.Label(topic_frame,
                         text=f"  {lang['icon'] if lang else '🌐'} {topic['title']} — {topic['mastery_percent']}%",
                         font=FONTS['small'], bg=COLORS['bg_card'],
                         fg=COLORS['text_secondary']).pack(side='left')

                mini_bar = create_progress_bar(topic_frame, topic['mastery_percent'], 100, COLORS['warning'])
                mini_bar.pack(side='right', fill='x', expand=True, padx=(10, 0))

    def build_skill_distribution(self, parent, date_from):
        card = create_card(parent, "🎯 Skills Practiced")
        card.pack(fill='x', pady=10)

        conn = db.get_connection()
        sessions = conn.execute(
            "SELECT skills FROM study_sessions WHERE date >= ? AND skills IS NOT NULL AND skills != ''",
            (date_from,)).fetchall()
        conn.close()

        skill_counts = {}
        for session in sessions:
            if session['skills']:
                for skill in session['skills'].split(','):
                    skill = skill.strip()
                    if skill:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1

        if not skill_counts:
            tk.Label(card, text="No skill data yet. Log study sessions with skills!",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=10)
            return

        max_count = max(skill_counts.values())

        skill_colors = {
            'Reading': COLORS['info'],
            'Listening': COLORS['success'],
            'Writing': COLORS['warning'],
            'Speaking': COLORS['accent'],
            'Grammar': '#9b59b6',
            'Vocabulary': '#1abc9c',
        }

        for skill, count in sorted(skill_counts.items(), key=lambda x: -x[1]):
            skill_frame = tk.Frame(card, bg=COLORS['bg_card'])
            skill_frame.pack(fill='x', pady=3)

            color = skill_colors.get(skill, COLORS['text_secondary'])

            tk.Label(skill_frame, text=f"{skill} ({count}x)", font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=color, width=20, anchor='w').pack(side='left')

            # Bar
            bar_container = tk.Frame(skill_frame, bg=COLORS['progress_bg'], height=16)
            bar_container.pack(side='left', fill='x', expand=True, padx=(10, 0))
            bar_container.pack_propagate(False)

            bar_width_pct = (count / max_count) * 100
            bar = tk.Frame(bar_container, bg=color)
            bar.place(relx=0, rely=0, relwidth=bar_width_pct / 100, relheight=1.0)

    def build_error_analysis(self, parent):
        card = create_card(parent, "❌ Error Analysis")
        card.pack(fill='x', pady=10)

        errors = db.get_errors()

        if not errors:
            tk.Label(card, text="No errors logged yet. Great... or maybe start logging them! 😄",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=10)
            return

        # Category breakdown
        categories = {}
        for error in errors:
            cat = error['category'] or 'Other'
            categories[cat] = categories.get(cat, 0) + 1

        total_errors = len(errors)
        active_errors = sum(1 for e in errors if e['status'] == 'Active')
        resolved_errors = sum(1 for e in errors if e['status'] == 'Resolved')

        # Summary
        tk.Label(card, text=f"Total: {total_errors}  |  Active: {active_errors}  |  Resolved: {resolved_errors}",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))

        # Category bars
        max_cat = max(categories.values()) if categories else 1

        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            cat_frame = tk.Frame(card, bg=COLORS['bg_card'])
            cat_frame.pack(fill='x', pady=2)

            tk.Label(cat_frame, text=f"{cat} ({count})", font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                     width=20, anchor='w').pack(side='left')

            bar_container = tk.Frame(cat_frame, bg=COLORS['progress_bg'], height=12)
            bar_container.pack(side='left', fill='x', expand=True, padx=(10, 0))
            bar_container.pack_propagate(False)

            bar_pct = count / max_cat
            bar = tk.Frame(bar_container, bg=COLORS['accent'])
            bar.place(relx=0, rely=0, relwidth=bar_pct, relheight=1.0)

        # Most frequent errors
        frequent = sorted(errors, key=lambda e: e['frequency'], reverse=True)[:5]
        if frequent and frequent[0]['frequency'] > 1:
            tk.Label(card, text="\n🔄 Most Repeated Errors:", font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=COLORS['warning']).pack(anchor='w', pady=(10, 5))

            for err in frequent:
                if err['frequency'] > 1:
                    tk.Label(card,
                             text=f"  • {err['wrong_form']} → {err['correct_form']} (×{err['frequency']})",
                             font=FONTS['small'], bg=COLORS['bg_card'],
                             fg=COLORS['text_secondary']).pack(anchor='w', pady=1)

    def build_goals_summary(self, parent):
        card = create_card(parent, "🎯 Goals Progress")
        card.pack(fill='x', pady=10)

        active_goals = db.get_goals(status='Active')
        completed_goals = db.get_goals(status='Completed')

        tk.Label(card, text=f"Active: {len(active_goals)}  |  Completed: {len(completed_goals)}",
                 font=FONTS['body'], bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))

        if not active_goals:
            tk.Label(card, text="No active goals. Set some goals to track progress!",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=5)
            return

        for goal in active_goals:
            goal_frame = tk.Frame(card, bg=COLORS['bg_card'])
            goal_frame.pack(fill='x', pady=5)

            lang = db.get_language_by_id(goal['language_id']) if goal['language_id'] else None
            lang_icon = lang['icon'] if lang else "🌐"

            tk.Label(goal_frame, text=f"{lang_icon} {goal['title']}",
                     font=FONTS['body_bold'], bg=COLORS['bg_card'],
                     fg=COLORS['text_primary']).pack(anchor='w')

            if goal['target_value'] > 0:
                pct = min(100, int((goal['current_value'] / goal['target_value']) * 100))
                progress = create_progress_bar(goal_frame, goal['current_value'],
                                               goal['target_value'], COLORS['accent'])
                progress.pack(fill='x', pady=(3, 0))

                tk.Label(goal_frame,
                         text=f"{goal['current_value']}/{goal['target_value']} {goal['unit'] or ''} ({pct}%)",
                         font=FONTS['small'], bg=COLORS['bg_card'],
                         fg=COLORS['text_muted']).pack(anchor='e')