"""
topics.py - manajemen topik/knowledge base
setiap topik punya knowledge base, latex, dan history revisi sendiri.
data disimpan di data/topics.json
"""

import json
import os
import uuid
import time
from config import DATA_DIR

TOPICS_FILE = os.path.join(DATA_DIR, "topics.json")


def _ensure_data_dir():
    """pastikan folder data dan pdfs ada"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "pdfs"), exist_ok=True)


def load_all():
    """load semua topik dari file json"""
    _ensure_data_dir()
    if not os.path.exists(TOPICS_FILE):
        return []
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("topics", [])


def save_all(topics):
    """simpan semua topik ke file json"""
    _ensure_data_dir()
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)


def create(name):
    """bikin topik baru, return topic id"""
    topics = load_all()
    topic_id = str(uuid.uuid4())[:8]
    new_topic = {
        "id": topic_id,
        "name": name,
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "files": [],
        "file_contents": {},
        "extracted_content": "",
        "latex_code": "",
        "revision_history": [],
        "style_used": "",
    }
    topics.append(new_topic)
    save_all(topics)
    return topic_id


def get_by_id(topic_id):
    """ambil data topik berdasarkan id"""
    topics = load_all()
    for t in topics:
        if t["id"] == topic_id:
            return t
    return None


def update(topic_id, updates):
    """update field tertentu dari topik"""
    topics = load_all()
    for i, t in enumerate(topics):
        if t["id"] == topic_id:
            topics[i].update(updates)
            break
    save_all(topics)


def delete(topic_id):
    """hapus topik beserta pdf-nya"""
    topics = load_all()
    topics = [t for t in topics if t["id"] != topic_id]
    save_all(topics)

    pdf_path = os.path.join(DATA_DIR, "pdfs", f"{topic_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)


def rename(topic_id, new_name):
    """ganti nama topik"""
    update(topic_id, {"name": new_name})


def save_pdf(topic_id, pdf_bytes):
    """simpan compiled pdf ke disk"""
    _ensure_data_dir()
    pdf_path = os.path.join(DATA_DIR, "pdfs", f"{topic_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)


def load_pdf(topic_id):
    """load compiled pdf dari disk, return bytes atau None"""
    pdf_path = os.path.join(DATA_DIR, "pdfs", f"{topic_id}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            return f.read()
    return None