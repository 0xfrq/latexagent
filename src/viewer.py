"""
viewer.py - interactive pdf viewer
render pakai streamlit components.html
"""

import os
import json
import streamlit.components.v1 as components


def render(pages_data, pdf_base64, height=800, key=None):
    """
    render interactive pdf viewer.
    return None (komunikasi satu arah dari python ke html).
    """
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "viewer_template.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__PAGES_JSON__", json.dumps(pages_data))
    html = html.replace("__PDF_BASE64__", pdf_base64)

    components.html(html, height=height, scrolling=True)