# -*- coding: utf-8 -*-
"""
markdown2_like.py

یک پیاده‌سازی ساده از تابع `markdown2.markdown()` با قابلیت فعال کردن
فیلتر extras (در حال حاضر فقط «fenced-code-blocks»).

استفاده:
>>> from markdown2_like import markdown
>>> html = markdown('''# عنوان\nمتن **سخت** و *کوتاه*.\n```python\ndef foo():\n    pass\n```\n[لینک](https://example.com)''')
"""
import re
from typing import List, Optional

__all__ = ['markdown']


def _escape_html(text: str) -> str:
    """تبدیل کاراکترهای خاص HTML به entites."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _fenced_code_blocks(md_text: str) -> str:
    """
    بلوک‌های کد فنس‌شده (```lang\n...\n```) را به <pre><code> تبدیل می‌کند.
    اگر زبان مشخص شده باشد، کلاس `language-<lang>` اضافه می‌شود.
    """
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
    """تبدیل #… به <h1>, ##… به <h2> و … تا <h6>."""
    def repl(match):
        level = len(match.group(1))
        content = match.group(2).strip()
        return f'<h{level}>{content}</h{level}>'
    heading_re = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)
    return heading_re.sub(repl, md_text)


def _bold_and_italic(md_text: str) -> str:
    """تبدیل **…** و __…__ به <strong>، *…* و _…_ به <em>."""
    # Bold
    bold_re = re.compile(r'(\*\*|__)(.*?)\1')
    md_text = bold_re.sub(r'<strong>\2</strong>', md_text)

    # Italic (باید بعد از بولد باشد تا تداخل نداشته باشد)
    italic_re = re.compile(r'(?<![*_])(\*|_)(.*?)(?![*_])\1')
    return italic_re.sub(r'<em>\2</em>', md_text)


def _inline_code(md_text: str) -> str:
    """تبدیل `…` به <code>."""
    code_re = re.compile(r'`([^`]+)`')
    return code_re.sub(r'<code>\1</code>', md_text)


def _links(md_text: str) -> str:
    """تبدیل [text](url) به <a href="url">text</a>."""
    link_re = re.compile(r'$([^$]+)$$([^)]+)$')
    return link_re.sub(r'<a href="\2">\1</a>', md_text)


def _paragraphs(md_text: str) -> str:
    """
    متون را به پاراگرافی (p) تبدیل می‌کند.
    خطوط خالی را به‌عنوان جداکننده پاراگراف در نظر می‌گیرد
    و سطرهای یکسان را در همان p نگه می‌دارد.
    """
    parts = re.split(r'\n\s*\n', md_text.strip())
    paragraphs = [f'<p>{part.replace("\n", " ")}</p>' for part in parts]
    return '\n'.join(paragraphs)


def markdown(md_text: str, extras: Optional[List[str]] = None) -> str:
    """
    تابع اصلی تبدیل Markdown به HTML.

    پارامترها
    ----------
    md_text : str
        متن ورودی ‎Markdown‎.
    extras : list of str, optional
        لیستی از گزینه‌های اضافی. در حال حاضر فقط «fenced-code-blocks»
        پشتیبانی می‌شود؛ اگر وجود نداشته باشد، بلوک‌های کد فنس‌شده به‌صورت
        ساده ` ``` ` بدون تبدیل باقی می‌مانند.
    """
    if extras is None:
        extras = []

    # مرحله 1: پردازش بلوک‌های فنس شده (در صورت فعال بودن)
    if 'fenced-code-blocks' in extras:
        md_text = _fenced_code_blocks(md_text)

    # مراحل بعدی به ترتیب: عنوان‌ها، بولد/ایتالیک، کد inline، لینک
    md_text = _headings(md_text)
    md_text = _bold_and_italic(md_text)
    md_text = _inline_code(md_text)
    md_text = _links(md_text)

    # در نهایت پاراگراف‌ها
    html = _paragraphs(md_text)

    return html


# ------------------------------------------------------------------
# اگر می‌خواهید از این فایل به صورت اسکریپت استفاده کنید، می‌توانید
# بخش زیر را فعال کنید. برای مثال:
#
#   python -m markdown2_like "متن Markdown"
#

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m markdown2_like \"markdown text\"")
        sys.exit(1)

    md_input = sys.argv[1]
    html_output = markdown(md_input, extras=['fenced-code-blocks'])
    print(html_output)
