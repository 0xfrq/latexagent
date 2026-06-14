import streamlit as st
import subprocess
import tempfile
import os
import base64
import json
import time
import fitz_new as fitz  # pymupdf buat render halaman pdf ke gambar

# --- konfigurasi halaman ---
st.set_page_config(
    page_title="latex editor lokal",
    page_icon="LaTeX",
    layout="wide",
)

# --- sample latex default: a4 + lorem ipsum ---
DEFAULT_LATEX = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{lipsum}
\usepackage[margin=2.5cm]{geometry}

\title{Contoh Dokumen LaTeX}
\author{Penulis}
\date{\today}

\begin{document}

\maketitle

\section{Pendahuluan}
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

\section{Metodologi}
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

\subsection{Sub-bagian Pertama}
Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

\section{Hasil dan Pembahasan}
Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet.

\subsection{Analisis Data}
At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.

\section{Kesimpulan}
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

\end{document}
"""


def compile_latex(latex_code):
    """
    jalanin pdflatex buat kompilasi kode latex.
    return (sukses, pdf_bytes, log_output).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")

        # tulis kode latex ke file
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)

        log_output = ""
        # compile 2x buat handle referensi silang
        for run_num in range(2):
            try:
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-output-directory", tmpdir,
                        tex_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=tmpdir,
                )
                log_output += f"--- run {run_num + 1} ---\n"
                log_output += result.stdout + "\n"
                if result.stderr:
                    log_output += "stderr: " + result.stderr + "\n"
            except subprocess.TimeoutExpired:
                return False, None, "kompilasi timeout (>60 detik)"
            except FileNotFoundError:
                return False, None, "pdflatex tidak ditemukan! pastikan miktex/texlive sudah ada di PATH."

        # baca pdf yang udah di-generate
        pdf_path = os.path.join(tmpdir, "main.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return True, f.read(), log_output
        else:
            return False, None, log_output


def render_pdf_pages(pdf_bytes, dpi=150):
    """
    convert setiap halaman pdf jadi gambar png (base64).
    pakai pymupdf biar ga perlu poppler.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes("png")
        b64_img = base64.b64encode(img_data).decode("utf-8")
        pages.append({
            "image": b64_img,
            "pdf_width": page.rect.width,
            "pdf_height": page.rect.height,
        })
    doc.close()
    return pages


def build_viewer_html(pages_data, pdf_base64):
    """
    baca template html, inject data halaman dan pdf base64.
    return string html yang siap di-render di streamlit.
    """
    template_path = os.path.join(os.path.dirname(__file__), "viewer_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # inject data json halaman dan base64 pdf ke template
    html = html.replace("__PAGES_JSON__", json.dumps(pages_data))
    html = html.replace("__PDF_BASE64__", pdf_base64)
    return html


# =============================================
# --- UI utama ---
# =============================================

# header
st.markdown(
    """
    <div style="text-align: center; padding: 8px 0 16px 0;">
        <h1 style="margin-bottom:4px;">LaTeX Editor Lokal</h1>
        <p style="color: gray; margin-top:0;">
            clone overleaf berbasis lokal -- kompilasi langsung di mesin kamu
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# session state
if "latex_code" not in st.session_state:
    st.session_state.latex_code = DEFAULT_LATEX

# --- toolbar ---
col_tb1, col_tb2, col_tb3 = st.columns([1, 1, 4])

with col_tb1:
    compile_btn = st.button("Compile", use_container_width=True, type="primary")

with col_tb2:
    reset_btn = st.button("Reset", use_container_width=True)

with col_tb3:
    st.write("")  # spacer, download button ada di viewer sekarang

# handle reset
if reset_btn:
    st.session_state.latex_code = DEFAULT_LATEX
    st.rerun()

# --- layout: editor kiri, viewer kanan ---
col_editor, col_viewer = st.columns([1, 1], gap="medium")

with col_editor:
    st.markdown("#### Editor")
    latex_input = st.text_area(
        label="kode",
        value=st.session_state.latex_code,
        height=700,
        key="editor",
        label_visibility="collapsed",
    )
    st.session_state.latex_code = latex_input

with col_viewer:
    st.markdown("#### Preview (interaktif)")

    if compile_btn:
        # proses kompilasi
        with st.spinner("kompilasi sedang berjalan..."):
            t0 = time.time()
            sukses, pdf_bytes, log = compile_latex(latex_input)
            elapsed = time.time() - t0

        if sukses:
            # simpan pdf ke session state
            st.session_state.pdf_bytes = pdf_bytes
            st.success(f"kompilasi berhasil ({elapsed:.1f} detik)")
        else:
            st.session_state.pdf_bytes = None
            st.error("kompilasi gagal! cek log di bawah:")
            with st.expander("Log Kompilasi", expanded=True):
                st.code(log, language="text")

    # render viewer kalau ada pdf
    if "pdf_bytes" in st.session_state and st.session_state.pdf_bytes:
        pdf_bytes = st.session_state.pdf_bytes

        # render halaman ke gambar + encode base64
        pages_data = render_pdf_pages(pdf_bytes, dpi=150)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # bangun html viewer interaktif
        viewer_html = build_viewer_html(pages_data, pdf_b64)

        # render di streamlit (tinggi disesuaikan)
        import streamlit.components.v1 as components
        components.html(viewer_html, height=900, scrolling=True)

    else:
        st.info('tekan tombol **Compile** untuk melihat hasil PDF')

# footer
st.markdown("---")
st.caption("dibuat dengan streamlit + pdflatex | semua proses berjalan di lokal")