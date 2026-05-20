import tkinter as tk
from tkinter import ttk
from datetime import datetime


# ============ Color Scheme ============
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'bg_card': '#1e2a4a',
    'bg_card_hover': '#253557',
    'accent': '#e94560',
    'accent_light': '#ff6b6b',
    'success': '#00d2d3',
    'warning': '#feca57',
    'info': '#54a0ff',
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0b0',
    'text_muted': '#6c6c7c',
    'english': '#54a0ff',
    'german': '#00d2d3',
    'border': '#2d3748',
    'input_bg': '#2d3436',
    'input_border': '#4a5568',
    'btn_primary': '#e94560',
    'btn_secondary': '#4a5568',
    'btn_success': '#00b894',
    'btn_warning': '#fdcb6e',
    'sidebar_bg': '#0d1b2a',
    'sidebar_active': '#1b2838',
    'sidebar_hover': '#162032',
    'progress_bg': '#2d3748',
    'scrollbar': '#4a5568',
}

FONTS = {
    'title': ('Segoe UI', 24, 'bold'),
    'subtitle': ('Segoe UI', 18, 'bold'),
    'heading': ('Segoe UI', 14, 'bold'),
    'body': ('Segoe UI', 11),
    'body_bold': ('Segoe UI', 11, 'bold'),
    'small': ('Segoe UI', 9),
    'small_bold': ('Segoe UI', 9, 'bold'),
    'icon': ('Segoe UI Emoji', 16),
    'icon_large': ('Segoe UI Emoji', 24),
    'mono': ('Consolas', 11),
}


def create_rounded_button(parent, text, command, bg=None, fg=None, width=None, height=2):
    if bg is None:
        bg = COLORS['btn_primary']
    if fg is None:
        fg = COLORS['text_primary']

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=FONTS['body_bold'],
        relief='flat',
        cursor='hand2',
        padx=20,
        pady=8,
        activebackground=COLORS['accent_light'],
        activeforeground=COLORS['text_primary'],
        borderwidth=0,
        highlightthickness=0,
    )
    if width:
        btn.config(width=width)

    def on_enter(e):
        btn.config(bg=COLORS['accent_light'])

    def on_leave(e):
        btn.config(bg=bg)

    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)

    return btn


def create_card(parent, title="", bg=None):
    if bg is None:
        bg = COLORS['bg_card']

    frame = tk.Frame(parent, bg=bg, padx=20, pady=15, highlightthickness=1,
                     highlightbackground=COLORS['border'])

    if title:
        lbl = tk.Label(frame, text=title, font=FONTS['heading'],
                       bg=bg, fg=COLORS['text_primary'], anchor='w')
        lbl.pack(fill='x', pady=(0, 10))

    return frame


def create_stat_card(parent, icon, value, label, color=None, bg=None):
    if bg is None:
        bg = COLORS['bg_card']
    if color is None:
        color = COLORS['accent']

    frame = tk.Frame(parent, bg=bg, padx=20, pady=15, highlightthickness=1,
                     highlightbackground=COLORS['border'])

    icon_lbl = tk.Label(frame, text=icon, font=('Segoe UI Emoji', 20),
                        bg=bg, fg=color)
    icon_lbl.pack(anchor='w')

    value_lbl = tk.Label(frame, text=str(value), font=('Segoe UI', 28, 'bold'),
                         bg=bg, fg=color)
    value_lbl.pack(anchor='w', pady=(5, 0))

    label_lbl = tk.Label(frame, text=label, font=FONTS['small'],
                         bg=bg, fg=COLORS['text_secondary'])
    label_lbl.pack(anchor='w')

    return frame


