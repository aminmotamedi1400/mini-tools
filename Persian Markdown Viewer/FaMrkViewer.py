import tkinter as tk
from tkinter import scrolledtext, ttk
import markdown2_like          # تبدیل Markdown به HTML
import webbrowser              # برای باز کردن فایل در مرورگر
import os                      # مسیر فایل
import tempfile                # ساخت پوشه‌ی temp
import importlib; importlib.reload(markdown2_like)

# -------------------------------------------------------------------
# 1. ایجاد پنجره اصلی
root = tk.Tk()
root.title("Persian Markdown Viewer")
root.geometry("900x600")

# -------------------------------------------------------------------
# 2. ناحیه متن (Markdown)
txt_md = scrolledtext.ScrolledText(root, wrap='word', font=('Tahoma', 12))
txt_md.pack(fill='both', expand=True, side='top')
txt_md.insert('1.0',
              '# سلام\nمتن فارسی نمونه برای تست.\n\n* لیست \n* دو مورد')

# -------------------------------------------------------------------
# 3. دکمه تبدیل به HTML
def render_to_html():
    md_text = txt_md.get("1.0", "end-1c")

    # تبدیل Markdown → HTML
    html_body = markdown2_like.markdown(md_text, extras=["fenced-code-blocks"])

    # افزودن CSS جهت RTL و فونت مناسب
    full_html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
/* -------------------------------
   پایه‌ی صفحه – راست‑به‑چپ
   ------------------------------- */
body{{
    direction: rtl;                  /* متن از راست به چپ خوانده می‌شود */
    unicode-bidi: embed;
    font-family: 'Tahoma', 'Arial', sans-serif;
    line-height: 1.6rem;             /* ارتفاع خط مناسب برای مقالات بلند */
    color:#333;                      /* رنگ خاکستری تیره برای متن */
    margin:0; padding:0;             /* حذف افراز پیش‌فرض مرورگر */
}}

/* -------------------------------
   پاراگراف‌ها
   ------------------------------- */
p{{
    margin-bottom:1.4rem;            /* فضا بعد از هر پاراگراف */
    text-align:justify;              /* هموار کردن حاشیه‌های متن */
    font-size:0.95rem;               /* کمی کوچکتر از خط پایه برای خوانایی بهتر */
}}

/* -------------------------------
   جدول‌ها
   ------------------------------- */
table{{
    width:100%;                      /* عرض کامل در ظرف خود */
    border-collapse:collapse;        /* حذف فواصل خالی بین سلول‌ها */
    margin-bottom:1.6rem;
}}

th, td{{
    padding:0.75rem 1rem;            /* فضای داخلی سلول */
    text-align:center;               /* مرکزیت متن */
    vertical-align:middle;           /* عمودی وسط‌گیری در ردیف‌ها */
    border:1px solid #ddd;           /* حاشیه نازک و خاکستری روشن */
}}

th{{
    background:#f0f0f0;              /* پس‌زمینه‌ی تیره‌تر برای هدر */
    font-weight:bold;
}}

tr:nth-child(even){{                 /* رنگ‌بندی ردیف‌های جدول */
    background:#fafafa;
}}

/* -------------------------------
   عناوین
   ------------------------------- */
h2{{
    margin-top:1.8rem;               /* فاصله بالا */
    margin-bottom:0.6rem;
    font-size:1.5rem;                /* اندازه بزرگ‌تر برای تیتر دوم */
    color:#222;
}}

h3{{
    margin-top:1.4rem;
    margin-bottom:0.5rem;
    font-size:1.25rem;               /* اندازه متوسط برای تیتر سوم */
    color:#444;
}}

/* -------------------------------
   تاکید
   ------------------------------- */
strong{{
    color:#d9534f;                   /* رنگ قرمز تیره برای تأکید */
    font-weight:bold;
}}

/* -------------------------------
   کد و پیش‌نویس (برای هماهنگی با استایل قبلی)
   ------------------------------- */
pre, code{{ 
    background:#f5f5f5; 
    padding:0.4rem 0.6rem; 
    border-radius:3px;
    font-family:"Courier New", monospace;
}}

        </style>
      </head>
      <body>{html_body}</body>
    </html>
    """

    # -------------------------------------------------------------------
    # 4. ذخیره در فایل موقت
    tmp_dir = tempfile.gettempdir()                 # پوشه‌ی سیستم (مثلاً C:\\Users\\…\\AppData\\Local\\Temp)
    file_path = os.path.join(tmp_dir, "persian_markdown_output.html")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    # -------------------------------------------------------------------
    # 5. باز کردن در مرورگر پیش‌فرض
    webbrowser.open(f'file://{os.path.abspath(file_path)}')

btn = ttk.Button(root, text="نمایش HTML", command=render_to_html)
btn.pack(fill='x', pady=5)

# -------------------------------------------------------------------
# (اختیاری) اگر می‌خواهید داخل پنجرهٔ Tkinter نمایش دهید،
# می‌توانید یک widget جدید مثل Text یا Label اضافه کنید.
# در این نسخه فقط فایل HTML باز می‌شود.

root.mainloop()
