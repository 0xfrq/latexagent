"""
utils.py - fungsi-fungsi utility umum
"""

import re


def detect_input_type(text_input):
    """deteksi tipe input: youtube, web_url, atau text"""
    text_input = text_input.strip()
    youtube_patterns = [
        r"youtube\.com/watch", r"youtu\.be/",
        r"youtube\.com/embed", r"youtube\.com/shorts",
    ]
    for pattern in youtube_patterns:
        if re.search(pattern, text_input):
            return "youtube"
    if text_input.startswith("http://") or text_input.startswith("https://"):
        return "web_url"
    return "text"


def clean_latex_response(text):
    """bersihin response model - hapus markdown code block wrapper kalau ada"""
    text = text.strip()
    if text.startswith("```latex"):
        text = text[8:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()