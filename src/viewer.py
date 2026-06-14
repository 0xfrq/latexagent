"""
viewer.py - builder buat interactive pdf viewer html
inject data halaman dan pdf base64 ke template
"""

import os
import json


def build_html(pages_data, pdf_base64):
    """
    baca template html, inject data halaman dan pdf base64.
    return string html yang siap di-render di streamlit.
    """
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "viewer_template.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__PAGES_JSON__", json.dumps(pages_data))
    html = html.replace("__PDF_BASE64__", pdf_base64)
    return html