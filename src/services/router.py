"""
router.py - integrasi 9router (openai-compatible api)
buat generate latex dan revisi dokumen (targeted section-only edit)
"""

import json
import requests


def call(base_url, api_key, model, messages, max_tokens=4096, temperature=0.7):
    """
    panggil 9router (atau openai-compatible endpoint).
    handle regular json dan streaming (sse) response.
    return string response dari model.
    """
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
        "stream": False,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()

    raw_text = resp.text.strip()

    # handle sse streaming format
    if raw_text.startswith("data:"):
        return _parse_sse_response(raw_text)

    # regular json
    try:
        data = json.loads(raw_text)
        return data["choices"][0]["message"]["content"]
    except json.JSONDecodeError:
        return _parse_messy_response(raw_text)


def _parse_sse_response(raw_text):
    """parse sse format, gabungkan semua chunk content"""
    content_parts = []
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            if "content" in delta:
                content_parts.append(delta["content"])
        except (json.JSONDecodeError, IndexError, KeyError):
            continue
    if content_parts:
        return "".join(content_parts)
    raise ValueError("tidak bisa extract content dari sse response")


def _parse_messy_response(raw_text):
    """handle response yang bukan clean json"""
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
        except json.JSONDecodeError:
            continue
    return raw_text


def build_generate_messages(extracted_content, style, extra_instructions=""):
    """bikin messages buat generate latex dari konten"""
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
        "given source material and a style, generate a complete, compilable latex document.\n"
        "requirements:\n"
        "- use \\documentclass[12pt,a4paper]{article}\n"
        "- include packages: inputenc, geometry (2.5cm margins), hyperref, enumitem, booktabs\n"
        "- use proper section/subsection structure\n"
        "- write in the same language as the source material\n"
        "- make it visually clean and professional\n"
        "- output ONLY the latex code, no explanations, no markdown code blocks\n"
        f"\nstyle: {style_desc}\n"
    )
    if extra_instructions:
        system_prompt += f"\nadditional instructions: {extra_instructions}\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"generate a latex document from:\n\n{extracted_content}"},
    ]


def build_revision_messages(current_latex, revision_request, page_text="", section_context=""):
    """
    bikin messages buat revisi BAGIAN TERTENTU saja dari dokumen latex.
    ai harus mengidentifikasi bagian yang dimaksud dan mengubah HANYA bagian itu.
    sisa dokumen tetap sama persis.

    parameter:
    - current_latex: kode latex lengkap saat ini
    - revision_request: apa yang mau diubah
    - page_text: teks dari halaman yang ditunjuk (buat konteks ai)
    - section_context: deskripsi user tentang bagian mana (e.g. "Section 2")
    """
    system_prompt = (
        "you are a surgical latex editor. your job is to modify ONLY a specific part "
        "of a latex document based on the user's revision request.\n\n"
        "CRITICAL RULES:\n"
        "1. identify the EXACT section/paragraph/element that corresponds to the user's description\n"
        "2. modify ONLY that specific part - nothing else\n"
        "3. keep ALL other content, formatting, structure, packages, preamble EXACTLY the same\n"
        "4. if the user wants to delete something, remove only that element\n"
        "5. if the user wants to add something, add it in the appropriate location near the described area\n"
        "6. output the COMPLETE document (full latex code) with only the targeted change applied\n"
        "7. output ONLY the latex code, no explanations, no markdown code blocks\n"
    )

    user_content = f"FULL LATEX DOCUMENT:\n{current_latex}\n\n"

    if page_text:
        user_content += f"TEXT CONTENT OF THE TARGET PAGE (for context on what's there):\n{page_text}\n\n"

    if section_context:
        user_content += f"USER POINTS TO THIS PART: {section_context}\n\n"

    user_content += f"REVISION REQUEST: {revision_request}\n\n"
    user_content += (
        "NOW: find the exact latex code that generates the content described above, "
        "and modify ONLY that part. output the complete document with that single change."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]