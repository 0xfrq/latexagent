"""
tab_generate.py - tab generate latex
pilih style, generate via 9router, auto compile
"""

import streamlit as st
import time
from models import topics
from services import router
from services.utils import clean_latex_response
from config import get_router_config
from compiler import compile as compile_latex


def render(current_topic, config):
    """render tab generate latex"""
    st.markdown(f"### Generate LaTeX: {current_topic['name']}")

    if not current_topic.get("extracted_content"):
        st.warning("knowledge base masih kosong! upload dan extract konten dulu di tab 'Knowledge Base'.")
        return

    rc = get_router_config(config)
    st.info(f"knowledge base: {len(current_topic['extracted_content'])} chars, {len(current_topic.get('files', []))} file(s)")

    # pilihan style
    st.markdown("#### Output Style")
    style_options = ["Summary", "Study Notes"]
    style_options.extend(st.session_state.get("custom_styles", []))
    style_options.append("Custom...")

    selected_style = st.selectbox("Choose style", style_options, key=f"style_{current_topic['id']}")

    custom_style_desc = ""
    if selected_style == "Custom...":
        custom_style_desc = st.text_area(
            "Describe the style", height=80,
            placeholder="contoh: review paper dengan format comparative analysis...",
            key=f"custom_style_{current_topic['id']}",
        )
        selected_style = custom_style_desc if custom_style_desc else "Summary"

    # manage custom styles
    with st.expander("Manage custom styles"):
        new_style = st.text_input("Add new style preset", key="new_style_gen")
        if st.button("Add Preset"):
            if new_style.strip():
                st.session_state.setdefault("custom_styles", []).append(new_style.strip())
                st.experimental_rerun()
        for i, cs in enumerate(st.session_state.get("custom_styles", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"- {cs}")
            if c2.button("x", key=f"rm_style_gen_{i}"):
                st.session_state["custom_styles"].pop(i)
                st.experimental_rerun()

    st.markdown("---")

    # tombol generate
    if not rc["base_url"] or not rc["api_key"] or not rc["latex_model"]:
        st.error("konfigurasi router belum lengkap! isi base_url, api_key, dan latex_model di config.json")
    else:
        if st.button("Generate LaTeX", type="primary", use_container_width=True):
            _handle_generate(current_topic, config, rc, selected_style)

    # tampilkan latex yang ada
    if current_topic.get("latex_code"):
        with st.expander("Current LaTeX Code", expanded=False):
            st.code(current_topic["latex_code"], language="latex")


def _handle_generate(current_topic, config, rc, selected_style):
    """proses generate latex via 9router"""
    with st.spinner("generating latex via 9router..."):
        try:
            progress = st.progress(0)

            messages = router.build_generate_messages(
                current_topic["extracted_content"], selected_style,
            )
            progress.progress(30)

            raw_response = router.call(
                rc["base_url"], rc["api_key"], rc["latex_model"],
                messages, max_tokens=8192, temperature=0.3,
            )
            latex_code = clean_latex_response(raw_response)
            progress.progress(60)

            # simpan latex ke topic
            topics.update(current_topic["id"], {
                "latex_code": latex_code,
                "style_used": selected_style,
            })

            # auto compile
            st.info("compiling...")
            sukses, pdf_bytes, log = compile_latex(latex_code)
            if sukses:
                topics.save_pdf(current_topic["id"], pdf_bytes)
                progress.progress(100)
                st.success("berhasil! buka tab 'Review & Revise' untuk melihat hasilnya.")
            else:
                progress.progress(100)
                st.warning("latex di-generate tapi kompilasi gagal. edit manual di tab Review.")
                with st.expander("Compile Log"):
                    st.code(log, language="text")

            st.experimental_rerun()
        except Exception as e:
            progress.progress(0)
            st.error(f"gagal generate: {str(e)}")