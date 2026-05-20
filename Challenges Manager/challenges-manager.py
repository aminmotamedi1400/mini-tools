#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import uuid
from datetime import date, datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


CHALLENGES_FILE = "challenges.csv"
PROGRESS_FILE   = "progress.csv"

# ---------- Helpers ----------
def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def today_str():
    return date.today().isoformat()

# ---------- Main Application ----------
class ChallengeManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("مدیریت چالش‌ها – 2026")
        self.geometry("950x600")
        self.resizable(False, False)

        # Load data
        self.challenges = read_csv(CHALLENGES_FILE)
        self.progress   = read_csv(PROGRESS_FILE)

        # UI
        self.create_widgets()
        self.refresh_tree()

    # ----- UI Creation -----
    def create_widgets(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="+ اضافه کردن چالش",
                   command=self.add_challenge).pack(side="left")
        ttk.Button(btn_frame, text="ویرایش",
                   command=lambda: self.edit_selected(False)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="حذف",
                   command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="ثبت پیشرفت روزانه",
                   command=self.record_progress).pack(side="left", padx=5)

        # Treeview
        columns = ("id","name","target","unit",
                   "start","end","completed","remaining","days_left","daily_req")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=25)
        for col in columns:
            if col == "name":
                self.tree.heading(col, text="نام چالش")
                self.tree.column(col, width=200, anchor="w")
            elif col == "unit":
                self.tree.heading(col, text="واحد")
                self.tree.column(col, width=60, anchor="center")
            else:
                self.tree.heading(col, text=col.replace("_"," ").title())
                self.tree.column(col, width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

    # ----- Data Handling -----
    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        today = date.today()
        for ch in self.challenges:
            target = float(ch["target"])
            completed = float(ch.get("completed", "0"))
            remaining = max(0, target - completed)

            start_date  = datetime.strptime(ch["start_date"], "%Y-%m-%d").date()
            end_date    = datetime.strptime(ch["end_date"],   "%Y-%m-%d").date()

            days_left = (end_date - today).days
            if days_left < 0: days_left = 0

            daily_req = remaining / max(1, days_left+1)  # avoid div by zero

            self.tree.insert("", "end", values=(
                ch["id"], ch["name"], f"{target:g}", ch["unit"],
                ch["start_date"], ch["end_date"], f"{completed:g}",
                f"{remaining:g}", f"{days_left:d}", f"{daily_req:.2f}"
            ))

    def add_challenge(self):
        dialog = ChallengeDialog(self, "ایجاد چالش جدید")
        self.wait_window(dialog)
        if dialog.result:
            ch_id = str(uuid.uuid4())
            new_ch = {
                "id": ch_id,
                **dialog.result,
                "completed": "0"
            }
            self.challenges.append(new_ch)
            write_csv(CHALLENGES_FILE, self.challenges, fieldnames=new_ch.keys())
            self.refresh_tree()

    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "لطفاً یک چالش انتخاب کنید.")
            return None
        item = self.tree.item(sel[0])
        ch_id = item["values"][0]
        for ch in self.challenges:
            if ch["id"] == ch_id:
                return ch
        return None

    def edit_selected(self, is_new=False):
        ch = self.get_selected()
        if not ch:
            return
        dialog = ChallengeDialog(self, "ویرایش چالش", initial=ch)
        self.wait_window(dialog)
        if dialog.result:
            # Update fields except id and completed
            for key in ("name","target","unit","start_date","end_date"):
                ch[key] = dialog.result[key]
            write_csv(CHALLENGES_FILE, self.challenges, fieldnames=self.challenges[0].keys())
            self.refresh_tree()

    def delete_selected(self):
        ch = self.get_selected()
        if not ch:
            return
        if messagebox.askyesno("تایید", f"آیا مطمئن هستید که می‌خواهید چالش «{ch['name']}» را حذف کنید؟"):
            self.challenges.remove(ch)
            write_csv(CHALLENGES_FILE, self.challenges, fieldnames=self.challenges[0].keys())
            # Remove related progress entries
            self.progress = [p for p in self.progress if p["challenge_id"] != ch["id"]]
            write_csv(PROGRESS_FILE, self.progress,
                      fieldnames=["challenge_id","date","value"])
            self.refresh_tree()

    def record_progress(self):
        ch = self.get_selected()
        if not ch:
            return
        amount_str = simpledialog.askstring("ورود پیشرفت",
                                            f"مقدار انجام شده برای «{ch['name']}» (به {ch['unit']}):")
        if amount_str is None:
            return  # cancel
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "لطفاً عدد مثبت وارد کنید.")
            return

        today = today_str()
        self.progress.append({
            "challenge_id": ch["id"],
            "date": today,
            "value": f"{amount:g}"
        })
        write_csv(PROGRESS_FILE, self.progress,
                  fieldnames=["challenge_id","date","value"])

        # Update completed field
        current_total = float(ch.get("completed", "0"))
        ch["completed"] = f"{current_total + amount:.4f}"
        write_csv(CHALLENGES_FILE, self.challenges,
                  fieldnames=self.challenges[0].keys())

        messagebox.showinfo("موفقیت", f"پیشرفت {amount:g} {ch['unit']} ثبت شد.")
        self.refresh_tree()


# ---------- Dialog for Adding/Editing ----------
class ChallengeDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        # Fields
        fields = [
            ("نام چالش", "name"),
            ("هدف کل (عدد)", "target"),
            ("واحد",     "unit"),
            ("تاریخ شروع (YYYY-MM-DD)", "start_date"),
            ("تاریخ پایان (YYYY-MM-DD)", "end_date")
        ]

        self.vars = {}
        for idx, (label_text, key) in enumerate(fields):
            ttk.Label(self, text=label_text).grid(row=idx, column=0, sticky="e", padx=5, pady=3)
            var = tk.StringVar()
            entry = ttk.Entry(self, textvariable=var, width=30)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.vars[key] = var

        # If editing pre-fill
        if initial:
            for k,v in initial.items():
                if k in self.vars and v is not None:
                    self.vars[k].set(v)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="ذخیره", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="انصراف", command=self.destroy).pack(side="left")

    def on_save(self):
        try:
            name = self.vars["name"].get().strip()
            if not name:
                raise ValueError("نام چالش خالی است.")
            target = float(self.vars["target"].get())
            if target <= 0:
                raise ValueError("هدف باید عدد مثبت باشد.")
            unit = self.vars["unit"].get().strip() or "یکه"
            start_date = datetime.strptime(self.vars["start_date"].get(), "%Y-%m-%d").date()
            end_date   = datetime.strptime(self.vars["end_date"].get(),   "%Y-%m-%d").date()
            if end_date < start_date:
                raise ValueError("تاریخ پایان قبل از شروع است.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))
            return

        self.result = {
            "name": name,
            "target": f"{target}",
            "unit": unit,
            "start_date": start_date.isoformat(),
            "end_date":   end_date.isoformat()
        }
        self.destroy()


# ---------- Run ----------
if __name__ == "__main__":
    app = ChallengeManager()
    app.mainloop()
