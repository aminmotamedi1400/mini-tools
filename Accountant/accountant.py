

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime, date

# try :
#     from ctypes import windll
#     windll.shcore.SetProcessDpiAwareness(1)
# except:
#     pass
# from ctypes import windll
# windll.shcore.SetProcessDpiAwareness(2)

class PersonalAccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.tk.call('tk', 'scaling', 1.5)
        self.root.title("Personal Accounting App")
        self.root.geometry("2000x1000")
        self.root.minsize(1000, 600)

        self.csv_file = './personal_accounting.csv'
        self.backup_dir = './backups'
        os.makedirs(self.backup_dir, exist_ok=True)

        self._setup_style()
        self.df = self._load_or_init_csv()
        self.filtered_df = self.df.copy()
        self.sort_state = {}  # column -> asc(True)/desc(False)

        # Menu
        self._build_menu()

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tabs
        self._build_dashboard_tab()
        self._build_transactions_tab()
        self._build_add_edit_tab()
        self._build_reports_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor='w', relief=tk.SUNKEN, padding=(8, 2))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Initial fill
        self._refresh_tree(self.df)
        self._update_dashboard()
        self._update_status()

    # ---------- Setup and Data ----------
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure('TButton', padding=6)
        style.configure('TLabel', padding=4)
        style.configure('Header.TLabel', font=('Segoe UI', 13, 'bold'))
        style.map("Treeview", background=[("selected", "#ececec")])
        style.configure("Treeview", rowheight=36, font=('Segoe UI', 20), padding=4)
        style.configure("Treeview.Heading", font=('Segoe UI', 24, 'bold'), padding=4)

    def _default_columns(self):
        return ['ID', 'Date', 'Type', 'Category', 'Description', 'Amount', 'Notes']

    def _load_or_init_csv(self):
        if not os.path.exists(self.csv_file):
            df = pd.DataFrame(columns=self._default_columns())
            df.to_csv(self.csv_file, index=False)
            return df

        try:
            df = pd.read_csv(self.csv_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")
            df = pd.DataFrame(columns=self._default_columns())

        # Upgrade older schema if needed
        cols = set(df.columns.tolist())
        if 'index' in cols and 'ID' not in cols:
            df = df.rename(columns={'index': 'ID'})
        # Ensure required columns exist
        for col in self._default_columns():
            if col not in df.columns:
                if col == 'ID':
                    continue
                df[col] = '' if col not in ['Amount', 'Date'] else (0.0 if col == 'Amount' else '')
        # Assign IDs if missing or NaN
        if 'ID' not in df.columns or df['ID'].isna().any():
            df['ID'] = range(1, len(df) + 1)
        # Dtypes and cleaning
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
        df['Amount'] = pd.to_numeric(df.get('Amount', 0), errors='coerce').fillna(0.0).astype(float)
        # Normalize Date to YYYY-MM-DD string
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['Date'] = df['Date'].fillna(date.today().strftime('%Y-%m-%d'))
        # Type defaults
        if 'Type' in df.columns:
            df['Type'] = df['Type'].replace('', pd.NA).fillna('Expense')
            df['Type'] = df['Type'].apply(lambda x: 'Income' if str(x).strip().lower() == 'income' else ('Expense' if str(x).strip().lower() == 'expense' else 'Expense'))
        # Category default
        if 'Category' in df.columns:
            df['Category'] = df['Category'].replace('', pd.NA).fillna('General')

        # Sort by ID to keep stable
        df = df.sort_values('ID').reset_index(drop=True)
        # Persist cleaned file
        df.to_csv(self.csv_file, index=False)
        return df

    def _save_df(self, make_backup=True):
        try:
            self.df.to_csv(self.csv_file, index=False, quoting=csv.QUOTE_MINIMAL)
            if make_backup:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(self.backup_dir, f'personal_accounting_{ts}.csv')
                self.df.to_csv(backup_path, index=False)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{e}")

    # ---------- Menu ----------
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Filtered to CSV...", command=self._export_filtered)
        file_menu.add_command(label="Backup Now", command=lambda: self._save_df(make_backup=True))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Delete Selected", command=self.delete_selected)
        edit_menu.add_command(label="Edit Selected", command=self.edit_selected)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Personal Accounting App (Upgraded)\nBy Zharph • Silicon Brain"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ---------- Dashboard Tab ----------
    def _build_dashboard_tab(self):
        self.dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard, text="Dashboard")

        hdr = ttk.Label(self.dashboard, text="Overview", style='Header.TLabel')
        hdr.pack(anchor='w', padx=6, pady=(6, 4))

        card_frame = ttk.Frame(self.dashboard)
        card_frame.pack(fill=tk.X, padx=6)

        self.lbl_total_income = ttk.Label(card_frame, text="Total Income: 0", foreground='green')
        self.lbl_total_expense = ttk.Label(card_frame, text="Total Expense: 0", foreground='firebrick')
        self.lbl_balance = ttk.Label(card_frame, text="Balance: 0", foreground='blue')
        self.lbl_this_month = ttk.Label(card_frame, text="This Month - I: 0 | E: 0 | B: 0")

        for i, w in enumerate([self.lbl_total_income, self.lbl_total_expense, self.lbl_balance, self.lbl_this_month]):
            w.grid(row=0, column=i, sticky='w', padx=10, pady=8)

        btns = ttk.Frame(self.dashboard)
        btns.pack(anchor='w', padx=6, pady=6)
        ttk.Button(btns, text="Export Current Month Report", command=self._export_current_month_report).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Backup Now", command=lambda: self._save_df(make_backup=True)).pack(side=tk.LEFT, padx=4)

        tip = ttk.Label(self.dashboard, text="Tip: Double-click a row in Transactions to edit it quickly.", foreground='#555')
        tip.pack(anchor='w', padx=8, pady=4)

    def _update_dashboard(self):
        if self.df.empty:
            total_income = total_expense = balance = 0.0
            m_income = m_expense = m_balance = 0.0
        else:
            income_sum = self.df.loc[self.df['Type'] == 'Income', 'Amount'].sum()
            expense_sum = self.df.loc[self.df['Type'] == 'Expense', 'Amount'].sum()
            total_income = float(income_sum)
            total_expense = float(expense_sum)
            balance = total_income - total_expense

            today = date.today()
            month_mask = pd.to_datetime(self.df['Date'], errors='coerce').dt.to_period('M') == pd.Period(today.strftime('%Y-%m'))
            mdf = self.df[month_mask]
            m_income = float(mdf.loc[mdf['Type'] == 'Income', 'Amount'].sum())
            m_expense = float(mdf.loc[mdf['Type'] == 'Expense', 'Amount'].sum())
            m_balance = m_income - m_expense

        self.lbl_total_income.config(text=f"Total Income: {total_income:,.2f}")
        self.lbl_total_expense.config(text=f"Total Expense: {total_expense:,.2f}")
        self.lbl_balance.config(text=f"Balance: {balance:,.2f}")
        self.lbl_this_month.config(text=f"This Month - I: {m_income:,.2f} | E: {m_expense:,.2f} | B: {m_balance:,.2f}")

    # ---------- Transactions Tab ----------
    def _build_transactions_tab(self):
        self.view_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.view_tab, text="Transactions")

        # Filters
        filter_frame = ttk.LabelFrame(self.view_tab, text="Filters")
        filter_frame.pack(fill=tk.X, padx=6, pady=6)

        self.search_text = tk.StringVar()
        self.filter_type = tk.StringVar(value='All')
        self.filter_category = tk.StringVar(value='All')
        self.filter_date_from = tk.StringVar()
        self.filter_date_to = tk.StringVar()
        self.filter_amount_min = tk.StringVar()
        self.filter_amount_max = tk.StringVar()

        # Row 1
        ttk.Label(filter_frame, text="Text:").grid(row=0, column=0, sticky='e', padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self.search_text, width=18).grid(row=0, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(filter_frame, text="Type:").grid(row=0, column=2, sticky='e', padx=4, pady=4)
        ttk.Combobox(filter_frame, textvariable=self.filter_type, values=['All', 'Income', 'Expense'], width=12, state='readonly').grid(row=0, column=3, sticky='w', padx=4, pady=4)
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, sticky='e', padx=4, pady=4)
        cat_values = ['All'] + sorted([c for c in self.df['Category'].dropna().unique().tolist() if str(c).strip() != ''])
        self.category_filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category, values=cat_values, width=16, state='readonly')
        self.category_filter_combo.grid(row=0, column=5, sticky='w', padx=4, pady=4)

        # Row 2
        ttk.Label(filter_frame, text="Date From (YYYY-MM-DD):").grid(row=1, column=0, sticky='e', padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self.filter_date_from, width=18).grid(row=1, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(filter_frame, text="Date To:").grid(row=1, column=2, sticky='e', padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self.filter_date_to, width=18).grid(row=1, column=3, sticky='w', padx=4, pady=4)
        ttk.Label(filter_frame, text="Amount Min:").grid(row=1, column=4, sticky='e', padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self.filter_amount_min, width=10).grid(row=1, column=5, sticky='w', padx=4, pady=4)
        ttk.Label(filter_frame, text="Amount Max:").grid(row=1, column=6, sticky='e', padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self.filter_amount_max, width=10).grid(row=1, column=7, sticky='w', padx=4, pady=4)

        # Buttons
        ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).grid(row=0, column=6, sticky='w', padx=4, pady=4)
        ttk.Button(filter_frame, text="Clear", command=self.clear_filters).grid(row=0, column=7, sticky='w', padx=4, pady=4)

        for i in range(8):
            filter_frame.grid_columnconfigure(i, weight=0)
        filter_frame.grid_columnconfigure(8, weight=1)

        # Treeview
        tree_frame = ttk.Frame(self.view_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        columns = ('ID', 'Date', 'Type', 'Category', 'Description', 'Amount', 'Notes')
        self.view_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.view_tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            anchor = 'e' if col in ['Amount', 'ID'] else 'w'
            width = 90 if col in ['ID', 'Type', 'Date'] else (120 if col in ['Amount', 'Category'] else 240)
            self.view_tree.column(col, anchor=anchor, width=width, stretch=True)
        self.view_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tags for coloring
        self.view_tree.tag_configure('income', foreground='green')
        self.view_tree.tag_configure('expense', foreground='firebrick')
        self.view_tree.tag_configure('oddrow', background='#f7f7f7')

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.view_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.view_tree.xview)
        self.view_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Buttons under tree
        btns = ttk.Frame(self.view_tab)
        btns.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Export Filtered...", command=self._export_filtered).pack(side=tk.LEFT, padx=4)

        self.view_tree.bind("<Double-1>", lambda e: self.edit_selected())

    def _refresh_tree(self, df):
        for item in self.view_tree.get_children():
            self.view_tree.delete(item)
        if df is None or df.empty:
            self._update_status()
            return
        # Insert with tags
        for i, row in df.iterrows():
            tags = []
            tags.append('income' if row['Type'] == 'Income' else 'expense')
            if i % 2 == 1:
                tags.append('oddrow')
            vals = (
                int(row['ID']),
                row['Date'],
                row['Type'],
                row['Category'],
                row['Description'],
                f"{float(row['Amount']):,.2f}",
                row.get('Notes', '')
            )
            self.view_tree.insert('', 'end', values=vals, tags=tuple(tags))
        self._update_status()

    def _sort_by(self, column):
        if self.filtered_df.empty:
            return
        asc = self.sort_state.get(column, True)
        key_map = {
            'ID': lambda s: pd.to_numeric(s, errors='coerce'),
            'Amount': lambda s: pd.to_numeric(s, errors='coerce'),
            'Date': lambda s: pd.to_datetime(s, errors='coerce')
        }
        key_func = key_map.get(column, None)
        try:
            if key_func:
                self.filtered_df = self.filtered_df.sort_values(by=column, key=key_func, ascending=asc)
            else:
                self.filtered_df = self.filtered_df.sort_values(by=column, ascending=asc)
        except Exception:
            pass
        self.sort_state[column] = not asc
        self._refresh_tree(self.filtered_df)

    # ---------- Add/Edit Tab ----------
    def _build_add_edit_tab(self):
        self.edit_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.edit_tab, text="Add / Edit")

        frm = ttk.Frame(self.edit_tab)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Variables
        self.var_id = tk.StringVar()
        self.var_date = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        self.var_type = tk.StringVar(value='Expense')
        self.var_category = tk.StringVar()
        self.var_description = tk.StringVar()
        self.var_amount = tk.StringVar()
        self.var_notes = tk.StringVar()

        # Form layout
        row = 0
        ttk.Label(frm, text="ID (selected):").grid(row=row, column=0, sticky='e', padx=6, pady=6)
        ttk.Label(frm, textvariable=self.var_id, foreground='#666').grid(row=row, column=1, sticky='w', padx=6, pady=6)

        row += 1
        ttk.Label(frm, text="Date (YYYY-MM-DD):").grid(row=row, column=0, sticky='e', padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_date, width=20).grid(row=row, column=1, sticky='w', padx=6, pady=6)

        ttk.Label(frm, text="Type:").grid(row=row, column=2, sticky='e', padx=6, pady=6)
        ttk.Combobox(frm, textvariable=self.var_type, values=['Income', 'Expense'], state='readonly', width=18).grid(row=row, column=3, sticky='w', padx=6, pady=6)

        row += 1
        ttk.Label(frm, text="Category:").grid(row=row, column=0, sticky='e', padx=6, pady=6)
        cat_values = sorted([c for c in self.df['Category'].dropna().unique().tolist() if str(c).strip() != ''])
        self.category_combo = ttk.Combobox(frm, textvariable=self.var_category, values=cat_values, width=22)
        self.category_combo.grid(row=row, column=1, sticky='w', padx=6, pady=6)

        ttk.Label(frm, text="Amount:").grid(row=row, column=2, sticky='e', padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_amount, width=20).grid(row=row, column=3, sticky='w', padx=6, pady=6)

        row += 1
        ttk.Label(frm, text="Description:").grid(row=row, column=0, sticky='e', padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_description, width=50).grid(row=row, column=1, columnspan=3, sticky='w', padx=6, pady=6)

        row += 1
        ttk.Label(frm, text="Notes:").grid(row=row, column=0, sticky='e', padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_notes, width=50).grid(row=row, column=1, columnspan=3, sticky='w', padx=6, pady=6)

        # Buttons
        row += 1
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=4, sticky='w', pady=10)
        ttk.Button(btns, text="Save New", command=self.save_record).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Update Selected", command=self.update_record).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=4)

        for c in range(4):
            frm.grid_columnconfigure(c, weight=1)

    def clear_form(self):
        self.var_id.set('')
        self.var_date.set(date.today().strftime('%Y-%m-%d'))
        self.var_type.set('Expense')
        self.var_category.set('')
        self.var_description.set('')
        self.var_amount.set('')
        self.var_notes.set('')

    # ---------- Reports Tab ----------
    def _build_reports_tab(self):
        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="Reports")

        lbl = ttk.Label(self.reports_tab, text="Quick Report: Totals by Category (All Time)", style='Header.TLabel')
        lbl.pack(anchor='w', padx=8, pady=(8, 6))

        self.report_tree = ttk.Treeview(self.reports_tab, columns=('Category', 'Income', 'Expense', 'Net'), show='headings', height=12)
        for col in ('Category', 'Income', 'Expense', 'Net'):
            anchor = 'e' if col in ['Income', 'Expense', 'Net'] else 'w'
            width = 180 if col == 'Category' else 120
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, anchor=anchor, width=width, stretch=False)
        self.report_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        ttk.Button(self.reports_tab, text="Refresh Report", command=self._refresh_report).pack(anchor='w', padx=8, pady=4)
        ttk.Button(self.reports_tab, text="Export Report to CSV...", command=self._export_report).pack(anchor='w', padx=8, pady=4)

        self._refresh_report()

    def _refresh_report(self):
        for i in self.report_tree.get_children():
            self.report_tree.delete(i)
        if self.df.empty:
            return
        cats = sorted(self.df['Category'].dropna().unique())
        for cat in cats:
            sub = self.df[self.df['Category'] == cat]
            inc = float(sub.loc[sub['Type'] == 'Income', 'Amount'].sum())
            exp = float(sub.loc[sub['Type'] == 'Expense', 'Amount'].sum())
            net = inc - exp
            self.report_tree.insert('', 'end', values=(cat, f"{inc:,.2f}", f"{exp:,.2f}", f"{net:,.2f}"))

    # ---------- Actions ----------
    def _parse_date(self, s):
        try:
            return datetime.strptime(s.strip(), '%Y-%m-%d').date()
        except Exception:
            return None

    def _validate_form(self, for_update=False):
        d = self._parse_date(self.var_date.get())
        if not d:
            messagebox.showwarning("Invalid Date", "Please enter date as YYYY-MM-DD.")
            return False
        t = self.var_type.get().strip()
        if t not in ['Income', 'Expense']:
            messagebox.showwarning("Invalid Type", "Type must be Income or Expense.")
            return False
        try:
            amt = float(str(self.var_amount.get()).replace(',', '').strip())
            if amt < 0:
                messagebox.showwarning("Invalid Amount", "Enter a positive amount. Type controls income/expense.")
                return False
        except:
            messagebox.showwarning("Invalid Amount", "Amount must be a number.")
            return False
        if for_update and not self.var_id.get():
            messagebox.showwarning("No Selection", "Select a row to update (double-click in Transactions or use Edit Selected).")
            return False
        return True

    def save_record(self):
        if not self._validate_form(for_update=False):
            return
        next_id = (self.df['ID'].max() + 1) if not self.df.empty else 1
        row = {
            'ID': int(next_id),
            'Date': self._parse_date(self.var_date.get()).strftime('%Y-%m-%d'),
            'Type': self.var_type.get().strip(),
            'Category': self.var_category.get().strip() or 'General',
            'Description': self.var_description.get().strip(),
            'Amount': float(str(self.var_amount.get()).replace(',', '').strip()),
            'Notes': self.var_notes.get().strip()
        }
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        self._save_df(make_backup=True)
        self.clear_form()
        self.apply_filters()  # refreshes tree using current filters
        self._update_dashboard()
        self._refresh_report()
        # update category combos
        self._refresh_category_values()
        messagebox.showinfo("Saved", "Record saved successfully.")

    def update_record(self):
        if not self._validate_form(for_update=True):
            return
        rid = int(self.var_id.get())
        idx = self.df.index[self.df['ID'] == rid]
        if len(idx) == 0:
            messagebox.showerror("Not Found", "Selected ID not found.")
            return
        i = idx[0]
        self.df.at[i, 'Date'] = self._parse_date(self.var_date.get()).strftime('%Y-%m-%d')
        self.df.at[i, 'Type'] = self.var_type.get().strip()
        self.df.at[i, 'Category'] = self.var_category.get().strip() or 'General'
        self.df.at[i, 'Description'] = self.var_description.get().strip()
        self.df.at[i, 'Amount'] = float(str(self.var_amount.get()).replace(',', '').strip())
        self.df.at[i, 'Notes'] = self.var_notes.get().strip()

        self._save_df(make_backup=True)
        self.apply_filters()
        self._update_dashboard()
        self._refresh_report()
        self._refresh_category_values()
        messagebox.showinfo("Updated", "Record updated successfully.")

    def delete_selected(self):
        sel = self.view_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a row in Transactions.")
            return
        vals = self.view_tree.item(sel[0], 'values')
        rid = int(vals[0])
        if messagebox.askyesno("Confirm Delete", f"Delete record ID {rid}?"):
            idx = self.df.index[self.df['ID'] == rid]
            if len(idx) == 0:
                messagebox.showerror("Not Found", "Selected ID not found.")
                return
            self.df = self.df.drop(index=idx).reset_index(drop=True)
            self._save_df(make_backup=True)
            self.apply_filters()
            self._update_dashboard()
            self._refresh_report()
            messagebox.showinfo("Deleted", "Record deleted.")

    def edit_selected(self):
        sel = self.view_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a row in Transactions.")
            return
        vals = self.view_tree.item(sel[0], 'values')
        rid = int(vals[0])
        row = self.df[self.df['ID'] == rid].iloc[0]
        self.var_id.set(str(int(row['ID'])))
        self.var_date.set(row['Date'])
        self.var_type.set(row['Type'])
        self.var_category.set(row['Category'])
        self.var_description.set(row['Description'])
        self.var_amount.set(str(float(row['Amount'])))
        self.var_notes.set(row.get('Notes', ''))
        self.notebook.select(self.edit_tab)

    def _refresh_category_values(self):
        cats = sorted([c for c in self.df['Category'].dropna().unique().tolist() if str(c).strip() != ''])
        self.category_combo['values'] = cats
        self.category_filter_combo['values'] = ['All'] + cats

    # ---------- Filtering ----------
    def apply_filters(self):
        df = self.df.copy()
        txt = self.search_text.get().strip().lower()
        if txt:
            df = df[df.apply(lambda r: txt in str(r['Description']).lower() or
                                       txt in str(r['Category']).lower() or
                                       txt in str(r['Notes']).lower(), axis=1)]
        t = self.filter_type.get()
        if t in ['Income', 'Expense']:
            df = df[df['Type'] == t]
        cat = self.filter_category.get()
        if cat not in ['', 'All']:
            df = df[df['Category'] == cat]

        df['Date_dt'] = pd.to_datetime(df['Date'], errors='coerce')
        dfrom = self._parse_date(self.filter_date_from.get()) if self.filter_date_from.get().strip() else None
        dto = self._parse_date(self.filter_date_to.get()) if self.filter_date_to.get().strip() else None
        if dfrom:
            df = df[df['Date_dt'] >= pd.Timestamp(dfrom)]
        if dto:
            df = df[df['Date_dt'] <= pd.Timestamp(dto)]

        try:
            amin = float(self.filter_amount_min.get().strip()) if self.filter_amount_min.get().strip() else None
        except:
            messagebox.showwarning("Invalid Amount Min", "Amount Min must be a number.")
            return
        try:
            amax = float(self.filter_amount_max.get().strip()) if self.filter_amount_max.get().strip() else None
        except:
            messagebox.showwarning("Invalid Amount Max", "Amount Max must be a number.")
            return
        if amin is not None:
            df = df[df['Amount'] >= amin]
        if amax is not None:
            df = df[df['Amount'] <= amax]

        df = df.drop(columns=['Date_dt'], errors='ignore')
        self.filtered_df = df
        self._refresh_tree(df)

    def clear_filters(self):
        self.search_text.set('')
        self.filter_type.set('All')
        self.filter_category.set('All')
        self.filter_date_from.set('')
        self.filter_date_to.set('')
        self.filter_amount_min.set('')
        self.filter_amount_max.set('')
        self.filtered_df = self.df.copy()
        self._refresh_tree(self.df)

    # ---------- Status and Export ----------
    def _update_status(self):
        count = len(self.filtered_df) if self.filtered_df is not None else 0
        total_income = float(self.filtered_df.loc[self.filtered_df['Type'] == 'Income', 'Amount'].sum()) if count else 0.0
        total_expense = float(self.filtered_df.loc[self.filtered_df['Type'] == 'Expense', 'Amount'].sum()) if count else 0.0
        balance = total_income - total_expense
        self.status_var.set(f"Rows: {count} | Income: {total_income:,.2f} | Expense: {total_expense:,.2f} | Balance: {balance:,.2f}")

    def _export_filtered(self):
        if self.filtered_df is None or self.filtered_df.empty:
            messagebox.showwarning("No Data", "Nothing to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title='Export CSV')
        if not path:
            return
        try:
            self.filtered_df.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Exported {len(self.filtered_df)} rows to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_report(self):
        if self.df.empty:
            messagebox.showwarning("No Data", "No data to export.")
            return
        # Create a report DataFrame
        rows = []
        cats = sorted(self.df['Category'].dropna().unique())
        for cat in cats:
            sub = self.df[self.df['Category'] == cat]
            inc = float(sub.loc[sub['Type'] == 'Income', 'Amount'].sum())
            exp = float(sub.loc[sub['Type'] == 'Expense', 'Amount'].sum())
            rows.append({'Category': cat, 'Income': inc, 'Expense': exp, 'Net': inc - exp})
        rpt = pd.DataFrame(rows)
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title='Export Report CSV')
        if not path:
            return
        try:
            rpt.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Report exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_current_month_report(self):
        if self.df.empty:
            messagebox.showwarning("No Data", "No data to export.")
            return
        today = date.today()
        period = today.strftime('%Y-%m')
        mask = pd.to_datetime(self.df['Date'], errors='coerce').dt.to_period('M') == pd.Period(period)
        mdf = self.df[mask]
        if mdf.empty:
            messagebox.showinfo("No Data", "No transactions this month.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], initialfile=f'monthly_{period}.csv', title='Export Current Month CSV')
        if not path:
            return
        try:
            mdf.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Exported {len(mdf)} rows for {period} to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalAccountingApp(root)
    root.mainloop()
