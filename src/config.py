"""
config.py - loader buat config.json
config.json ada di root project, bukan di src/
"""

import json
import os

# path ke root project (parent dari src/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
DATA_DIR = os.path.join(ROOT_DIR, "data")


def load_config():
    """baca config.json dari root project"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_router_config(config):
    """shortcut ambil router config"""
    r = config.get("router", {})
    return {
        "base_url": r.get("base_url", ""),
        "api_key": r.get("api_key", ""),
        "latex_model": r.get("latex_model", ""),
    }


def get_web_fetch_config(config):
    """ambil config buat web fetch"""
    wf = config.get("web_fetch", {})
    router = config.get("router", {})
    return {
        "url": wf.get("url", "http://localhost:20128/v1/web/fetch"),
        "model": wf.get("model", "jina-reader"),
        "api_key": router.get("api_key", ""),
    }