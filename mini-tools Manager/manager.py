#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mini-Tools Manager v2.0
A modern, categorized tool launcher for managing and running mini-tools.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # mini-tools folder
CONFIG_FILE = Path(__file__).resolve().parent / "tools_config.json"

# ──────────────────────────────────────────────
# THEME COLORS
# ──────────────────────────────────────────────
THEME = {
    "bg":             "#F0F2F5",
    "sidebar_bg":     "#FFFFFF",
    "card_bg":        "#FFFFFF",
    "card_hover":     "#F8F9FF",
    "card_border":    "#E4E6EB",
    "primary":        "#4F46E5",
    "primary_hover":  "#4338CA",
    "text_dark":      "#1F2937",
    "text_medium":    "#6B7280",
    "text_light":     "#9CA3AF",
    "search_bg":      "#FFFFFF",
    "search_border":  "#D1D5DB",
    "pin_color":      "#F59E0B",
    "success":        "#10B981",
    "danger":         "#EF4444",
}

CATEGORY_COLORS = {
    "All":          ("#6C5CE7", "#F3F0FF"),
    "Pinned":       ("#F59E0B", "#FFFBEB"),
    "Productivity": ("#10B981", "#ECFDF5"),
    "Language":     ("#F59E0B", "#FFFBEB"),
    "Documents":    ("#EF4444", "#FEF2F2"),
    "Development":  ("#3B82F6", "#EFF6FF"),
    "Other":        ("#6B7280", "#F3F4F6"),
}

# ──────────────────────────────────────────────
# DEFAULT TOOL METADATA
# ──────────────────────────────────────────────
DEFAULT_TOOLS_META = {
    "Accountant":              {"category": "Productivity", "description": "Financial tracking and accounting",  "emoji": "\U0001f4b0"},
    "backup csv":              {"category": "Documents",    "description": "CSV file backup utility",            "emoji": "\U0001f4be"},
    "Challenges Manager":      {"category": "Productivity", "description": "Track and manage challenges",        "emoji": "\U0001f3c6"},
    "chat-searcher":           {"category": "Documents",    "description": "Search through chat histories",      "emoji": "\U0001f50d"},
    "File Folders Organizer":  {"category": "Documents",    "description": "Organize files and folders",         "emoji": "\U0001f4c1"},
    "mini-tools Manager":      {"category": "Development",  "description": "This tool manager itself",           "emoji": "\U0001f6e0\ufe0f"},
    "Password Manager":        {"category": "Productivity", "description": "Secure password management",         "emoji": "\U0001f510"},
    "PDF concatinator":        {"category": "Documents",    "description": "Merge multiple PDF files",           "emoji": "\U0001f4c4"},
    "pdf-searcher":            {"category": "Documents",    "description": "Full-text search inside PDFs",       "emoji": "\U0001f50e"},
    "Persian Markdown Viewer": {"category": "Documents",    "description": "Render and view Persian markdown",   "emoji": "\U0001f4dd"},
    "RAG":                     {"category": "Development",  "description": "Retrieval-Augmented Generation",     "emoji": "\U0001f916"},
    "Shopping Management":     {"category": "Productivity", "description": "Shopping list and budget tracker",   "emoji": "\U0001f6d2"},
    "test App":                {"category": "Development",  "description": "Testing and debugging sandbox",      "emoji": "\U0001f9ea"},
    "Thesis Manager":          {"category": "Productivity", "description": "Thesis project management",          "emoji": "\U0001f393"},
    "Language Learning Manager":    {"category": "Language",     "description": "tool for language learning",    "emoji": "\U0001f33f"},
}


