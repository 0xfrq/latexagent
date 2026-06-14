"""
app.py - entry point utama aplikasi
dijalankan dengan: streamlit run src/app.py
"""

import sys
import os

# pastikan src/ ada di path biar import bisa jalan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from config import load_config
from ui import sidebar
from ui import tab_knowledge
from ui import tab_generate
from ui import tab_review


# --- konfigurasi halaman ---
st.set_page_config(
    page_title="latex ai editor",
    page_icon="LaTeX",
    layout="wide",
)

# --- load config ---
try:
    config = load_config()
except Exception as e:
    st.error(f"gagal baca config.json: {e}")
    st.stop()

# --- session state defaults ---
if "current_topic_id" not in st.session_state:
    st.session_state.current_topic_id = None
if "custom_styles" not in st.session_state:
    st.session_state.custom_styles = []

# --- sidebar: topic management ---
current_topic = sidebar.render()

# --- header ---
st.markdown(
    '<div style="text-align:center; padding:6px 0 14px 0;">'
    '<h1 style="margin-bottom:2px;">LaTeX AI Editor</h1>'
    '<p style="color:gray; margin-top:0;">topic-based knowledge base & document generator</p>'
    "</div>",
    unsafe_allow_html=True,
)

# --- cek apakah ada topik aktif ---
if not current_topic:
    st.info("pilih atau buat topik baru di sidebar untuk mulai.")
    st.stop()

# --- tabs ---
tab_kb, tab_gen, tab_review_tab = st.tabs([
    "Knowledge Base",
    "Generate LaTeX",
    "Review & Revise",
])

with tab_kb:
    tab_knowledge.render(current_topic, config)

with tab_gen:
    tab_generate.render(current_topic, config)

with tab_review_tab:
    tab_review.render(current_topic, config)

# --- footer ---
st.markdown("---")
st.caption("latex ai editor | config via config.json | topics stored in data/topics.json")