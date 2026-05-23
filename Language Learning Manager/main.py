import tkinter as tk
from tkinter import ttk
import App.database as db
from App.utils import COLORS, FONTS, create_rounded_button

# Import page modules
from App.dashboard import DashboardPage
from App.vocabulary import VocabularyPage
from App.sessions import SessionsPage
from App.grammar import GrammarPage
from App.errors_log import ErrorsPage
from App.review import ReviewPage
from App.goals import GoalsPage
from App.reports import ReportsPage


class LanguageLearningManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌐 Language Learning Manager")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)
        self.root.configure(bg=COLORS['bg_dark'])

        # Try to set icon
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # Initialize database
        db.init_database()

        # Configure styles
        self.configure_styles()

        # Current page
        self.current_page = None
        self.current_page_name = "dashboard"

        # Build UI
        self.build_sidebar()
        self.build_main_area()

        # Show dashboard
        self.show_page("dashboard")

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TCombobox',
                        fieldbackground=COLORS['input_bg'],
                        background=COLORS['input_bg'],
                        foreground=COLORS['text_primary'],
                        borderwidth=1,
                        relief='flat')

        style.map('TCombobox',
                  fieldbackground=[('readonly', COLORS['input_bg'])],
                  foreground=[('readonly', COLORS['text_primary'])])

        style.configure('TScrollbar',
                        background=COLORS['scrollbar'],
                        troughcolor=COLORS['bg_dark'],
                        borderwidth=0)

        style.configure('Treeview',
                        background=COLORS['bg_card'],
                        foreground=COLORS['text_primary'],
                        fieldbackground=COLORS['bg_card'],
                        borderwidth=0,
                        font=FONTS['body'])

        style.configure('Treeview.Heading',
                        background=COLORS['bg_light'],
                        foreground=COLORS['text_primary'],
                        font=FONTS['body_bold'],
                        borderwidth=0)

        style.map('Treeview',
                  background=[('selected', COLORS['bg_light'])],
                  foreground=[('selected', COLORS['text_primary'])])

    def build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=COLORS['sidebar_bg'], width=250)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Logo / Title
        logo_frame = tk.Frame(self.sidebar, bg=COLORS['sidebar_bg'], pady=20)
        logo_frame.pack(fill='x')

        tk.Label(logo_frame, text="🌐", font=('Segoe UI Emoji', 30),
                 bg=COLORS['sidebar_bg'], fg=COLORS['accent']).pack()
        tk.Label(logo_frame, text="Language\nLearning Manager",
                 font=('Segoe UI', 12, 'bold'), bg=COLORS['sidebar_bg'],
                 fg=COLORS['text_primary'], justify='center').pack(pady=(5, 0))

        # Separator
        tk.Frame(self.sidebar, bg=COLORS['border'], height=1).pack(fill='x', padx=20, pady=10)

        # Menu items
        self.menu_buttons = {}
        menu_items = [
            ("dashboard", "📊", "Dashboard"),
            ("vocabulary", "📝", "Vocabulary"),
            ("sessions", "📚", "Study Sessions"),
            ("grammar", "📐", "Grammar"),
            ("sentences", "💬", "Sentences"),
            ("errors", "❌", "Error Log"),
            ("review", "🔄", "Review"),
            ("goals", "🎯", "Goals"),
            ("reports", "📈", "Reports"),
            ("settings", "⚙️", "Settings"),
        ]

        for page_id, icon, label in menu_items:
            btn = self.create_menu_button(page_id, icon, label)
            self.menu_buttons[page_id] = btn

        # Bottom section
        bottom_frame = tk.Frame(self.sidebar, bg=COLORS['sidebar_bg'])
        bottom_frame.pack(side='bottom', fill='x', pady=20)

        tk.Frame(bottom_frame, bg=COLORS['border'], height=1).pack(fill='x', padx=20, pady=10)

        # Version info
        tk.Label(bottom_frame, text="v1.0.0 • Made with ❤️",
                 font=FONTS['small'], bg=COLORS['sidebar_bg'],
                 fg=COLORS['text_muted']).pack()

    def create_menu_button(self, page_id, icon, label):
        frame = tk.Frame(self.sidebar, bg=COLORS['sidebar_bg'], cursor='hand2')
        frame.pack(fill='x', padx=10, pady=2)

        inner = tk.Frame(frame, bg=COLORS['sidebar_bg'], padx=15, pady=10)
        inner.pack(fill='x')

        icon_lbl = tk.Label(inner, text=icon, font=('Segoe UI Emoji', 14),
                            bg=COLORS['sidebar_bg'], fg=COLORS['text_secondary'])
        icon_lbl.pack(side='left')

        text_lbl = tk.Label(inner, text=label, font=FONTS['body'],
                            bg=COLORS['sidebar_bg'], fg=COLORS['text_secondary'])
        text_lbl.pack(side='left', padx=(12, 0))

        def on_click(e=None):
            self.show_page(page_id)

        def on_enter(e):
            if self.current_page_name != page_id:
                inner.config(bg=COLORS['sidebar_hover'])
                icon_lbl.config(bg=COLORS['sidebar_hover'])
                text_lbl.config(bg=COLORS['sidebar_hover'])

        def on_leave(e):
            if self.current_page_name != page_id:
                inner.config(bg=COLORS['sidebar_bg'])
                icon_lbl.config(bg=COLORS['sidebar_bg'])
                text_lbl.config(bg=COLORS['sidebar_bg'])

        for widget in [frame, inner, icon_lbl, text_lbl]:
            widget.bind('<Button-1>', on_click)
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)

        return {'frame': frame, 'inner': inner, 'icon': icon_lbl, 'text': text_lbl}

    def build_main_area(self):
        self.main_area = tk.Frame(self.root, bg=COLORS['bg_medium'])
        self.main_area.pack(side='right', fill='both', expand=True)

    def show_page(self, page_name):
        # Update sidebar styling
        for pid, btn in self.menu_buttons.items():
            if pid == page_name:
                btn['inner'].config(bg=COLORS['sidebar_active'])
                btn['icon'].config(bg=COLORS['sidebar_active'], fg=COLORS['accent'])
                btn['text'].config(bg=COLORS['sidebar_active'], fg=COLORS['text_primary'])
            else:
                btn['inner'].config(bg=COLORS['sidebar_bg'])
                btn['icon'].config(bg=COLORS['sidebar_bg'], fg=COLORS['text_secondary'])
                btn['text'].config(bg=COLORS['sidebar_bg'], fg=COLORS['text_secondary'])

        self.current_page_name = page_name

        # Clear main area
        for widget in self.main_area.winfo_children():
            widget.destroy()

        # Load page
        if page_name == "dashboard":
            self.current_page = DashboardPage(self.main_area, self)
        elif page_name == "vocabulary":
            self.current_page = VocabularyPage(self.main_area, self)
        elif page_name == "sessions":
            self.current_page = SessionsPage(self.main_area, self)
        elif page_name == "grammar":
            self.current_page = GrammarPage(self.main_area, self)
        elif page_name == "errors":
            self.current_page = ErrorsPage(self.main_area, self)
        elif page_name == "review":
            self.current_page = ReviewPage(self.main_area, self)
        elif page_name == "goals":
            self.current_page = GoalsPage(self.main_area, self)
        elif page_name == "reports":
            self.current_page = ReportsPage(self.main_area, self)
        elif page_name == "sentences":
            from App.sentences import SentencesPage
            self.current_page = SentencesPage(self.main_area, self)
        elif page_name == "settings":
            from App.settings import SettingsPage
            self.current_page = SettingsPage(self.main_area, self)
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LanguageLearningManager()
    app.run()