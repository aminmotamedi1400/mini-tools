import tkinter as tk
from tkinter import ttk
import traceback
import sys
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
        # Redirect error handling
        self.setup_global_exception_handler()
        
        try:
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
            
        except Exception as e:
            self.log_error("Initialization error", e)
            # Try to recover with minimal UI
            self.create_emergency_ui()

    def setup_global_exception_handler(self):
        """Setup global exception handler to catch all errors"""
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            # Log the error
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.log_error("Unhandled exception", error_msg)
            
            # Don't close the app, just show a message
            if hasattr(self, 'root') and self.root:
                try:
                    self.show_error_notification(str(exc_value))
                except:
                    pass
            
            # Don't let the app crash
            return True  # Prevents the default exception handler
        
        sys.excepthook = global_exception_handler
        
        # Also catch tkinter exceptions
        try:
            tk.Tk.report_callback_exception = self.tk_exception_handler
        except:
            pass
    
    def tk_exception_handler(self, exc, val, tb):
        """Handle tkinter callback exceptions"""
        error_msg = ''.join(traceback.format_exception(exc, val, tb))
        self.log_error("Tkinter callback error", error_msg)
        self.show_error_notification(str(val))
        # Don't crash, continue running
    
    def log_error(self, context, error):
        """Log error to file (optional)"""
        try:
            import datetime
            with open('app_errors.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now()}] {context}: {error}\n")
                f.write("-" * 50 + "\n")
        except:
            pass  # Don't crash if logging fails
    
    def show_error_notification(self, message):
        """Show error notification without crashing"""
        try:
            # Create a small notification window
            notification = tk.Toplevel(self.root)
            notification.title("Error Occurred")
            notification.geometry("400x150")
            notification.configure(bg=COLORS['bg_medium'])
            
            # Center on parent
            notification.transient(self.root)
            notification.grab_set()
            
            tk.Label(notification, text="⚠️", font=('Segoe UI Emoji', 24),
                    bg=COLORS['bg_medium'], fg='orange').pack(pady=(20, 5))
            tk.Label(notification, text="An error occurred but the app continues to run.",
                    font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack()
            tk.Label(notification, text=f"Error: {message[:100]}",
                    font=FONTS['small'], bg=COLORS['bg_medium'], fg='red', wraplength=350).pack(pady=5)
            
            tk.Button(notification, text="OK", command=notification.destroy,
                    bg=COLORS['accent'], fg='white', padx=20, pady=5).pack(pady=10)
            
            # Auto close after 5 seconds
            self.root.after(5000, notification.destroy)
        except:
            pass  # Don't crash while showing error
    
    def create_emergency_ui(self):
        """Create emergency UI if main initialization fails"""
        try:
            if not hasattr(self, 'root') or not self.root:
                self.root = tk.Tk()
                self.root.title("Language Learning Manager - Emergency Mode")
                self.root.geometry("800x600")
                self.root.configure(bg='#2b2b2b')
            
            # Clear any existing widgets
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # Create emergency UI
            frame = tk.Frame(self.root, bg='#2b2b2b')
            frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            tk.Label(frame, text="⚠️ Application Recovered", 
                    font=('Segoe UI', 18, 'bold'), bg='#2b2b2b', fg='white').pack(pady=20)
            tk.Label(frame, text="The application encountered an error but is running in safe mode.\n"
                                "Please restart the app for full functionality.",
                    font=('Segoe UI', 11), bg='#2b2b2b', fg='#cccccc', justify='center').pack(pady=10)
            
            tk.Button(frame, text="Restart Application", 
                    command=lambda: self.restart_app(),
                    bg='#4a90e2', fg='white', padx=30, pady=10,
                    font=('Segoe UI', 10, 'bold')).pack(pady=20)
            
            tk.Button(frame, text="Continue Anyway", 
                    command=lambda: self.continue_with_limited_functionality(),
                    bg='#555555', fg='white', padx=30, pady=5).pack(pady=10)
            
        except Exception as e:
            # Ultimate fallback
            print(f"Critical error in emergency UI: {e}")
            self.root = tk.Tk()
            self.root.title("CRITICAL ERROR")
            self.root.geometry("400x200")
            tk.Label(self.root, text="Please restart the application", 
                    font=('Segoe UI', 12)).pack(expand=True)
    
    def restart_app(self):
        """Restart the application"""
        try:
            self.root.destroy()
        except:
            pass
        import subprocess
        import sys
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    
    def continue_with_limited_functionality(self):
        """Continue with basic functionality"""
        # Try to rebuild UI
        self.build_sidebar()
        self.build_main_area()
        self.show_page("dashboard")
    
    def configure_styles(self):
        try:
            style = ttk.Style()
            style.theme_use('clam')

            style.configure('TCombobox',
                            fieldbackground=COLORS.get('input_bg', '#3a3a3a'),
                            background=COLORS.get('input_bg', '#3a3a3a'),
                            foreground=COLORS.get('text_primary', '#ffffff'),
                            borderwidth=1,
                            relief='flat')

            style.map('TCombobox',
                      fieldbackground=[('readonly', COLORS.get('input_bg', '#3a3a3a'))],
                      foreground=[('readonly', COLORS.get('text_primary', '#ffffff'))])

            style.configure('TScrollbar',
                            background=COLORS.get('scrollbar', '#555555'),
                            troughcolor=COLORS.get('bg_dark', '#2b2b2b'),
                            borderwidth=0)

            style.configure('Treeview',
                            background=COLORS.get('bg_card', '#3a3a3a'),
                            foreground=COLORS.get('text_primary', '#ffffff'),
                            fieldbackground=COLORS.get('bg_card', '#3a3a3a'),
                            borderwidth=0,
                            font=FONTS.get('body', ('Segoe UI', 10)))

            style.configure('Treeview.Heading',
                            background=COLORS.get('bg_light', '#4a4a4a'),
                            foreground=COLORS.get('text_primary', '#ffffff'),
                            font=FONTS.get('body_bold', ('Segoe UI', 10, 'bold')),
                            borderwidth=0)

            style.map('Treeview',
                      background=[('selected', COLORS.get('bg_light', '#4a4a4a'))],
                      foreground=[('selected', COLORS.get('text_primary', '#ffffff'))])
        except Exception as e:
            self.log_error("Style configuration error", e)
            # Use fallback styles if needed
    
    def build_sidebar(self):
        try:
            self.sidebar = tk.Frame(self.root, bg=COLORS.get('sidebar_bg', '#2b2b2b'), width=250)
            self.sidebar.pack(side='left', fill='y')
            self.sidebar.pack_propagate(False)

            # Logo / Title
            logo_frame = tk.Frame(self.sidebar, bg=COLORS.get('sidebar_bg', '#2b2b2b'), pady=20)
            logo_frame.pack(fill='x')

            tk.Label(logo_frame, text="🌐", font=('Segoe UI Emoji', 30),
                     bg=COLORS.get('sidebar_bg', '#2b2b2b'), fg=COLORS.get('accent', '#4a90e2')).pack()
            tk.Label(logo_frame, text="Language\nLearning Manager",
                     font=('Segoe UI', 12, 'bold'), bg=COLORS.get('sidebar_bg', '#2b2b2b'),
                     fg=COLORS.get('text_primary', '#ffffff'), justify='center').pack(pady=(5, 0))

            # Separator
            tk.Frame(self.sidebar, bg=COLORS.get('border', '#444444'), height=1).pack(fill='x', padx=20, pady=10)

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
            bottom_frame = tk.Frame(self.sidebar, bg=COLORS.get('sidebar_bg', '#2b2b2b'))
            bottom_frame.pack(side='bottom', fill='x', pady=20)

            tk.Frame(bottom_frame, bg=COLORS.get('border', '#444444'), height=1).pack(fill='x', padx=20, pady=10)

            # Version info
            tk.Label(bottom_frame, text="v1.0.0 • Made with ❤️",
                     font=FONTS.get('small', ('Segoe UI', 8)), bg=COLORS.get('sidebar_bg', '#2b2b2b'),
                     fg=COLORS.get('text_muted', '#888888')).pack()
        except Exception as e:
            self.log_error("Sidebar building error", e)

    def create_menu_button(self, page_id, icon, label):
        try:
            frame = tk.Frame(self.sidebar, bg=COLORS.get('sidebar_bg', '#2b2b2b'), cursor='hand2')
            frame.pack(fill='x', padx=10, pady=2)

            inner = tk.Frame(frame, bg=COLORS.get('sidebar_bg', '#2b2b2b'), padx=15, pady=10)
            inner.pack(fill='x')

            icon_lbl = tk.Label(inner, text=icon, font=('Segoe UI Emoji', 14),
                                bg=COLORS.get('sidebar_bg', '#2b2b2b'), fg=COLORS.get('text_secondary', '#cccccc'))
            icon_lbl.pack(side='left')

            text_lbl = tk.Label(inner, text=label, font=FONTS.get('body', ('Segoe UI', 10)),
                                bg=COLORS.get('sidebar_bg', '#2b2b2b'), fg=COLORS.get('text_secondary', '#cccccc'))
            text_lbl.pack(side='left', padx=(12, 0))

            def on_click(e=None):
                try:
                    self.show_page(page_id)
                except Exception as click_error:
                    self.log_error(f"Click error for {page_id}", click_error)
                    self.show_error_notification(str(click_error))

            def on_enter(e):
                if self.current_page_name != page_id:
                    inner.config(bg=COLORS.get('sidebar_hover', '#3a3a3a'))
                    icon_lbl.config(bg=COLORS.get('sidebar_hover', '#3a3a3a'))
                    text_lbl.config(bg=COLORS.get('sidebar_hover', '#3a3a3a'))

            def on_leave(e):
                if self.current_page_name != page_id:
                    inner.config(bg=COLORS.get('sidebar_bg', '#2b2b2b'))
                    icon_lbl.config(bg=COLORS.get('sidebar_bg', '#2b2b2b'))
                    text_lbl.config(bg=COLORS.get('sidebar_bg', '#2b2b2b'))

            for widget in [frame, inner, icon_lbl, text_lbl]:
                widget.bind('<Button-1>', on_click)
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)

            return {'frame': frame, 'inner': inner, 'icon': icon_lbl, 'text': text_lbl}
        except Exception as e:
            self.log_error(f"Menu button creation error for {page_id}", e)
            return None

    def build_main_area(self):
        try:
            self.main_area = tk.Frame(self.root, bg=COLORS.get('bg_medium', '#3a3a3a'))
            self.main_area.pack(side='right', fill='both', expand=True)
        except Exception as e:
            self.log_error("Main area building error", e)

    def show_page(self, page_name):
        try:
            # Update sidebar styling
            for pid, btn in self.menu_buttons.items():
                if btn and pid == page_name:
                    btn['inner'].config(bg=COLORS.get('sidebar_active', '#3a3a3a'))
                    btn['icon'].config(bg=COLORS.get('sidebar_active', '#3a3a3a'), fg=COLORS.get('accent', '#4a90e2'))
                    btn['text'].config(bg=COLORS.get('sidebar_active', '#3a3a3a'), fg=COLORS.get('text_primary', '#ffffff'))
                elif btn:
                    btn['inner'].config(bg=COLORS.get('sidebar_bg', '#2b2b2b'))
                    btn['icon'].config(bg=COLORS.get('sidebar_bg', '#2b2b2b'), fg=COLORS.get('text_secondary', '#cccccc'))
                    btn['text'].config(bg=COLORS.get('sidebar_bg', '#2b2b2b'), fg=COLORS.get('text_secondary', '#cccccc'))

            self.current_page_name = page_name

            # Clear main area
            for widget in self.main_area.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass

            # Load page with error handling
            try:
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
                else:
                    # Fallback to dashboard
                    self.current_page = DashboardPage(self.main_area, self)
            except Exception as page_error:
                self.log_error(f"Error loading page {page_name}", page_error)
                self.show_error_notification(f"Could not load {page_name} page")
                # Load error page instead
                self.show_error_page(page_name)
                
        except Exception as e:
            self.log_error(f"Error in show_page for {page_name}", e)
            self.show_error_notification(str(e))
    
    def show_error_page(self, attempted_page):
        """Show an error page when a page fails to load"""
        try:
            for widget in self.main_area.winfo_children():
                widget.destroy()
            
            error_frame = tk.Frame(self.main_area, bg=COLORS.get('bg_medium', '#3a3a3a'))
            error_frame.pack(expand=True, fill='both')
            
            tk.Label(error_frame, text="⚠️", font=('Segoe UI Emoji', 48),
                    bg=COLORS.get('bg_medium', '#3a3a3a'), fg='orange').pack(pady=50)
            tk.Label(error_frame, text=f"Could not load {attempted_page} page",
                    font=FONTS.get('title', ('Segoe UI', 16, 'bold')),
                    bg=COLORS.get('bg_medium', '#3a3a3a'), fg=COLORS.get('text_primary', '#ffffff')).pack(pady=10)
            tk.Label(error_frame, text="The application encountered an error but continues to run.\n"
                                      "Please try another page or restart the app.",
                    font=FONTS.get('body', ('Segoe UI', 10)),
                    bg=COLORS.get('bg_medium', '#3a3a3a'), fg=COLORS.get('text_secondary', '#cccccc'),
                    justify='center').pack(pady=5)
            
            tk.Button(error_frame, text="Go to Dashboard",
                    command=lambda: self.show_page("dashboard"),
                    bg=COLORS.get('accent', '#4a90e2'), fg='white',
                    padx=20, pady=10, font=('Segoe UI', 10, 'bold')).pack(pady=20)
        except Exception as e:
            self.log_error("Error showing error page", e)
    
    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            self.log_error("Main loop error", e)
            # Keep the app running if possible
            try:
                self.root.after(1000, self.run)
            except:
                pass


if __name__ == "__main__":
    # Create error log file at start
    try:
        import datetime
        with open('app_errors.log', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Application started at {datetime.datetime.now()}\n")
            f.write(f"{'='*60}\n\n")
    except:
        pass
    
    app = LanguageLearningManager()
    app.run()