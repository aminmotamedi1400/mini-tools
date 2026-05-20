# -*- coding: utf-8 -*-
"""
مدیریت پسورد ساده با pandas، base64 و Tkinter

1.  پسوردها به صورت Base‑64 در فایل CSV ذخیره می‌شوند.
2.  رابط گرافیکی با Tkinter ساخته شده است که لیست سایت‌ها را نمایش می‌دهد
    و با دوبار کلیک روی یک ردیف پسورد رمزگشایی‌شده نشان داده می‌شود.
3.  امکان افزودن ورودی جدید (سایت، کاربر، پسورد) وجود دارد؛ پسورد در هنگام ذخیره
    به صورت Base‑64 کدگذاری می‌شود.

"""

import os
import base64
import pandas as pd
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

# ------------------------------------------------------------------
# ۱. تنظیمات پایه
# ------------------------------------------------------------------
CSV_FILE = "passwords.csv"          # مسیر فایل CSV

def encode_pw(pw: str) -> str:
    """کدگذاری پسورد به Base‑64."""
    return base64.b64encode(pw.encode("utf-8")).decode("utf-8")

def decode_pw(encoded_pw: str) -> str:
    """رمزگشایی پسورد از Base‑64."""
    try:
        return base64.b64decode(encoded_pw.encode("utf-8")).decode("utf-8")
    except Exception as e:
        # در صورت خطا، پیغام هشدار
        return "[خطای رمزگشایی]"

# ------------------------------------------------------------------
# ۲. بارگذاری یا ایجاد دیتافریم اولیه
# ------------------------------------------------------------------
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    # ساخت جدول خالی با ستون‌های مورد نیاز
    df = pd.DataFrame(columns=["Site", "Username", "Password"])
    df.to_csv(CSV_FILE, index=False)

# ------------------------------------------------------------------
# ۳. رابط کاربری Tkinter
# ------------------------------------------------------------------
root = tk.Tk()
root.title("مدیریت پسورد")
root.geometry("600x400")

def refresh_table() -> None:
    """بارگذاری مجدد داده‌ها در جدول Treeview."""
    for row in tree.get_children():
        tree.delete(row)
    for idx, (_, row) in enumerate(df.iterrows()):
        tree.insert("", "end", iid=idx,
                    values=(row["Site"], row["Username"], row["Password"]))

def add_entry() -> None:
    """افزودن پسورد جدید از طریق dialog."""
    site = simpledialog.askstring("ورودی", "نام سایت:")
    if not site: return

    user = simpledialog.askstring("ورودی", "کاربر:")
    if not user: return

    pwd = simpledialog.askstring("ورودی", "پسورد:", show="*")
    if pwd is None: return

    encoded_pwd = encode_pw(pwd)
    new_row = {"Site": site, "Username": user, "Password": encoded_pwd}
    
    global df
    
    # روش ۱ – با loc
    # df.loc[len(df)] = new_row
    
    # روش ۲ – با pd.concat (به صورت زیر در کد کامل قرار می‌گیرد)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(CSV_FILE, index=False)   # ذخیره در CSV
    refresh_table()                    # بروزرسانی جدول


def show_password(event=None):
    """نمایش پسورد رمزگشایی‌شده هنگام کلیک دابل‌کلیک."""
    selected_id = tree.focus()
    if not selected_id: return
    row = df.loc[int(selected_id)]
    decoded = decode_pw(row["Password"])
    messagebox.showinfo(
        "پسورد رمزگشایی شده",
        f"سایت: {row['Site']}\nکاربر: {row['Username']}\nپسورد: {decoded}"
    )

# ------------------------------------------------------------------
# ۴. جدول Treeview برای نمایش داده‌ها
# ------------------------------------------------------------------
columns = ("site", "username", "password")
tree = ttk.Treeview(root, columns=columns, show="headings")
tree.heading("site", text="سایت")
tree.heading("username", text="کاربر")
tree.heading("password", text="پسورد (رمزنگاری)")
tree.column("site", width=150)
tree.column("username", width=120)
tree.column("password", width=200)
tree.pack(fill="both", expand=True)

# پیوند دابل‌کلیک برای نمایش پسورد
tree.bind("<Double-1>", show_password)

# ------------------------------------------------------------------
# ۵. دکمه‌های کنترل
# ------------------------------------------------------------------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

add_btn = tk.Button(btn_frame, text="افزودن پسورد", command=add_entry)
add_btn.pack(side="left", padx=5)

refresh_table()
root.mainloop()