def create_progress_bar(parent, value, max_value, color=None, height=8, bg=None):
    if bg is None:
        bg = COLORS['bg_card']
    if color is None:
        color = COLORS['accent']

    frame = tk.Frame(parent, bg=bg, height=height)

    canvas = tk.Canvas(frame, height=height, bg=COLORS['progress_bg'],
                       highlightthickness=0)
    canvas.pack(fill='x')

    def draw_bar(event=None):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1:
            w = 200
        # Background
        canvas.create_rectangle(0, 0, w, height, fill=COLORS['progress_bg'], outline='')
        # Progress
        if max_value > 0:
            progress_width = int((value / max_value) * w)
            canvas.create_rectangle(0, 0, progress_width, height, fill=color, outline='')

    canvas.bind('<Configure>', draw_bar)
    frame.after(100, draw_bar)

    return frame


def create_input_field(parent, label_text, placeholder="", bg=None):
    if bg is None:
        bg = COLORS['bg_card']

    frame = tk.Frame(parent, bg=bg)

    label = tk.Label(frame, text=label_text, font=FONTS['small_bold'],
                     bg=bg, fg=COLORS['text_secondary'], anchor='w')
    label.pack(fill='x', pady=(0, 4))

    entry = tk.Entry(frame, font=FONTS['body'], bg=COLORS['input_bg'],
                     fg=COLORS['text_primary'], insertbackground=COLORS['text_primary'],
                     relief='flat', highlightthickness=1,
                     highlightbackground=COLORS['input_border'],
                     highlightcolor=COLORS['accent'])
    entry.pack(fill='x', ipady=6)

    if placeholder:
        entry.insert(0, placeholder)
        entry.config(fg=COLORS['text_muted'])

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
                entry.config(fg=COLORS['text_primary'])

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=COLORS['text_muted'])

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    return frame, entry


def create_dropdown(parent, label_text, options, bg=None):
    if bg is None:
        bg = COLORS['bg_card']

    frame = tk.Frame(parent, bg=bg)

    label = tk.Label(frame, text=label_text, font=FONTS['small_bold'],
                     bg=bg, fg=COLORS['text_secondary'], anchor='w')
    label.pack(fill='x', pady=(0, 4))

    var = tk.StringVar()
    if options:
        var.set(options[0])

    combo = ttk.Combobox(frame, textvariable=var, values=options,
                         font=FONTS['body'], state='readonly')
    combo.pack(fill='x', ipady=4)

    return frame, var, combo


def create_text_area(parent, label_text, height=4, bg=None):
    if bg is None:
        bg = COLORS['bg_card']

    frame = tk.Frame(parent, bg=bg)

    label = tk.Label(frame, text=label_text, font=FONTS['small_bold'],
                     bg=bg, fg=COLORS['text_secondary'], anchor='w')
    label.pack(fill='x', pady=(0, 4))

    text = tk.Text(frame, font=FONTS['body'], bg=COLORS['input_bg'],
                   fg=COLORS['text_primary'], insertbackground=COLORS['text_primary'],
                   relief='flat', height=height, highlightthickness=1,
                   highlightbackground=COLORS['input_border'],
                   highlightcolor=COLORS['accent'], wrap='word')
    text.pack(fill='x')

    return frame, text


def create_scrollable_frame(parent, bg=None):
    if bg is None:
        bg = COLORS['bg_medium']

    container = tk.Frame(parent, bg=bg)

    canvas = tk.Canvas(container, bg=bg, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    scrollable = tk.Frame(canvas, bg=bg)
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return container, scrollable, canvas


def format_duration(minutes):
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def get_status_color(status):
    status_colors = {
        'New': COLORS['info'],
        'Learning': COLORS['warning'],
        'Reviewing': COLORS['accent'],
        'Mastered': COLORS['success'],
        'Known': COLORS['success'],
        'Active': COLORS['accent'],
        'Completed': COLORS['success'],
        'Not Started': COLORS['text_muted'],
        'In Progress': COLORS['info'],
        'Practicing': COLORS['warning'],
        'Solid': COLORS['success'],
    }
    return status_colors.get(status, COLORS['text_secondary'])