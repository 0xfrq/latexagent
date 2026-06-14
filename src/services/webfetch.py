"""
webfetch.py - fetch konten web langsung via jina-reader style api
bukan lewat llm model, tapi langsung fetch halaman web-nya
"""

import json
import requests
from config import get_web_fetch_config


def fetch(url, config):
    """
    fetch konten web dari url menggunakan web fetch api.
    return string markdown konten halaman.
    """
    wf = get_web_fetch_config(config)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {wf['api_key']}",
    }
    payload = {
        "model": wf["model"],
        "url": url,
        "format": "markdown",
        "max_characters": 0,
    }

    resp = requests.post(wf["url"], headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # extract konten dari response
    if "data" in data:
        if isinstance(data["data"], dict):
            return data["data"].get("content", data["data"].get("markdown", json.dumps(data["data"])))
        return str(data["data"])
    elif "content" in data:
        return data["content"]
    else:
        return json.dumps(data, indent=2)