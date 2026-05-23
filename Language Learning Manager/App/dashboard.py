import tkinter as tk
from tkinter import ttk
from datetime import datetime
import App.database as db
from App.utils import (COLORS, FONTS, create_stat_card, create_card,
                   create_progress_bar, format_duration, create_scrollable_frame)


class DashboardPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        # Main scrollable container
        container, self.scroll_frame, canvas = create_scrollable_frame(self.parent)
        container.pack(fill='both', expand=True)

        main = self.scroll_frame
        main.config(padx=30, pady=20)

        # Header
        header = tk.Frame(main, bg=COLORS['bg_medium'])
        header.pack(fill='x', pady=(0, 20))

        greeting = self.get_greeting()
        tk.Label(header, text=f"{greeting} 👋", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        tk.Label(header, text=datetime.now().strftime("%A, %B %d, %Y"),
                 font=FONTS['body'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary']).pack(side='right', pady=10)

        # Stats Row
        self.build_stats_row(main)

        # Two column layout
        columns = tk.Frame(main, bg=COLORS['bg_medium'])
        columns.pack(fill='both', expand=True, pady=20)

        left_col = tk.Frame(columns, bg=COLORS['bg_medium'])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right_col = tk.Frame(columns, bg=COLORS['bg_medium'])
        right_col.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # Left column
        self.build_today_review(left_col)
        self.build_progress_section(left_col)

        # Right column
        self.build_recent_sessions(right_col)
        self.build_goals_summary(right_col)

    def get_greeting(self):
        hour = datetime.now().hour
        if hour < 12:
            return "Good Morning"
        elif hour < 17:
            return "Good Afternoon"
        else:
            return "Good Evening"

    def build_stats_row(self, parent):
        stats_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        stats_frame.pack(fill='x')

        # Get data
        streak = db.get_streak()
        total_time = db.get_total_study_time()
        vocab_stats = db.get_vocabulary_stats()
        weekly = db.get_weekly_stats()
        review_items = len(db.get_vocabulary_for_review())

        stats = [
            ("🔥", streak, "Day Streak", COLORS['accent']),
            ("⏱️", format_duration(total_time), "Total Study Time", COLORS['info']),
            ("📝", vocab_stats['total'], "Total Words", COLORS['success']),
            ("✅", vocab_stats.get('mastered', 0), "Mastered", COLORS['success']),
            ("🔄", review_items, "Due for Review", COLORS['warning']),
            ("📚", weekly['sessions'], "Sessions This Week", COLORS['info']),
        ]

        for i, (icon, value, label, color) in enumerate(stats):
            card = create_stat_card(stats_frame, icon, value, label, color)
            card.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')

        for i in range(len(stats)):
            stats_frame.columnconfigure(i, weight=1)

    def build_today_review(self, parent):
        card = create_card(parent, "📋 Today's Review Items")
        card.pack(fill='x', pady=(0, 15))

        review_items = db.get_vocabulary_for_review()

        if not review_items:
            tk.Label(card, text="✨ No items due for review today!",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['success']).pack(pady=10)
        else:
            tk.Label(card, text=f"You have {len(review_items)} items to review",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['warning']).pack(anchor='w', pady=(0, 10))

            # Show first 5
            for item in review_items[:5]:
                lang = db.get_language_by_id(item['language_id'])
                lang_color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']

                item_frame = tk.Frame(card, bg=COLORS['bg_card'])
                item_frame.pack(fill='x', pady=2)

                tk.Label(item_frame, text="●", font=('Segoe UI', 8),
                         bg=COLORS['bg_card'], fg=lang_color).pack(side='left', padx=(0, 8))
                tk.Label(item_frame, text=item['word'], font=FONTS['body_bold'],
                         bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(side='left')
                tk.Label(item_frame, text=f"  — {item['meaning']}",
                         font=FONTS['body'], bg=COLORS['bg_card'],
                         fg=COLORS['text_secondary']).pack(side='left')

            if len(review_items) > 5:
                tk.Label(card, text=f"  + {len(review_items) - 5} more...",
                         font=FONTS['small'], bg=COLORS['bg_card'],
                         fg=COLORS['text_muted']).pack(anchor='w', pady=(5, 0))

            # Review button
            from utils import create_rounded_button
            btn = create_rounded_button(card, "🔄 Start Review",
                                        lambda: self.app.show_page("review"),
                                        bg=COLORS['btn_success'])
            btn.pack(pady=(10, 0))

    def build_progress_section(self, parent):
        card = create_card(parent, "📈 Language Progress")
        card.pack(fill='x', pady=(0, 15))

        languages = db.get_languages()

        for lang in languages:
            lang_frame = tk.Frame(card, bg=COLORS['bg_card'])
            lang_frame.pack(fill='x', pady=8)

            color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']

            # Language name and stats
            header = tk.Frame(lang_frame, bg=COLORS['bg_card'])
            header.pack(fill='x')

            tk.Label(header, text=f"{lang['icon']} {lang['name']}",
                     font=FONTS['body_bold'], bg=COLORS['bg_card'],
                     fg=color).pack(side='left')

            vocab_stats = db.get_vocabulary_stats(lang['id'])
            total_time = db.get_total_study_time(lang['id'])

            tk.Label(header, text=f"{vocab_stats['total']} words • {format_duration(total_time)}",
                     font=FONTS['small'], bg=COLORS['bg_card'],
                     fg=COLORS['text_secondary']).pack(side='right')

            # Progress bar for vocabulary mastery
            mastered = vocab_stats.get('mastered', 0)
            total = vocab_stats.get('total', 1)
            if total == 0:
                total = 1

            progress = create_progress_bar(lang_frame, mastered, total, color)
            progress.pack(fill='x', pady=(5, 0))

            tk.Label(lang_frame, text=f"{int(mastered / total * 100)}% mastered",
                     font=FONTS['small'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(anchor='e')

    def build_recent_sessions(self, parent):
        card = create_card(parent, "📚 Recent Study Sessions")
        card.pack(fill='x', pady=(0, 15))

        sessions = db.get_study_sessions(limit=5)

        if not sessions:
            tk.Label(card, text="No study sessions yet. Start learning!",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=10)
        else:
            for session in sessions:
                s_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=5)
                s_frame.pack(fill='x')

                lang = db.get_language_by_id(session['language_id'])
                color = COLORS['english'] if lang['name'] == 'English' else COLORS['german']

                left = tk.Frame(s_frame, bg=COLORS['bg_card'])
                left.pack(side='left', fill='x', expand=True)

                tk.Label(left, text=f"{lang['icon']} {session['topic'] or session['unit_lesson'] or 'Study Session'}",
                         font=FONTS['body_bold'], bg=COLORS['bg_card'],
                         fg=COLORS['text_primary']).pack(anchor='w')
                tk.Label(left, text=session['date'],
                         font=FONTS['small'], bg=COLORS['bg_card'],
                         fg=COLORS['text_muted']).pack(anchor='w')

                tk.Label(s_frame, text=f"{session['duration_minutes']}min",
                         font=FONTS['body_bold'], bg=COLORS['bg_card'],
                         fg=color).pack(side='right')

                # Separator
                tk.Frame(card, bg=COLORS['border'], height=1).pack(fill='x', pady=2)

    def build_goals_summary(self, parent):
        card = create_card(parent, "🎯 Active Goals")
        card.pack(fill='x', pady=(0, 15))

        goals = db.get_goals(status='Active')

        if not goals:
            tk.Label(card, text="No active goals. Set some goals!",
                     font=FONTS['body'], bg=COLORS['bg_card'],
                     fg=COLORS['text_muted']).pack(pady=10)
        else:
            for goal in goals[:4]:
                g_frame = tk.Frame(card, bg=COLORS['bg_card'], pady=5)
                g_frame.pack(fill='x')

                tk.Label(g_frame, text=goal['title'], font=FONTS['body_bold'],
                         bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w')

                if goal['target_value'] > 0:
                    progress = create_progress_bar(g_frame, goal['current_value'],
                                                   goal['target_value'], COLORS['accent'])
                    progress.pack(fill='x', pady=(3, 0))

                    tk.Label(g_frame,
                             text=f"{goal['current_value']}/{goal['target_value']} {goal['unit'] or ''}",
                             font=FONTS['small'], bg=COLORS['bg_card'],
                             fg=COLORS['text_muted']).pack(anchor='e')