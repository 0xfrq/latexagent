"""
services.py - semua integrasi api eksternal
- mistral ocr: extract teks dari pdf/gambar
- 9router: generate latex, fetch web content
- youtube: extract caption dengan timestamp
"""

import base64
import json
import requests
import re
from youtube_transcript_api import YouTubeTranscriptApi


# =============================================
# mistral ocr - extract teks dari pdf/image
# =============================================
def mistral_cr(file_bytes, filename, api_key):
    """
    kirim file ke mistral ocr api buat extract teks.
    support pdf dan image (png, jpg, etc).
    return string teks hasil ocr.
    """
    b64_data = base64.b64encode(file_bytes).decode("utf-8")

    # tentukan mime type dari nama file
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    mime_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "bmp": "image/bmp",
        "webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "application/pdf")
    data_uri = f"data:{mime_type};base64,{b64_data}"

    # panggil mistral ocr api
    url = "https://api.mistral.ai/v1/ocr/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": data_uri,
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # extract teks dari response
    # struktur response bisa beda tergantung versi api, handle keduanya
    if "pages" in data:
        # format baru: list of pages
        texts = []
        for page in data["pages"]:
            if "markdown" in page:
                texts.append(page["markdown"])
            elif "text" in page:
                texts.append(page["text"])
        return "\n\n---\n\n".join(texts)
    elif "choices" in data:
        # format lama: completion style
        return data["choices"][0].get("message", {}).get("content", "")
    else:
        return json.dumps(data)


# =============================================
# 9router - openai-compatible api
# =============================================
def call_router(base_url, api_key, model, messages, max_tokens=4096, temperature=0.7):
    """
    panggil 9router (atau openai-compatible endpoint).
    return string response dari model.
    """
    # normalisasi url - pastikan berakhir dengan /chat/completions
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + "/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()

    # extract konten dari response
    return data["choices"][0]["message"]["content"]


def fetch_web_content(url, base_url, api_key, model):
    """
    pakai 9router model buat fetch dan summarize konten dari url web.
    model diinstruksiin buat extract konten utama dari artikel web.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "you are a web content extractor. given a url, "
                "you will fetch and extract the main article content, "
                "including title, author, date, and body text. "
                "return the full extracted text in a clean, readable format. "
                "if you cannot fetch the url, explain what the url likely contains "
                "based on the domain and path."
            ),
        },
        {
            "role": "user",
            "content": f"fetch and extract the content from this url: {url}",
        },
    ]
    return call_router(base_url, api_key, model, messages, max_tokens=8192)


def generate_latex(extracted_content, style, extra_instructions=""):
    """
    generate kode latex dari konten yang udah di-extract.
    style bisa 'summary', 'study_notes', atau custom string.
    return string kode latex.
    ini return messages list, bukan langsung call api
    (biar caller yang handle api call-nya).
    """
    style_prompts = {
        "summary": (
            "create a concise, well-structured summary document. "
            "focus on key points, main arguments, and conclusions. "
            "use clear section headings and bullet points where appropriate."
        ),
        "study_notes": (
            "create comprehensive study notes optimized for learning. "
            "include definitions, key concepts, examples, and important formulas. "
            "use clear hierarchical structure with sections and subsections. "
            "add emphasis (bold/italic) for important terms. "
            "include a quick reference section at the end if applicable."
        ),
    }

    style_desc = style_prompts.get(style.lower(), style)

    system_prompt = (
        "you are an expert latex document writer. "
        "given source material and a style, generate a complete, compilable latex document. "
        "requirements:\n"
        "- use \\documentclass[12pt,a4paper]{article}\n"
        "- include packages: inputenc, geometry (2.5cm margins), hyperref, enumitem, booktabs\n"
        "- use proper section/subsection structure\n"
        "- write in the same language as the source material\n"
        "- make it visually clean and professional\n"
        "- output ONLY the latex code, no explanations\n"
        "- do not wrap in markdown code blocks\n"
        f"\nstyle: {style_desc}\n"
    )

    if extra_instructions:
        system_prompt += f"\nadditional instructions: {extra_instructions}\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "generate a latex document from the following source material:\n\n"
                f"{extracted_content}"
            ),
        },
    ]
    return messages


def revise_latex_section(current_latex, revision_request, section_context=""):
    """
    bikin messages buat revisi bagian tertentu dari dokumen latex.
    return messages list buat di-feed ke 9router.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "you are an expert latex document editor. "
                "given a complete latex document and a revision request, "
                "output the FULL revised latex document (not just the changed part). "
                "keep everything else exactly the same. "
                "output ONLY the revised latex code, no explanations. "
                "do not wrap in markdown code blocks."
            ),
        },
        {
            "role": "user",
            "content": (
                f"here is the current latex document:\n\n"
                f"```latex\n{current_latex}\n```\n\n"
                f"section/context the user wants to change: {section_context}\n\n"
                f"revision request: {revision_request}\n\n"
                f"output the full revised latex document with the requested changes applied."
            ),
        },
    ]
    return messages


# =============================================
# youtube caption extraction
# =============================================
def extract_youtube_video_id(url):
    """
    extract video id dari berbagai format url youtube.
    support: youtube.com/watch?v=xxx, youtu.be/xxx, youtube.com/embed/xxx
    """
    patterns = [
        r"(?:v=|/v/|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})",
        r"(?:v=|/v/|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_youtube_captions(url):
    """
    extract caption/subtitle dari video youtube beserta timestamp.
    return string dengan format timestamp + teks.
    """
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError(f"tidak bisa extract video id dari url: {url}")

    # coba ambil transcript (auto-generated atau manual)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        raise ValueError(f"gagal ambil daftar transcript: {e}")

    # prioritaskan manual transcript, fallback ke auto-generated
    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript()
    except Exception:
        pass

    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(["en", "id"])
        except Exception:
            pass

    if transcript is None:
        try:
            # ambil transcript pertama yang tersedia
            for t in transcript_list:
                transcript = t
                break
        except Exception:
            pass

    if transcript is None:
        raise ValueError(f"tidak ada transcript tersedia untuk video {video_id}")

    # fetch transcript data
    entries = transcript.fetch()

    # format dengan timestamp
    lines = []
    for entry in entries:
        # entry bisa dict atau object tergantung versi library
        if isinstance(entry, dict):
            ts = entry.get("start", 0)
            text = entry.get("text", "")
        else:
            ts = entry.start
            text = entry.text

        # format timestamp mm:ss
        minutes = int(ts // 60)
        seconds = int(ts % 60)
        lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")

    return f"youtube video id: {video_id}\n\n" + "\n".join(lines)


# =============================================
# utility: deteksi tipe input
# =============================================
def detect_input_type(text_input):
    """
    deteksi apakah input user itu url youtube, url web, atau teks biasa.
    return: 'youtube', 'web_url', atau 'text'
    """
    text_input = text_input.strip()
    youtube_patterns = [
        r"youtube\.com/watch",
        r"youtu\.be/",
        r"youtube\.com/embed",
        r"youtube\.com/shorts",
    ]
    for pattern in youtube_patterns:
        if re.search(pattern, text_input):
            return "youtube"

    if text_input.startswith("http://") or text_input.startswith("https://"):
        return "web_url"

    return "text"


def clean_latex_response(text):
    """
    bersihin response dari model - hapus markdown code block wrapper kalau ada.
    kadang model wrap outputnya dalam ```latex ... ```
    """
    text = text.strip()
    # hapus ```latex di awal
    if text.startswith("```latex"):
        text = text[8:]
    elif text.startswith("```"):
        text = text[3:]
    # hapus ``` di akhir
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()