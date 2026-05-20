import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import uuid
from datetime import date, datetime, timedelta
import csv

DATA_FILE = "shopping_data.json"

FREQUENCIES = ["Weekly", "Monthly", "Yearly"]
CATEGORIES = ["Home", "Life", "Kitchen", "Cleaning", "Bills", "Maintenance", "Healthcare", "Education", "Transport", "Subscriptions", "Other"]

def today():
    return date.today()

def format_date(d: date | None) -> str:
    return d.strftime("%Y-%m-%d") if d else ""

def parse_date(s: str) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def add_months(d: date, months: int) -> date:
    # naive month add
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # clamp day
    days_in_month = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(d.day, days_in_month[m - 1])
    return date(y, m, day)

def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # handle Feb 29 -> Feb 28
        return d.replace(month=2, day=28, year=d.year + years)

def next_due_from(last_purchased: date | None, freq: str) -> date:
    base = last_purchased or today()
    if freq == "Weekly":
        return base + timedelta(days=7)
    if freq == "Monthly":
        return add_months(base, 1)
    if freq == "Yearly":
        return add_years(base, 1)
    return base

class ShoppingManager:
    def __init__(self, path: str):
        self.path = path
        self.items: list[dict] = []
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.items = self._default_items()
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.items = json.load(f)
        except Exception:
            self.items = self._default_items()
        # ensure fields and recompute if needed
        changed = False
        for it in self.items:
            it.setdefault("id", str(uuid.uuid4()))
            it.setdefault("name", "")
            it.setdefault("category", "Home")
            it.setdefault("frequency", "Monthly")
            it.setdefault("quantity", 1.0)
            it.setdefault("unit", "")
            it.setdefault("notes", "")
            it.setdefault("last_purchased", None)
            it.setdefault("next_due", None)
            it.setdefault("active", True)
            # coerce types
            if isinstance(it.get("quantity"), str):
                try:
                    it["quantity"] = float(it["quantity"])
                except Exception:
                    it["quantity"] = 1.0
            # parse dates
            lp = parse_date(it.get("last_purchased") or "")
            nd = parse_date(it.get("next_due") or "")
            # recompute next_due if missing or invalid
            nd2 = next_due_from(lp, it.get("frequency", "Monthly"))
            if nd != nd2:
                it["next_due"] = format_date(nd2)
                changed = True
            else:
                it["next_due"] = format_date(nd2)
            it["last_purchased"] = format_date(lp) if lp else None
        if changed:
            self.save()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Save error:", e)

    def _default_items(self):
        sample = [
            {
                "id": str(uuid.uuid4()),
                "name": "Milk",
                "category": "Kitchen",
                "frequency": "Weekly",
                "quantity": 2,
                "unit": "liters",
                "notes": "Low fat",
                "last_purchased": format_date(today() - timedelta(days=5)),
                "next_due": None,
                "active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Electricity Bill",
                "category": "Bills",
                "frequency": "Monthly",
                "quantity": 1,
                "unit": "bill",
                "notes": "",
                "last_purchased": format_date(today().replace(day=1)),
                "next_due": None,
                "active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Car Insurance",
                "category": "Transport",
                "frequency": "Yearly",
                "quantity": 1,
                "unit": "policy",
                "notes": "Renew on time",
                "last_purchased": format_date(add_years(today(), -1)),
                "next_due": None,
                "active": True,
            },
        ]
        # fill next_due
        for it in sample:
            lp = parse_date(it["last_purchased"])
            it["next_due"] = format_date(next_due_from(lp, it["frequency"]))
        return sample

    def add_item(self, data: dict):
        data["id"] = str(uuid.uuid4())
        lp = parse_date(data.get("last_purchased") or "")
        data["last_purchased"] = format_date(lp) if lp else None
        data["next_due"] = format_date(next_due_from(lp, data.get("frequency", "Monthly")))
        data["active"] = True
        self.items.append(data)
        self.save()
        return data

    def update_item(self, item_id: str, data: dict):
        for it in self.items:
            if it["id"] == item_id:
                it.update({
                    "name": data.get("name", it["name"]),
                    "category": data.get("category", it["category"]),
                    "frequency": data.get("frequency", it["frequency"]),
                    "quantity": float(data.get("quantity", it["quantity"])),
                    "unit": data.get("unit", it["unit"]),
                    "notes": data.get("notes", it["notes"]),
                })
                lp = parse_date(data.get("last_purchased") or it.get("last_purchased") or "")
                it["last_purchased"] = format_date(lp) if lp else None
                it["next_due"] = format_date(next_due_from(lp, it["frequency"]))
                self.save()
                return it
        return None

    def delete_items(self, ids: list[str]):
        before = len(self.items)
        self.items = [it for it in self.items if it["id"] not in ids]
        if len(self.items) != before:
            self.save()

    def mark_purchased(self, ids: list[str], when: date | None = None):
        when = when or today()
        for it in self.items:
            if it["id"] in ids:
                it["last_purchased"] = format_date(when)
                it["next_due"] = format_date(next_due_from(when, it["frequency"]))
        self.save()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shopping Management - Weekly / Monthly / Yearly")
        self.geometry("1100x650")
        self.minsize(980, 580)

        self.manager = ShoppingManager(DATA_FILE)
        self.sort_state = {"col": None, "reverse": False}

        self._build_ui()
        self._refresh_tree()

    def _build_ui(self):
        # Top: Form
        form = ttk.LabelFrame(self, text="Add / Edit Item")
        form.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8, ipady=4)

        r = 0
        ttk.Label(form, text="Name").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        self.var_name = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_name, width=28).grid(row=r, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Category").grid(row=r, column=2, sticky="w", padx=6, pady=4)
        self.var_category = tk.StringVar(value="Home")
        self.cb_category = ttk.Combobox(form, textvariable=self.var_category, values=CATEGORIES, width=20)
        self.cb_category.grid(row=r, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Frequency").grid(row=r, column=4, sticky="w", padx=6, pady=4)
        self.var_freq = tk.StringVar(value="Monthly")
        self.cb_freq = ttk.Combobox(form, textvariable=self.var_freq, values=FREQUENCIES, width=14, state="readonly")
        self.cb_freq.grid(row=r, column=5, sticky="w", padx=6, pady=4)

        r += 1
        ttk.Label(form, text="Quantity").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        self.var_qty = tk.DoubleVar(value=1.0)
        self.sp_qty = ttk.Spinbox(form, from_=0, to=100000, increment=1, textvariable=self.var_qty, width=10)
        self.sp_qty.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Unit").grid(row=r, column=2, sticky="w", padx=6, pady=4)
        self.var_unit = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_unit, width=20).grid(row=r, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Last Purchased (YYYY-MM-DD)").grid(row=r, column=4, sticky="w", padx=6, pady=4)
        self.var_last = tk.StringVar(value=format_date(today()))
        ttk.Entry(form, textvariable=self.var_last, width=16).grid(row=r, column=5, sticky="w", padx=6, pady=4)

        r += 1
        ttk.Label(form, text="Notes").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        self.var_notes = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_notes, width=60).grid(row=r, column=1, columnspan=3, sticky="we", padx=6, pady=4)

        self.btn_add = ttk.Button(form, text="Add Item", command=self.on_add)
        self.btn_add.grid(row=r, column=4, padx=6, pady=4, sticky="e")

        self.btn_update = ttk.Button(form, text="Update Selected", command=self.on_update, state="disabled")
        self.btn_update.grid(row=r, column=5, padx=6, pady=4, sticky="w")

        # Middle: Filters and actions
        filt = ttk.LabelFrame(self, text="Search / Filter")
        filt.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)

        ttk.Label(filt, text="Search").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.var_search = tk.StringVar()
        ent_search = ttk.Entry(filt, textvariable=self.var_search, width=30)
        ent_search.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ent_search.bind("<KeyRelease>", lambda e: self._refresh_tree())

        ttk.Label(filt, text="Category").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        self.var_fcat = tk.StringVar(value="All")
        cb_fcat = ttk.Combobox(filt, textvariable=self.var_fcat, values=["All"] + CATEGORIES, width=18, state="readonly")
        cb_fcat.grid(row=0, column=3, sticky="w", padx=6, pady=4)
        cb_fcat.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())

        ttk.Label(filt, text="Frequency").grid(row=0, column=4, sticky="w", padx=6, pady=4)
        self.var_ffreq = tk.StringVar(value="All")
        cb_ffreq = ttk.Combobox(filt, textvariable=self.var_ffreq, values=["All"] + FREQUENCIES, width=14, state="readonly")
        cb_ffreq.grid(row=0, column=5, sticky="w", padx=6, pady=4)
        cb_ffreq.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())

        self.var_due_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(filt, text="Show due only (today or overdue)", variable=self.var_due_only, command=self._refresh_tree).grid(row=0, column=6, padx=10, pady=4)

        # Actions
        act = ttk.Frame(self)
        act.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)
        ttk.Button(act, text="Mark Purchased Today", command=self.on_mark_purchased).pack(side=tk.LEFT, padx=4)
        ttk.Button(act, text="Delete Selected", command=self.on_delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(act, text="Export CSV", command=self.on_export_csv).pack(side=tk.LEFT, padx=4)
        ttk.Button(act, text="Reload", command=self._reload).pack(side=tk.LEFT, padx=4)

        # Treeview
        tvf = ttk.Frame(self)
        tvf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=4)

        columns = ("name", "category", "frequency", "quantity", "unit", "last_purchased", "next_due", "days_left", "notes")
        self.tree = ttk.Treeview(tvf, columns=columns, show="headings", selectmode="extended")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hs = ttk.Scrollbar(tvf, orient="horizontal", command=self.tree.xview)
        vs = ttk.Scrollbar(tvf, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        hs.pack(side=tk.BOTTOM, fill=tk.X)

        headings = {
            "name": "Name",
            "category": "Category",
            "frequency": "Frequency",
            "quantity": "Qty",
            "unit": "Unit",
            "last_purchased": "Last Purchased",
            "next_due": "Next Due",
            "days_left": "Days Left",
            "notes": "Notes",
        }
        widths = {
            "name": 170, "category": 110, "frequency": 100, "quantity": 60, "unit": 70,
            "last_purchased": 110, "next_due": 100, "days_left": 80, "notes": 240
        }
        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths[col], anchor="w")

        # Row tags for coloring
        self.tree.tag_configure("overdue", background="#ffd8d8")
        self.tree.tag_configure("due_soon", background="#fff4cc")
        self.tree.tag_configure("ok", background="#eaffea")

        self.tree.bind("<<TreeviewSelect>>", self._on_select_change)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Footer info
        self.var_status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.var_status).pack(side=tk.BOTTOM, anchor="w", padx=12, pady=6)

    def _reload(self):
        self.manager.load()
        self._refresh_tree()

    def _on_select_change(self, event=None):
        sel = self.tree.selection()
        self.btn_update.configure(state="normal" if len(sel) == 1 else "disabled")

    def _on_double_click(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        item = self.tree.item(iid, "values")
        # Fill form
        self.var_name.set(item[0])
        self.var_category.set(item[1])
        self.var_freq.set(item[2])
        try:
            self.var_qty.set(float(item[3]))
        except Exception:
            self.var_qty.set(1.0)
        self.var_unit.set(item[4])
        self.var_last.set(item[5])
        self.var_notes.set(item[8])

    def _gather_form(self):
        name = self.var_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return None
        freq = self.var_freq.get()
        if freq not in FREQUENCIES:
            messagebox.showwarning("Validation", "Select a valid frequency.")
            return None
        lp_str = self.var_last.get().strip()
        if lp_str:
            lp = parse_date(lp_str)
            if not lp:
                messagebox.showwarning("Validation", "Last Purchased date must be YYYY-MM-DD.")
                return None
        data = {
            "name": name,
            "category": (self.var_category.get() or "Other").strip() or "Other",
            "frequency": freq,
            "quantity": float(self.var_qty.get() or 1.0),
            "unit": self.var_unit.get().strip(),
            "notes": self.var_notes.get().strip(),
            "last_purchased": lp_str if lp_str else None,
        }
        return data

    def on_add(self):
        data = self._gather_form()
        if not data:
            return
        self.manager.add_item(data)
        self._refresh_tree()
        self._clear_form()

    def on_update(self):
        sel = self.tree.selection()
        if len(sel) != 1:
            messagebox.showinfo("Update", "Select exactly one item to update.")
            return
        data = self._gather_form()
        if not data:
            return
        item_id = self.tree.set(sel[0], "name_id") if "name_id" in self.tree["columns"] else self.tree.item(sel[0], "text")
        # We stored the real id in iid map; use hidden value in tags via self._iid_to_id
        item_id = self.tree.set(sel[0], "name")  # temporary placeholder, will map below
        # Proper way: store item id in iid itself
        iid = sel[0]
        real_id = iid  # we set iid as item id when inserting
        updated = self.manager.update_item(real_id, data)
        if not updated:
            messagebox.showerror("Update", "Failed to update item.")
            return
        self._refresh_tree()

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "No items selected.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(sel)} selected item(s)?"):
            return
        ids = list(sel)  # we use iid as id
        self.manager.delete_items(ids)
        self._refresh_tree()

    def on_mark_purchased(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Mark Purchased", "Select items to mark as purchased.")
            return
        self.manager.mark_purchased(list(sel), when=today())
        self._refresh_tree()

    def on_export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="shopping_export.csv")
        if not path:
            return
        cols = ["id", "name", "category", "frequency", "quantity", "unit", "last_purchased", "next_due", "notes"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                for it in self.manager.items:
                    w.writerow({k: it.get(k, "") for k in cols})
            messagebox.showinfo("Export", f"Exported {len(self.manager.items)} items.")
        except Exception as e:
            messagebox.showerror("Export", f"Failed to export:\n{e}")

    def _passes_filters(self, it: dict) -> bool:
        q = self.var_search.get().strip().lower()
        if q:
            hay = " ".join([
                it.get("name", ""),
                it.get("category", ""),
                it.get("frequency", ""),
                it.get("unit", ""),
                it.get("notes", "")
            ]).lower()
            if q not in hay:
                return False
        fc = self.var_fcat.get()
        if fc != "All" and it.get("category") != fc:
            return False
        ff = self.var_ffreq.get()
        if ff != "All" and it.get("frequency") != ff:
            return False
        if self.var_due_only.get():
            nd = parse_date(it.get("next_due") or "")
            if not nd:
                return False
            if nd > today():
                return False
        return True

    def _row_tag_for(self, it: dict) -> str:
        nd = parse_date(it.get("next_due") or "")
        if not nd:
            return "ok"
        delta = (nd - today()).days
        if delta < 0:
            return "overdue"
        if delta <= 3:
            return "due_soon"
        return "ok"

    def _days_left(self, it: dict) -> str:
        nd = parse_date(it.get("next_due") or "")
        if not nd:
            return ""
        return str((nd - today()).days)

    def _refresh_tree(self):
        # keep selection
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        shown = 0
        for it in self.manager.items:
            if not self._passes_filters(it):
                continue
            vals = (
                it.get("name", ""),
                it.get("category", ""),
                it.get("frequency", ""),
                str(it.get("quantity", "")),
                it.get("unit", ""),
                it.get("last_purchased", "") or "",
                it.get("next_due", "") or "",
                self._days_left(it),
                it.get("notes", ""),
            )
            iid = it["id"]  # use persistent id as iid
            tag = self._row_tag_for(it)
            self.tree.insert("", "end", iid=iid, values=vals, tags=(tag,))
            shown += 1
            if iid in selected:
                self.tree.selection_add(iid)
        total = len(self.manager.items)
        self.var_status.set(f"Showing {shown} of {total} items")
        self._on_select_change()

    def _clear_form(self):
        self.var_name.set("")
        self.var_category.set("Home")
        self.var_freq.set("Monthly")
        self.var_qty.set(1.0)
        self.var_unit.set("")
        self.var_last.set(format_date(today()))
        self.var_notes.set("")
        self.btn_update.configure(state="disabled")

    def _sort_by(self, col: str):
        # Map displayed col to key
        def keyfunc(item: dict):
            if col == "name":
                return item.get("name", "").lower()
            if col == "category":
                return item.get("category", "").lower()
            if col == "frequency":
                order = {f: i for i, f in enumerate(FREQUENCIES)}
                return order.get(item.get("frequency", ""), 999)
            if col == "quantity":
                try:
                    return float(item.get("quantity", 0))
                except Exception:
                    return 0
            if col == "unit":
                return (item.get("unit", "") or "").lower()
            if col == "last_purchased":
                d = parse_date(item.get("last_purchased") or "")
                return d or date.min
            if col == "next_due":
                d = parse_date(item.get("next_due") or "")
                return d or date.max
            if col == "days_left":
                nd = parse_date(item.get("next_due") or "")
                return (nd - today()).days if nd else 10**9
            if col == "notes":
                return (item.get("notes", "") or "").lower()
            return 0

        reverse = False
        if self.sort_state["col"] == col:
            reverse = not self.sort_state["reverse"]
        self.sort_state = {"col": col, "reverse": reverse}
        self.manager.items.sort(key=keyfunc, reverse=reverse)
        self._refresh_tree()

if __name__ == "__main__":
    App().mainloop()