# ══════════════════════════════════════════════
# CONFIG MANAGER
# ══════════════════════════════════════════════
class ConfigManager:
    """Handles loading and saving tool configuration to a JSON file."""

    def __init__(self, config_path: Path):
        self.path = config_path
        self.data = {"tools": {}, "settings": {"window_width": 780, "window_height": 680}}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = {"tools": {}, "settings": {"window_width": 780, "window_height": 680}}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_tool_meta(self, tool_name: str) -> dict:
        """Return metadata for a tool, merging defaults with saved config."""
        defaults = DEFAULT_TOOLS_META.get(tool_name, {
            "category": "Other",
            "description": "No description available",
            "emoji": "\U0001f527",
        })
        saved = self.data.get("tools", {}).get(tool_name, {})
        merged = {**defaults, **saved}
        # Ensure pinned and last_used keys exist
        merged.setdefault("pinned", False)
        merged.setdefault("last_used", None)
        return merged

    def set_tool_meta(self, tool_name: str, key: str, value):
        if "tools" not in self.data:
            self.data["tools"] = {}
        if tool_name not in self.data["tools"]:
            self.data["tools"][tool_name] = {}
        self.data["tools"][tool_name][key] = value
        self.save()


# ══════════════════════════════════════════════
# TOOL DISCOVERY
# ══════════════════════════════════════════════
def discover_tools(tools_dir: Path) -> list:
    """
    Scan the tools directory and return a list of (name, script_path) tuples.
    Each subdirectory containing at least one .py file is considered a tool.
    """
    tools = []
    for entry in sorted(tools_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            py_files = sorted(entry.glob("*.py"))
            if py_files:
                tools.append((entry.name, py_files[0]))
    return tools


# ══════════════════════════════════════════════
# TOOL CARD WIDGET
# ══════════════════════════════════════════════
class ToolCard(tk.Frame):
    """A single tool card widget with emoji, name, description, and actions."""

    def __init__(self, parent, tool_name, script_path, meta, on_run, on_pin_toggle, **kwargs):
        super().__init__(parent, **kwargs)

        self.tool_name = tool_name
        self.script_path = script_path
        self.meta = meta
        self.on_run = on_run
        self.on_pin_toggle = on_pin_toggle

        self.configure(bg=THEME["card_bg"], highlightbackground=THEME["card_border"],
                       highlightthickness=1, padx=14, pady=10)

        self._build_ui()
        self._bind_hover()

    def _build_ui(self):
        # -- Top row: emoji + name + pin button --
        top_frame = tk.Frame(self, bg=THEME["card_bg"])
        top_frame.pack(fill=tk.X)

        # Emoji
        emoji_label = tk.Label(top_frame, text=self.meta.get("emoji", "\U0001f527"),
                               font=("Segoe UI Emoji", 18), bg=THEME["card_bg"])
        emoji_label.pack(side=tk.LEFT, padx=(0, 8))

        # Name
        name_label = tk.Label(top_frame, text=self.tool_name,
                              font=("Segoe UI", 12, "bold"), fg=THEME["text_dark"],
                              bg=THEME["card_bg"], anchor="w")
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Pin button
        pin_text = "\u2605" if self.meta.get("pinned") else "\u2606"
        pin_color = THEME["pin_color"] if self.meta.get("pinned") else THEME["text_light"]
        self.pin_btn = tk.Label(top_frame, text=pin_text, font=("Segoe UI", 16),
                                fg=pin_color, bg=THEME["card_bg"], cursor="hand2")
        self.pin_btn.pack(side=tk.RIGHT, padx=(8, 0))
        self.pin_btn.bind("<Button-1>", lambda e: self.on_pin_toggle(self.tool_name))

        # -- Description --
        desc_label = tk.Label(self, text=self.meta.get("description", ""),
                              font=("Segoe UI", 9), fg=THEME["text_medium"],
                              bg=THEME["card_bg"], anchor="w")
        desc_label.pack(fill=tk.X, pady=(4, 6))

        # -- Bottom row: category badge + last used + run button --
        bottom_frame = tk.Frame(self, bg=THEME["card_bg"])
        bottom_frame.pack(fill=tk.X)

        # Category badge
        cat = self.meta.get("category", "Other")
        cat_fg, cat_bg = CATEGORY_COLORS.get(cat, ("#6B7280", "#F3F4F6"))
        cat_label = tk.Label(bottom_frame, text=f"  {cat}  ",
                             font=("Segoe UI", 8, "bold"), fg=cat_fg, bg=cat_bg)
        cat_label.pack(side=tk.LEFT)

        # Last used
        last_used = self.meta.get("last_used")
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used)
                time_str = dt.strftime("%b %d, %H:%M")
            except (ValueError, TypeError):
                time_str = ""
            if time_str:
                last_label = tk.Label(bottom_frame, text=f"Last: {time_str}",
                                      font=("Segoe UI", 8), fg=THEME["text_light"],
                                      bg=THEME["card_bg"])
                last_label.pack(side=tk.LEFT, padx=(10, 0))

        # Run button
        run_btn = tk.Frame(bottom_frame, bg=THEME["primary"], padx=12, pady=3, cursor="hand2")
        run_btn.pack(side=tk.RIGHT)
        run_text = tk.Label(run_btn, text="\u25B6  Run", font=("Segoe UI", 9, "bold"),
                            fg="#FFFFFF", bg=THEME["primary"])
        run_text.pack()

        # Bind click events on run button
        for widget in (run_btn, run_text):
            widget.bind("<Button-1>", lambda e: self.on_run(self.tool_name, self.script_path))
            widget.bind("<Enter>", lambda e, f=run_btn, t=run_text: (
                f.configure(bg=THEME["primary_hover"]),
                t.configure(bg=THEME["primary_hover"])
            ))
            widget.bind("<Leave>", lambda e, f=run_btn, t=run_text: (
                f.configure(bg=THEME["primary"]),
                t.configure(bg=THEME["primary"])
            ))

    def _bind_hover(self):
        """Add hover highlight effect to the whole card."""

        def on_enter(e):
            self.configure(bg=THEME["card_hover"])
            for child in self.winfo_children():
                try:
                    child.configure(bg=THEME["card_hover"])
                except tk.TclError:
                    pass

        def on_leave(e):
            self.configure(bg=THEME["card_bg"])
            for child in self.winfo_children():
                try:
                    child.configure(bg=THEME["card_bg"])
                except tk.TclError:
                    pass

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        self.bind("<Double-1>", lambda e: self.on_run(self.tool_name, self.script_path))


