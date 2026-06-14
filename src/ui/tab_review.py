"""
tab_review.py - tab review & revise
editor latex, interactive pdf viewer, dan targeted revision loop
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import time
from models import topics
from services import router
from services.utils import clean_latex_response
from config import get_router_config
from compiler import compile as compile_latex, render_pages, extract_page_text, get_page_count
from viewer import build_html


def render(current_topic, config):
    """render tab review & revise"""
    st.markdown(f"### Review & Revise: {current_topic['name']}")

    rc = get_router_config(config)

    # toolbar
    col_tb1, col_tb2 = st.columns([1, 5])
    with col_tb1:
        compile_btn = st.button("Compile", use_container_width=True, type="primary")

    # layout: editor kiri, viewer kanan
    col_editor, col_viewer = st.columns([1, 1], gap="medium")

    with col_editor:
        st.markdown("#### LaTeX Editor")
        latex_val = current_topic.get("latex_code", "")
        latex_input = st.text_area(
            label="kode", value=latex_val, height=500,
            key=f"editor_{current_topic['id']}",
            label_visibility="collapsed",
        )
        if latex_input != latex_val:
            topics.update(current_topic["id"], {"latex_code": latex_input})

    with col_viewer:
        st.markdown("#### PDF Preview (interactive)")

        if compile_btn:
            with st.spinner("kompilasi..."):
                t0 = time.time()
                sukses, pdf_bytes, log = compile_latex(latex_input)
                elapsed = time.time() - t0
            if sukses:
                topics.save_pdf(current_topic["id"], pdf_bytes)
                st.success(f"compiled ({elapsed:.1f}s)")
                st.experimental_rerun()
            else:
                st.error("compile gagal!")
                with st.expander("Compile Log", expanded=True):
                    st.code(log, language="text")

        # render viewer
        cached_pdf = topics.load_pdf(current_topic["id"])
        if cached_pdf:
            pages_data = render_pages(cached_pdf, dpi=150)
            pdf_b64 = base64.b64encode(cached_pdf).decode("utf-8")
            viewer_html = build_html(pages_data, pdf_b64)
            components.html(viewer_html, height=700, scrolling=True)
        else:
            st.info("tekan Compile untuk melihat PDF")

    # =============================================
    # targeted revision section
    # =============================================
    st.markdown("---")
    st.markdown("#### Targeted Revision")
    st.caption(
        "tandai area di PDF pakai tool 'Select to Revise' di viewer, "
        "lalu jelaskan perubahan yang mau dilakukan. "
        "ai akan mengubah HANYA bagian yang ditunjuk, sisanya tetap sama."
    )

    # baris 1: page number + section reference
    cached_pdf = topics.load_pdf(current_topic["id"])
    page_count = get_page_count(cached_pdf) if cached_pdf else 0

    col_pg, col_sec = st.columns([1, 3])
    with col_pg:
        page_num = st.number_input(
            "Page (where the content is)",
            min_value=1, max_value=max(page_count, 1), value=1,
            key=f"page_{current_topic['id']}",
        )
    with col_sec:
        section_ref = st.text_input(
            "Describe what content is there (helps AI locate it)",
            placeholder="e.g. the diagram in section 2, the table about results, the paragraph about methodology...",
            key=f"sec_{current_topic['id']}",
        )

    # baris 2: revision description
    revision_desc = st.text_area(
        "What do you want to change?",
        placeholder="e.g. replace the diagram with a flowchart showing the data pipeline, "
                    "or: delete this paragraph and add a bullet point summary instead, "
                    "or: make the table include an additional column for percentages...",
        height=80,
        key=f"rev_{current_topic['id']}",
    )

    col_rev_btn1, col_rev_btn2, col_rev_btn3 = st.columns([1, 1, 4])
    with col_rev_btn1:
        apply_revision = st.button("Apply Revision", use_container_width=True)
    with col_rev_btn2:
        clear_history = st.button("Clear History", use_container_width=True)

    if clear_history:
        topics.update(current_topic["id"], {"revision_history": []})
        st.experimental_rerun()

    if apply_revision:
        _handle_revision(current_topic, rc, latex_input, cached_pdf, page_num, section_ref, revision_desc)

    # history
    if current_topic.get("revision_history"):
        with st.expander(f"Revision History ({len(current_topic['revision_history'])} changes)"):
            for i, rev in enumerate(current_topic["revision_history"]):
                st.markdown(
                    f"**#{i+1}** [{rev['timestamp']}] "
                    f"**Page {rev.get('page', '?')}** | "
                    f"**{rev['section']}**: {rev['request']}"
                )
                st.divider()


def _handle_revision(current_topic, rc, latex_input, cached_pdf, page_num, section_ref, revision_desc):
    """proses revisi targeted via 9router"""
    if not revision_desc.strip():
        st.warning("deskripsi revisi tidak boleh kosong!")
        return
    if not rc["base_url"] or not rc["api_key"] or not rc["latex_model"]:
        st.error("konfigurasi router belum lengkap di config.json!")
        return

    # extract teks dari halaman yang ditunjuk buat konteks ai
    page_text = ""
    if cached_pdf:
        page_text = extract_page_text(cached_pdf, page_num - 1)  # page_num 1-based, api 0-based

    with st.spinner(f"ai merevisi bagian di halaman {page_num}..."):
        try:
            messages = router.build_revision_messages(
                current_latex=latex_input,
                revision_request=revision_desc.strip(),
                page_text=page_text,
                section_context=section_ref.strip() if section_ref else "",
            )
            raw_response = router.call(
                rc["base_url"], rc["api_key"], rc["latex_model"],
                messages, max_tokens=8192, temperature=0.3,
            )
            revised_latex = clean_latex_response(raw_response)

            # update history
            history = current_topic.get("revision_history", [])
            history.append({
                "page": page_num,
                "section": section_ref.strip() if section_ref else "general",
                "request": revision_desc.strip(),
                "timestamp": time.strftime("%H:%M:%S"),
            })

            topics.update(current_topic["id"], {
                "latex_code": revised_latex,
                "revision_history": history,
            })

            # auto compile
            sukses, pdf_bytes, log = compile_latex(revised_latex)
            if sukses:
                topics.save_pdf(current_topic["id"], pdf_bytes)
                st.success(f"revisi halaman {page_num} berhasil diterapkan dan di-compile ulang!")
            else:
                st.warning("revisi diterapkan tapi kompilasi gagal. cek di editor.")
                with st.expander("Compile Log"):
                    st.code(log, language="text")

            st.experimental_rerun()
        except Exception as e:
            st.error(f"gagal merevisi: {str(e)}")