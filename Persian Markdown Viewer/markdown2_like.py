import re
from typing import List, Optional

__all__ = ['markdown']

# ------------------------------------------------------------------
# helpers ------------------------------------------------------------
# ------------------------------------------------------------------

def _escape_html(text: str) -> str:
    """
    همان تابعی که برای خروجی‌گذاری متن استفاده می‌کنید.
    اگر بخشی از متن یک تگ HTML است، آن را به‌صورت خام نگه می‌دارد؛
    در غیر این صورت، کاراکترهای خاص را escape‑می‌کند.
    """
    if re.search(r'<[^>]+>', text):
        return text          # فرض: اگر contain `<…>`، متن HTML است و escape نمی‌شود
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
    )

# ------------------------------------------------------------------
# existing conversion functions (unchanged)
# ------------------------------------------------------------------

def _fenced_code_blocks(md_text: str) -> str:
    fence_re = re.compile(r'''
        ^```          # شروع با سه backtick
        (\w+)?        # (اختیاری) نام زبان
        \n            # خط جدید
        ([\s\S]*?)    # محتوا (غیر‌دریافت‌گر تا پایان)
        ^```\s*$      # پایان بلوک؛ سه backtick در ابتدای خط
    ''', re.MULTILINE | re.VERBOSE)

    def repl(match):
        lang = match.group(1)
        code = _escape_html(match.group(2))
        if lang:
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
        else:
            return f'<pre><code>{code}</code></pre>'

    return fence_re.sub(repl, md_text)


def _headings(md_text: str) -> str:
    def repl(match):
        level = len(match.group(1))
        content = match.group(2).strip()
        return f'<h{level}>{content}</h{level}>'
    heading_re = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)
    return heading_re.sub(repl, md_text)


def _bold_and_italic(md_text: str) -> str:
    # Bold
    bold_re = re.compile(r'(\*\*|__)(.*?)\1')
    md_text = bold_re.sub(r'<strong>\2</strong>', md_text)

    # Italic (باید بعد از بولد باشد تا تداخل نداشته باشد)
    italic_re = re.compile(r'(?<![*_])(\*|_)(.*?)(?![*_])\1')
    return italic_re.sub(r'<em>\2</em>', md_text)


def _inline_code(md_text: str) -> str:
    code_re = re.compile(r'`([^`]+)`')
    return code_re.sub(r'<code>\1</code>', md_text)

# ------------------------------------------------------------------
# NEW: table conversion ----------------------------------------------
# ------------------------------------------------------------------
def _tables(md_text: str) -> str:
    """
    تبدیل بلوک‌های جدول Markdown (با ساختار `| … |` و خط separator)
    به `<table>...</table>`.

    ویژگی‌ها:
        * فقط جداولی که در دو یا چند خط پشت سر هم هستند،
          و خط دوم صرفاً شامل `-`, `:`, `|`, و/یا فاصله است، تبدیل می‌شوند.
        * سلول‌های حاوی تگ‌های HTML (مثل `<strong>`) به‌صورت خام نگه‌داری
          می‌شوند؛ سایر محتوای سلول escape‑می‌شود.
        * خطوط separator (`---` یا `:--:` و ...) حذف می‌شوند و فقط
          هدر و ردیف‌های واقعی جدول در خروجی ظاهر می‌شوند.
    """
    # جدا کردن بلوک‌ها (متن‌های جداگانهٔ بین دو خط خالی)
    blocks = re.split(r'\n\s*\n', md_text)
    result_blocks: List[str] = []

    # regex برای تشخیص خط separator
    sep_re = re.compile(r'^[\s|:-]+$')

    for block in blocks:
        lines = [l.rstrip() for l in block.strip('\n').split('\n')]
        # اگر حداقل دو خط نداریم یا اولین خط شامل `|` نیست، فقط بازگردانیم
        if len(lines) < 2 or '|' not in lines[0]:
            result_blocks.append(block)
            continue

        # پیدا کردن اندیس خط separator (اگر وجود نداشته باشد، بلوک را رد می‌کنیم)
        sep_index = None
        for idx, line in enumerate(lines):
            if sep_re.match(line):
                sep_index = idx
                break

        if sep_index is None:
            result_blocks.append(block)
            continue

        # ------------------------------------------------------------------
        # تبدیل هدر (خط اول) به <th>
        header_cells = [c.strip() for c in lines[0].split('|')]
        if header_cells and not header_cells[0]:
            header_cells = header_cells[1:]
        if header_cells and not header_cells[-1]:
            header_cells = header_cells[:-1]

        th_html = "".join(f"<th>{_escape_html(c)}</th>" for c in header_cells)
        table_rows = [f"<tr>{th_html}</tr>"]

        # ------------------------------------------------------------------
        # تبدیل ردیف‌های داده (بعد از خط separator) به <td>
        for data_line in lines[sep_index + 1 :]:
            cells = [c.strip() for c in data_line.split('|')]
            if cells and not cells[0]:
                cells = cells[1:]
            if cells and not cells[-1]:
                cells = cells[:-1]

            td_html = "".join(f"<td>{_escape_html(c)}</td>" for c in cells)
            table_rows.append(f"<tr>{td_html}</tr>")

        # ------------------------------------------------------------------
        # ایجاد خروجی جدول
        table_html = "<table>\n" + "\n".join(table_rows) + "\n</table>"
        result_blocks.append(table_html)

    return "\n\n".join(result_blocks)

def _links(md_text: str) -> str:
    """تبدیل [text](url) به <a href="url">text</a>."""
    link_re = re.compile(r'$([^$]+)$$([^)]+)$')
    return link_re.sub(r'<a href="\2">\1</a>', md_text)


def _paragraphs(md_text: str) -> str:
    parts = re.split(r'\n\s*\n', md_text.strip())
    paragraphs = [f'<p>{part.replace("\n", " ")}</p>' for part in parts]
    return '\n'.join(paragraphs)

# ------------------------------------------------------------------
# main function ------------------------------------------------------
# ------------------------------------------------------------------

def markdown(md_text: str, extras: Optional[List[str]] = None) -> str:
    """
    تبدیل متن Markdown به HTML.
    """
    if extras is None:
        extras = []

    # 1. بلوک‌های کد فنس‌شده (در صورت فعال بودن)
    if 'fenced-code-blocks' in extras:
        md_text = _fenced_code_blocks(md_text)

    # 2. عناصر دیگر
    md_text = _headings(md_text)
    md_text = _bold_and_italic(md_text)
    md_text = _inline_code(md_text)
    md_text = _links(md_text)

    # 3. جداول
    md_text = _tables(md_text)

    # 4. پاراگراف‌ها
    html = _paragraphs(md_text)

    return html

# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m markdown2_like \"markdown text\"")
        sys.exit(1)
    md_input = sys.argv[1]
    html_output = markdown(md_input, extras=['fenced-code-blocks'])
    print(html_output)
