"""
tab_knowledge.py - tab knowledge base
upload file, paste url/teks, extract konten
"""

import streamlit as st
import base64
from models import topics
from services import mistral, webfetch, youtube
from services.utils import detect_input_type


def render(current_topic, config):
    """render tab knowledge base"""
    st.markdown(f"### Knowledge Base: {current_topic['name']}")

    # tampilkan file yang udah ada
    if current_topic.get("files"):
        st.markdown("**Uploaded files:**")
        for fname in current_topic["files"]:
            st.text(f"  - {fname}")
        st.markdown("---")

    # tampilkan extracted content
    if current_topic.get("extracted_content"):
        with st.expander("Extracted Content", expanded=False):
            st.text(current_topic["extracted_content"][:5000])
        st.markdown("---")

    # --- upload sumber baru ---
    st.markdown("#### Add Sources")

    uploaded_files = st.file_uploader(
        "Upload PDF, images, or text files",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp", "txt", "md", "csv"],
        key=f"upload_{current_topic['id']}",
    )

    url_input = st.text_input(
        "Or paste a URL (web article / YouTube video)",
        placeholder="https://...",
        key=f"url_{current_topic['id']}",
    )

    with st.expander("Or paste text directly"):
        text_input = st.text_area(
            "Paste text here", height=150,
            key=f"text_{current_topic['id']}",
        )

    st.markdown("---")

    # tombol extract & clear
    col_ext1, col_ext2 = st.columns([1, 3])
    with col_ext1:
        extract_btn = st.button("Extract Content", type="primary", use_container_width=True)
    with col_ext2:
        clear_kb = st.button("Clear Knowledge Base", use_container_width=True)

    if clear_kb:
        topics.update(current_topic["id"], {
            "files": [], "file_contents": {}, "extracted_content": "",
        })
        st.experimental_rerun()

    if extract_btn:
        _handle_extract(current_topic, config, uploaded_files, url_input, text_input)


def _handle_extract(current_topic, config, uploaded_files, url_input, text_input):
    """proses ekstraksi konten dari semua sumber"""
    has_source = (
        (uploaded_files and len(uploaded_files) > 0)
        or url_input.strip()
        or (text_input and text_input.strip())
    )
    if not has_source:
        st.error("upload minimal 1 file, URL, atau paste teks!")
        return

    all_content = []
    progress_bar = st.progress(0)

    # simpan file yang di-upload
    existing_files = current_topic.get("files", [])
    existing_contents = current_topic.get("file_contents", {})

    for i, f in enumerate(uploaded_files or []):
        file_bytes = f.read()
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""

        if f.name not in existing_files:
            existing_files.append(f.name)
        existing_contents[f.name] = base64.b64encode(file_bytes).decode("utf-8")

        # extract berdasarkan tipe file
        if ext in ("pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"):
            st.info(f"OCR: {f.name}...")
            try:
                text, key_used = mistral.ocr(file_bytes, f.name, config)
                all_content.append(f"## Source: {f.name} (via {key_used})\n\n{text}")
            except Exception as e:
                all_content.append(f"## Source: {f.name}\n\n[OCR ERROR: {str(e)}]")
        else:
            try:
                text = file_bytes.decode("utf-8")
                all_content.append(f"## Source: {f.name}\n\n{text}")
            except Exception:
                all_content.append(f"## Source: {f.name}\n\n[could not read file]")

        progress_bar.progress(int((i + 1) / max(len(uploaded_files), 1) * 50))

    # proses url
    if url_input.strip():
        input_type = detect_input_type(url_input)
        if input_type == "youtube":
            st.info("extracting youtube captions...")
            try:
                captions = youtube.extract_captions(url_input)
                all_content.append(f"## Source: YouTube - {url_input}\n\n{captions}")
            except Exception as e:
                all_content.append(f"## Source: YouTube - {url_input}\n\n[ERROR: {str(e)}]")
        elif input_type == "web_url":
            if not config.get("router", {}).get("api_key"):
                all_content.append(f"## Source: {url_input}\n\n[ERROR: api_key belum diisi di config.json]")
            else:
                st.info("fetching web content...")
                try:
                    web_text = webfetch.fetch(url_input, config)
                    all_content.append(f"## Source: {url_input}\n\n{web_text}")
                except Exception as e:
                    all_content.append(f"## Source: {url_input}\n\n[ERROR: {str(e)}]")
        else:
            all_content.append(f"## Source: {url_input}\n\n{url_input}")
        progress_bar.progress(75)

    # proses teks langsung
    if text_input and text_input.strip():
        all_content.append(f"## Source: Direct Input\n\n{text_input}")

    # gabungkan dengan konten lama
    existing_content = current_topic.get("extracted_content", "")
    new_content = "\n\n---\n\n".join(all_content)
    combined = existing_content + "\n\n---\n\n" + new_content if existing_content else new_content

    # simpan ke topic
    topics.update(current_topic["id"], {
        "files": existing_files,
        "file_contents": existing_contents,
        "extracted_content": combined,
    })

    progress_bar.progress(100)
    st.success("konten berhasil di-extract dan disimpan ke knowledge base!")
    st.experimental_rerun()