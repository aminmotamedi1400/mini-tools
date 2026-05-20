import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import random
import database as db
from utils import (COLORS, FONTS, create_card, create_rounded_button,
                   create_scrollable_frame)


class ReviewPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.review_items = []
        self.current_index = 0
        self.showing_answer = False
        self.session_results = {'correct': 0, 'incorrect': 0}
        self.build()

    def build(self):
        # Header
        header = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30, pady=15)
        header.pack(fill='x')

        tk.Label(header, text="🔄 Review Session", font=FONTS['title'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='left')

        # Review mode selector
        mode_frame = tk.Frame(header, bg=COLORS['bg_medium'])
        mode_frame.pack(side='right')

        self.mode_var = tk.StringVar(value="vocabulary")

        modes = [("📝 Vocabulary", "vocabulary"), ("❌ Errors", "errors"), ("📐 Grammar", "grammar")]
        for text, value in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=value,
                                bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['bg_card'], font=FONTS['body'],
                                activebackground=COLORS['bg_medium'],
                                activeforeground=COLORS['text_primary'],
                                command=self.load_review_items)
            rb.pack(side='left', padx=8)

        # Main content area
        self.content_frame = tk.Frame(self.parent, bg=COLORS['bg_medium'], padx=30)
        self.content_frame.pack(fill='both', expand=True, pady=10)

        self.load_review_items()

    def load_review_items(self):
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        mode = self.mode_var.get()
        self.current_index = 0
        self.showing_answer = False
        self.session_results = {'correct': 0, 'incorrect': 0}

        if mode == "vocabulary":
            items = db.get_vocabulary_for_review()
            self.review_items = [dict(item) for item in items]
        elif mode == "errors":
            items = db.get_errors_for_review()
            self.review_items = [dict(item) for item in items]
        else:
            # Grammar - get topics that need review
            conn = db.get_connection()
            today = datetime.now().strftime("%Y-%m-%d")
            items = conn.execute("""
                SELECT * FROM grammar_topics 
                WHERE status != 'Solid' AND (next_review IS NULL OR next_review <= ?)
                ORDER BY mastery_percent ASC
            """, (today,)).fetchall()
            conn.close()
            self.review_items = [dict(item) for item in items]

        if not self.review_items:
            self.show_empty_state()
        else:
            random.shuffle(self.review_items)
            self.show_review_card()

    def show_empty_state(self):
        empty_frame = tk.Frame(self.content_frame, bg=COLORS['bg_medium'])
        empty_frame.pack(expand=True)

        tk.Label(empty_frame, text="✨", font=('Segoe UI Emoji', 48),
                 bg=COLORS['bg_medium']).pack(pady=(0, 10))
        tk.Label(empty_frame, text="Nothing to review right now!",
                 font=FONTS['subtitle'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_primary']).pack()
        tk.Label(empty_frame, text="All items are up to date. Come back later or add more content.",
                 font=FONTS['body'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_secondary']).pack(pady=(5, 20))

        btn = create_rounded_button(empty_frame, "📝 Go to Vocabulary",
                                    lambda: self.app.show_page("vocabulary"),
                                    bg=COLORS['btn_primary'])
        btn.pack()

    def show_review_card(self):
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.current_index >= len(self.review_items):
            self.show_session_complete()
            return

        item = self.review_items[self.current_index]
        mode = self.mode_var.get()

        # Progress bar
        progress_frame = tk.Frame(self.content_frame, bg=COLORS['bg_medium'])
        progress_frame.pack(fill='x', pady=(0, 15))

        progress_text = f"Card {self.current_index + 1} of {len(self.review_items)}"
        tk.Label(progress_frame, text=progress_text, font=FONTS['body'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side='left')

        results_text = f"✅ {self.session_results['correct']}  |  ❌ {self.session_results['incorrect']}"
        tk.Label(progress_frame, text=results_text, font=FONTS['body_bold'],
                 bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(side='right')

        # Progress bar visual
        if len(self.review_items) > 0:
            prog_canvas = tk.Canvas(self.content_frame, height=6, bg=COLORS['progress_bg'],
                                    highlightthickness=0)
            prog_canvas.pack(fill='x', pady=(0, 20))
            prog_canvas.update_idletasks()
            w = prog_canvas.winfo_width() or 800
            progress_width = int((self.current_index / len(self.review_items)) * w)
            prog_canvas.create_rectangle(0, 0, progress_width, 6, fill=COLORS['accent'], outline='')

        # Card
        card = tk.Frame(self.content_frame, bg=COLORS['bg_card'], padx=40, pady=40,
                        highlightthickness=2, highlightbackground=COLORS['border'])
        card.pack(fill='both', expand=True, padx=50)

        # Language indicator
        lang = db.get_language_by_id(item['language_id'])
        lang_color = COLORS['english'] if lang and lang['name'] == 'English' else COLORS['german']

        tk.Label(card, text=f"{lang['icon']} {lang['name']}" if lang else "🌐",
                 font=FONTS['body'], bg=COLORS['bg_card'], fg=lang_color).pack(anchor='w')

        if mode == "vocabulary":
            self.show_vocab_card(card, item)
        elif mode == "errors":
            self.show_error_card(card, item)
        else:
            self.show_grammar_card(card, item)

    def show_vocab_card(self, card, item):
        # Question - show word
        tk.Label(card, text="What does this word mean?", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(pady=(20, 10))

        tk.Label(card, text=item['word'], font=('Segoe UI', 36, 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(pady=10)

        if item.get('article'):
            tk.Label(card, text=f"({item['article']})", font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['info']).pack()

        if item.get('part_of_speech'):
            tk.Label(card, text=item['part_of_speech'], font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(pady=(5, 0))

        # Answer area
        self.answer_frame = tk.Frame(card, bg=COLORS['bg_card'])
        self.answer_frame.pack(fill='x', pady=20)

        if not self.showing_answer:
            # Show "Reveal" button
            reveal_btn = create_rounded_button(self.answer_frame, "👁️ Show Answer",
                                               self.reveal_answer, bg=COLORS['info'])
            reveal_btn.pack(pady=10)
        else:
            # Show answer
            tk.Frame(self.answer_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=10)

            tk.Label(self.answer_frame, text=item.get('meaning', 'N/A'),
                     font=('Segoe UI', 24, 'bold'), bg=COLORS['bg_card'],
                     fg=COLORS['success']).pack(pady=10)

            if item.get('example_sentence'):
                tk.Label(self.answer_frame, text=f"📝 {item['example_sentence']}",
                         font=FONTS['body'], bg=COLORS['bg_card'],
                         fg=COLORS['text_secondary'], wraplength=500).pack(pady=5)

            if item.get('collocations'):
                tk.Label(self.answer_frame, text=f"🔗 {item['collocations']}",
                         font=FONTS['small'], bg=COLORS['bg_card'],
                         fg=COLORS['text_muted']).pack(pady=2)

            # Rating buttons
            self.show_rating_buttons(card, item)

    def show_error_card(self, card, item):
        tk.Label(card, text="What's wrong with this?", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(pady=(20, 10))

        tk.Label(card, text=f"❌ {item['wrong_form']}", font=('Segoe UI', 28, 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['accent']).pack(pady=10)

        if item.get('category'):
            tk.Label(card, text=f"Category: {item['category']}", font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()

        self.answer_frame = tk.Frame(card, bg=COLORS['bg_card'])
        self.answer_frame.pack(fill='x', pady=20)

        if not self.showing_answer:
            reveal_btn = create_rounded_button(self.answer_frame, "👁️ Show Correct Form",
                                               self.reveal_answer, bg=COLORS['info'])
            reveal_btn.pack(pady=10)
        else:
            tk.Frame(self.answer_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=10)

            tk.Label(self.answer_frame, text=f"✅ {item['correct_form']}",
                     font=('Segoe UI', 24, 'bold'), bg=COLORS['bg_card'],
                     fg=COLORS['success']).pack(pady=10)

            if item.get('explanation'):
                tk.Label(self.answer_frame, text=f"💡 {item['explanation']}",
                         font=FONTS['body'], bg=COLORS['bg_card'],
                         fg=COLORS['text_secondary'], wraplength=500).pack(pady=5)

            self.show_error_rating_buttons(card, item)

    def show_grammar_card(self, card, item):
        tk.Label(card, text="Grammar Review", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(pady=(20, 10))

        tk.Label(card, text=item['title'], font=('Segoe UI', 28, 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(pady=10)

        if item.get('category'):
            tk.Label(card, text=f"Category: {item['category']}", font=FONTS['small'],
                     bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()

        tk.Label(card, text=f"Mastery: {item['mastery_percent']}%", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['info']).pack(pady=5)

        self.answer_frame = tk.Frame(card, bg=COLORS['bg_card'])
        self.answer_frame.pack(fill='x', pady=20)

        if not self.showing_answer:
            reveal_btn = create_rounded_button(self.answer_frame, "👁️ Show Details",
                                               self.reveal_answer, bg=COLORS['info'])
            reveal_btn.pack(pady=10)
        else:
            tk.Frame(self.answer_frame, bg=COLORS['border'], height=1).pack(fill='x', pady=10)

            if item.get('explanation'):
                tk.Label(self.answer_frame, text=item['explanation'],
                         font=FONTS['body'], bg=COLORS['bg_card'],
                         fg=COLORS['text_secondary'], wraplength=500, justify='left').pack(anchor='w', pady=5)

            if item.get('examples'):
                tk.Label(self.answer_frame, text=f"Examples:\n{item['examples']}",
                         font=FONTS['mono'], bg=COLORS['bg_card'],
                         fg=COLORS['info'], wraplength=500, justify='left').pack(anchor='w', pady=5)

            self.show_grammar_rating_buttons(card, item)

    def reveal_answer(self):
        self.showing_answer = True
        self.show_review_card()

    def show_rating_buttons(self, card, item):
        btn_frame = tk.Frame(card, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        tk.Label(btn_frame, text="How well did you know it?", font=FONTS['body'],
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(pady=(0, 10))

        buttons_frame = tk.Frame(btn_frame, bg=COLORS['bg_card'])
        buttons_frame.pack()

        # Wrong button
        wrong_btn = create_rounded_button(buttons_frame, "❌ Didn't Know",
                                          lambda: self.rate_vocab(item, False),
                                          bg=COLORS['accent'])
        wrong_btn.pack(side='left', padx=10)

        # Correct button
        correct_btn = create_rounded_button(buttons_frame, "✅ Knew It!",
                                            lambda: self.rate_vocab(item, True),
                                            bg=COLORS['btn_success'])
        correct_btn.pack(side='left', padx=10)

    def show_error_rating_buttons(self, card, item):
        btn_frame = tk.Frame(card, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        buttons_frame = tk.Frame(btn_frame, bg=COLORS['bg_card'])
        buttons_frame.pack()

        wrong_btn = create_rounded_button(buttons_frame, "❌ Still Confusing",
                                          lambda: self.rate_error(item, False),
                                          bg=COLORS['accent'])
        wrong_btn.pack(side='left', padx=10)

        correct_btn = create_rounded_button(buttons_frame, "✅ Got It!",
                                            lambda: self.rate_error(item, True),
                                            bg=COLORS['btn_success'])
        correct_btn.pack(side='left', padx=10)

    def show_grammar_rating_buttons(self, card, item):
        btn_frame = tk.Frame(card, bg=COLORS['bg_card'])
        btn_frame.pack(fill='x', pady=(15, 0))

        buttons_frame = tk.Frame(btn_frame, bg=COLORS['bg_card'])
        buttons_frame.pack()

        wrong_btn = create_rounded_button(buttons_frame, "❌ Need More Practice",
                                          lambda: self.rate_grammar(item, False),
                                          bg=COLORS['accent'])
        wrong_btn.pack(side='left', padx=10)

        correct_btn = create_rounded_button(buttons_frame, "✅ Solid!",
                                            lambda: self.rate_grammar(item, True),
                                            bg=COLORS['btn_success'])
        correct_btn.pack(side='left', padx=10)

    def rate_vocab(self, item, success):
        db.update_vocabulary_review(item['id'], success)

        if success:
            self.session_results['correct'] += 1
        else:
            self.session_results['incorrect'] += 1

        self.current_index += 1
        self.showing_answer = False
        self.show_review_card()

    def rate_error(self, item, success):
        conn = db.get_connection()
        if success:
            next_review = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            conn.execute("UPDATE error_log SET next_review=?, last_reviewed=? WHERE id=?",
                         (next_review, datetime.now().strftime("%Y-%m-%d"), item['id']))
            self.session_results['correct'] += 1
        else:
            next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            conn.execute("""
                UPDATE error_log SET next_review=?, last_reviewed=?, frequency=frequency+1 WHERE id=?
            """, (next_review, datetime.now().strftime("%Y-%m-%d"), item['id']))
            self.session_results['incorrect'] += 1
        conn.commit()
        conn.close()

        self.current_index += 1
        self.showing_answer = False
        self.show_review_card()

    def rate_grammar(self, item, success):
        conn = db.get_connection()
        if success:
            new_mastery = min(100, item['mastery_percent'] + 10)
            next_review = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            status = 'Solid' if new_mastery >= 90 else 'Reviewing'
            self.session_results['correct'] += 1
        else:
            new_mastery = max(0, item['mastery_percent'] - 5)
            next_review = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            status = 'Practicing'
            self.session_results['incorrect'] += 1

        conn.execute("""
            UPDATE grammar_topics SET mastery_percent=?, status=?, next_review=?,
            last_reviewed=?, review_count=review_count+1 WHERE id=?
        """, (new_mastery, status, next_review,
              datetime.now().strftime("%Y-%m-%d"), item['id']))
        conn.commit()
        conn.close()

        self.current_index += 1
        self.showing_answer = False
        self.show_review_card()

    def show_session_complete(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        complete_frame = tk.Frame(self.content_frame, bg=COLORS['bg_medium'])
        complete_frame.pack(expand=True)

        tk.Label(complete_frame, text="🎉", font=('Segoe UI Emoji', 64),
                 bg=COLORS['bg_medium']).pack(pady=(0, 10))

        tk.Label(complete_frame, text="Review Complete!",
                 font=FONTS['title'], bg=COLORS['bg_medium'],
                 fg=COLORS['text_primary']).pack(pady=(0, 20))

        # Results
        total = self.session_results['correct'] + self.session_results['incorrect']
        if total > 0:
            accuracy = int((self.session_results['correct'] / total) * 100)
        else:
            accuracy = 0

        results_frame = tk.Frame(complete_frame, bg=COLORS['bg_card'], padx=40, pady=30,
                                 highlightthickness=1, highlightbackground=COLORS['border'])
        results_frame.pack(pady=10)

        tk.Label(results_frame, text=f"📊 Results", font=FONTS['heading'],
                 bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(pady=(0, 15))

        stats = [
            (f"✅ Correct: {self.session_results['correct']}", COLORS['success']),
            (f"❌ Incorrect: {self.session_results['incorrect']}", COLORS['accent']),
            (f"📈 Accuracy: {accuracy}%", COLORS['info']),
            (f"📝 Total Reviewed: {total}", COLORS['text_primary']),
        ]

        for text, color in stats:
            tk.Label(results_frame, text=text, font=FONTS['body_bold'],
                     bg=COLORS['bg_card'], fg=color).pack(anchor='w', pady=3)

        # Encouragement
        if accuracy >= 80:
            msg = "🌟 Excellent! Keep up the great work!"
        elif accuracy >= 60:
            msg = "👍 Good job! Keep practicing!"
        else:
            msg = "💪 Don't worry! Practice makes perfect!"

        tk.Label(complete_frame, text=msg, font=FONTS['body'],
                 bg=COLORS['bg_medium'], fg=COLORS['warning']).pack(pady=20)

        # Buttons
        btn_frame = tk.Frame(complete_frame, bg=COLORS['bg_medium'])
        btn_frame.pack(pady=10)

        again_btn = create_rounded_button(btn_frame, "🔄 Review Again",
                                          self.load_review_items, bg=COLORS['btn_primary'])
        again_btn.pack(side='left', padx=10)

        dash_btn = create_rounded_button(btn_frame, "📊 Dashboard",
                                         lambda: self.app.show_page("dashboard"),
                                         bg=COLORS['btn_secondary'])
        dash_btn.pack(side='left', padx=10)