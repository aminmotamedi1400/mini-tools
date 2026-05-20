# backup_csv.py
import os
import csv
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox



class BackupApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("سامانهٔ بکاپ‌گیری فایل CSV")
        self.geometry("700x400")

        # -------------------------
        # داده‌ها (مسیری ذخیره‌شده در csv)
        # -------------------------
        self.csv_path = os.path.join(os.getcwd(), "file_list.csv")
        self.file_paths = []          # لیست داخلی

        # -------------------------
        # بخش‌های گرافیکی
        # -------------------------
        self.create_widgets()
        self.load_csv()              # اگر فایل csv موجود بود، بارگذاری کن
    def create_widgets(self):
        # --- لیبل و دکمهٔ انتخاب پوشه مقصد ---
        dest_frame = ttk.Frame(self)
        dest_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(dest_frame, text="پوشهٔ مقصد: ").pack(side="left")
        self.dest_var = tk.StringVar()
        ttk.Entry(dest_frame, textvariable=self.dest_var, width=50).pack(side="left", fill="x", expand=True)
        ttk.Button(dest_frame, text="انتخاب …", command=self.browse_dest_folder).pack(side="left", padx=5)

        # --- جدول فایل‌ها ---
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(table_frame, columns=("path",), show="headings")
        self.tree.heading("path", text="مسیر فایل")
        self.tree.column("path", anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # --- دکمه‌های کنترلی ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="افزودن فایل …",
                   command=self.add_file).pack(side="left")
        ttk.Button(btn_frame, text="حذف انتخابی",
                   command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="کپی همه به مقصد",
                   command=self.backup_files).pack(side="right")
    def load_csv(self):
        """اگر فایل csv وجود داشته باشد، مسیرها را بخواند."""
        if not os.path.exists(self.csv_path):
            return
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # خط خالی نگیرد
                        path = row[0]
                        self.file_paths.append(path)
                        self.tree.insert("", "end", values=(path,))
        except Exception as e:
            messagebox.showerror("خطا", f"بارگذاری CSV ناموفق بود.\n{e}")

    def save_csv(self):
        """فهرست مسیرها را در csv ذخیره کند."""
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for p in self.file_paths:
                    writer.writerow([p])
        except Exception as e:
            messagebox.showerror("خطا", f"ذخیره‌ی CSV ناموفق بود.\n{e}")
    def browse_dest_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_var.set(folder)
    def add_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        # اگر قبلاً اضافه شده بود، نادیده بگیر
        if path in self.file_paths:
            messagebox.showinfo("هشدار", "این فایل قبلاً افزوده شد.")
            return

        self.file_paths.append(path)
        self.tree.insert("", "end", values=(path,))
    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("هشدار", "هیچ فایلی انتخاب نشده است.")
            return
        for sel in selected:
            path = self.tree.item(sel, "values")[0]
            try:
                self.file_paths.remove(path)
            except ValueError:
                pass
            self.tree.delete(sel)
    def backup_files(self):
        dest_folder = self.dest_var.get()
        if not dest_folder:
            messagebox.showwarning("خطا", "پوشهٔ مقصد را انتخاب نکرده‌اید.")
            return

        if not os.path.isdir(dest_folder):
            try:
                os.makedirs(dest_folder)
            except Exception as e:
                messagebox.showerror("خطا", f"نمی‌توان پوشه مقصد ایجاد کرد.\n{e}")
                return

        # کپی کردن
        failures = []
        for src in self.file_paths:
            if not os.path.exists(src):
                failures.append((src, "فایل وجود ندارد"))
                continue
            try:
                shutil.copy2(src, dest_folder)
            except Exception as e:
                failures.append((src, str(e)))

        # نتیجه را نمایش بده
        if failures:
            msg = "\n".join(f"{p} : {err}" for p, err in failures)
            messagebox.showerror("خطا", f"برخی فایل‌ها کپی نشدند:\n{msg}")
        else:
            messagebox.showinfo("موفقیت", "تمام فایل‌ها با موفقیت کپی شد.")
    def on_close(self):
        self.save_csv()
        self.destroy()

if __name__ == "__main__":
    app = BackupApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
