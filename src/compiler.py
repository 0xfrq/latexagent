"""
compiler.py - kompilasi latex pakai pdflatex
handle compile, render pdf ke gambar, dan simpan pdf
"""

import subprocess
import tempfile
import os
import base64
import fitz_new as fitz


def compile(latex_code):
    """
    jalanin pdflatex 2x (buat referensi silang).
    return tuple (sukses: bool, pdf_bytes: bytes|None, log: str)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)

        log_output = ""
        for run_num in range(2):
            try:
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode",
                     "-output-directory", tmpdir, tex_path],
                    capture_output=True, text=True, timeout=60, cwd=tmpdir,
                )
                log_output += f"--- run {run_num + 1} ---\n{result.stdout}\n"
                if result.stderr:
                    log_output += f"stderr: {result.stderr}\n"
            except subprocess.TimeoutExpired:
                return False, None, "kompilasi timeout (>60 detik)"
            except FileNotFoundError:
                return False, None, "pdflatex tidak ditemukan! pastikan miktex/texlive ada di PATH."

        pdf_path = os.path.join(tmpdir, "main.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return True, f.read(), log_output
        return False, None, log_output


def render_pages(pdf_bytes, dpi=150):
    """
    convert setiap halaman pdf jadi gambar png (base64).
    pakai pymupdf biar ga perlu poppler.
    return list of dict {image, pdf_width, pdf_height}
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes("png")
        pages.append({
            "image": base64.b64encode(img_data).decode("utf-8"),
            "pdf_width": page.rect.width,
            "pdf_height": page.rect.height,
        })
    doc.close()
    return pages

def extract_page_text(pdf_bytes, page_num):
    """
    extract teks dari halaman tertentu di pdf.
    page_num mulai dari 0.
    berguna buat kasih konteks ke ai tentang isi halaman yang mau direvisi.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if page_num < len(doc):
        text = doc[page_num].get_text()
        doc.close()
        return text
    doc.close()
    return ""


def get_page_count(pdf_bytes):
    """return jumlah halaman pdf"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count