# ══════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════
class ToolManagerApp(tk.Tk):
    """Main application window for Mini-Tools Manager."""

    def __init__(self):
        super().__init__()

        self.title("Mini-Tools Manager v2.0")
        self.configure(bg=THEME["bg"])
        self.minsize(650, 500)

        # Load config
        self.config = ConfigManager(CONFIG_FILE)
        w = self.config.data.get("settings", {}).get("window_width", 780)
        h = self.config.data.get("settings", {}).get("window_height", 680)
        self.geometry(f"{w}x{h}")

        # Discover tools
        self.tools = discover_tools(BASE_DIR)
        self.active_category = "All"
        self.search_query = ""

        # Build the interface
        self._build_header()
        self._build_category_bar()
        self._build_tools_area()
        self._build_status_bar()

        # Populate
        self.refresh_tools()

        # Keyboard shortcuts
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.bind("<Escape>", lambda e: self._clear_search())
        self.bind("<Control-r>", lambda e: self.refresh_tools())

    # ──────────────────────────────────────────
    # UI BUILDING
    # ──────────────────────────────────────────
    def _build_header(self):
        """Build the header section with title and search bar."""
        header = tk.Frame(self, bg=THEME["sidebar_bg"], pady=12, padx=20)
        header.pack(fill=tk.X)

        # Title row
        title_frame = tk.Frame(header, bg=THEME["sidebar_bg"])
        title_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(title_frame, text="\U0001f6e0\ufe0f",
                 font=("Segoe UI Emoji", 20), bg=THEME["sidebar_bg"]).pack(side=tk.LEFT)
        tk.Label(title_frame, text="Mini-Tools Manager",
                 font=("Segoe UI", 18, "bold"), fg=THEME["text_dark"],
                 bg=THEME["sidebar_bg"]).pack(side=tk.LEFT, padx=(8, 0))

        # Tool count
        self.count_label = tk.Label(title_frame, text="",
                                    font=("Segoe UI", 10), fg=THEME["text_medium"],
                                    bg=THEME["sidebar_bg"])
        self.count_label.pack(side=tk.RIGHT)

        # Search bar
        search_frame = tk.Frame(header, bg=THEME["search_border"], padx=1, pady=1)
        search_frame.pack(fill=tk.X)

        search_inner = tk.Frame(search_frame, bg=THEME["search_bg"], padx=10, pady=6)
        search_inner.pack(fill=tk.X)

        tk.Label(search_inner, text="\U0001f50d", font=("Segoe UI Emoji", 12),
                 bg=THEME["search_bg"], fg=THEME["text_light"]).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())
        self.search_entry = tk.Entry(search_inner, textvariable=self.search_var,
                                     font=("Segoe UI", 11), border=0,
                                     bg=THEME["search_bg"], fg=THEME["text_dark"],
                                     insertbackground=THEME["primary"])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.search_entry.insert(0, "")
        self.search_entry.bind("<FocusIn>", lambda e: None)

        # Clear button
        self.clear_btn = tk.Label(search_inner, text="\u2715", font=("Segoe UI", 11),
                                  fg=THEME["text_light"], bg=THEME["search_bg"],
                                  cursor="hand2")
        self.clear_btn.pack(side=tk.RIGHT)
        self.clear_btn.bind("<Button-1>", lambda e: self._clear_search())

        # Separator
        tk.Frame(self, bg=THEME["card_border"], height=1).pack(fill=tk.X)

    def _build_category_bar(self):
        """Build the horizontal category filter buttons."""
        self.cat_bar = tk.Frame(self, bg=THEME["bg"], pady=10, padx=16)
        self.cat_bar.pack(fill=tk.X)

        self.cat_buttons = {}

        # Gather categories that actually have tools
        used_categories = set()
        for name, _ in self.tools:
            meta = self.config.get_tool_meta(name)
            used_categories.add(meta.get("category", "Other"))
            if meta.get("pinned"):
                used_categories.add("Pinned")

        ordered = ["All", "Pinned", "Productivity", "Language", "Documents", "Development", "Other"]
        for cat in ordered:
            if cat not in ("All",) and cat not in used_categories:
                if cat == "Pinned":
                    # Always show Pinned
                    pass
                elif cat not in used_categories:
                    continue

            fg_color, bg_color = CATEGORY_COLORS.get(cat, ("#6B7280", "#F3F4F6"))

            btn = tk.Label(self.cat_bar, text=f"  {cat}  ",
                           font=("Segoe UI", 9, "bold"),
                           fg=fg_color if cat != self.active_category else "#FFFFFF",
                           bg=bg_color if cat != self.active_category else fg_color,
                           padx=10, pady=4, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=(0, 6))
            btn.bind("<Button-1>", lambda e, c=cat: self._select_category(c))
            self.cat_buttons[cat] = btn

        self._highlight_active_category()

    def _build_tools_area(self):
        """Build the scrollable tools display area."""
        container = tk.Frame(self, bg=THEME["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 5))

        # Canvas for scrolling
        self.canvas = tk.Canvas(container, bg=THEME["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=THEME["bg"])

        self.scrollable_frame.bind("<Configure>",
                                   lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame,
                                                       anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Make canvas window fill width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _build_status_bar(self):
        """Build the bottom status bar."""
        self.status_bar = tk.Frame(self, bg=THEME["sidebar_bg"], padx=16, pady=6)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Frame(self, bg=THEME["card_border"], height=1).pack(fill=tk.X, side=tk.BOTTOM)

        self.status_left = tk.Label(self.status_bar, text="",
                                    font=("Segoe UI", 8), fg=THEME["text_light"],
                                    bg=THEME["sidebar_bg"])
        self.status_left.pack(side=tk.LEFT)

        self.status_right = tk.Label(self.status_bar, text="Ctrl+F: Search  |  Double-click: Run  |  Ctrl+R: Refresh",
                                     font=("Segoe UI", 8), fg=THEME["text_light"],
                                     bg=THEME["sidebar_bg"])
        self.status_right.pack(side=tk.RIGHT)

    # ──────────────────────────────────────────
    # LOGIC
    # ──────────────────────────────────────────
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _clear_search(self):
        self.search_var.set("")
        self.search_entry.focus_set()

    def _on_search(self):
        self.search_query = self.search_var.get().strip().lower()
        self.refresh_tools()

    def _select_category(self, category: str):
        self.active_category = category
        self._highlight_active_category()
        self.refresh_tools()

    def _highlight_active_category(self):
        for cat, btn in self.cat_buttons.items():
            fg_color, bg_color = CATEGORY_COLORS.get(cat, ("#6B7280", "#F3F4F6"))
            if cat == self.active_category:
                btn.configure(fg="#FFFFFF", bg=fg_color)
            else:
                btn.configure(fg=fg_color, bg=bg_color)

    def refresh_tools(self):
        """Rebuild tool cards based on current filters."""
        # Clear existing cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Filter tools
        filtered = []
        for name, path in self.tools:
            meta = self.config.get_tool_meta(name)

            # Category filter
            if self.active_category == "Pinned":
                if not meta.get("pinned"):
                    continue
            elif self.active_category != "All":
                if meta.get("category", "Other") != self.active_category:
                    continue

            # Search filter
            if self.search_query:
                searchable = f"{name} {meta.get('description', '')} {meta.get('category', '')}".lower()
                if self.search_query not in searchable:
                    continue

            filtered.append((name, path, meta))

        # Sort: pinned first, then alphabetical
        filtered.sort(key=lambda x: (not x[2].get("pinned", False), x[0].lower()))

        # Create cards
        if not filtered:
            no_result = tk.Label(self.scrollable_frame,
                                 text="\U0001f50d  No tools found matching your criteria",
                                 font=("Segoe UI", 12), fg=THEME["text_light"],
                                 bg=THEME["bg"], pady=40)
            no_result.pack(fill=tk.X)
        else:
            for name, path, meta in filtered:
                card = ToolCard(self.scrollable_frame,
                                tool_name=name,
                                script_path=path,
                                meta=meta,
                                on_run=self._run_tool,
                                on_pin_toggle=self._toggle_pin)
                card.pack(fill=tk.X, pady=(0, 8))

        # Update counts
        total = len(self.tools)
        shown = len(filtered)
        self.count_label.configure(text=f"{shown} of {total} tools")
        self.status_left.configure(text=f"Tools directory: {BASE_DIR}")

        # Reset scroll to top
        self.canvas.yview_moveto(0)

    def _run_tool(self, tool_name: str, script_path: Path):
        """Launch the selected tool in a separate process."""
        cwd = script_path.parent

        try:
            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Update last_used timestamp
            self.config.set_tool_meta(tool_name, "last_used", datetime.now().isoformat())

            # Brief visual feedback in status bar
            self.status_left.configure(text=f"\u2705 Launched: {tool_name}", fg=THEME["success"])
            self.after(3000, lambda: self.status_left.configure(
                text=f"Tools directory: {BASE_DIR}", fg=THEME["text_light"]))

            # Refresh to update last_used display
            self.refresh_tools()

        except FileNotFoundError:
            messagebox.showerror("File Not Found",
                                 f"Could not find:\n{script_path}\n\nDoes the file exist?")
        except PermissionError:
            messagebox.showerror("Permission Denied",
                                 f"No permission to execute:\n{script_path}")
        except Exception as exc:
            messagebox.showerror("Error Launching Tool",
                                 f"An unexpected error occurred:\n\n{exc}")

    def _toggle_pin(self, tool_name: str):
        """Toggle the pinned state of a tool."""
        meta = self.config.get_tool_meta(tool_name)
        new_state = not meta.get("pinned", False)
        self.config.set_tool_meta(tool_name, "pinned", new_state)
        self.refresh_tools()


# ══════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    app = ToolManagerApp()
    app.mainloop()