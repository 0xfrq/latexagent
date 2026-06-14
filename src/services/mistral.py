"""
mistral.py - integrasi mistral ocr api
support 7 key dengan round-robin switching
"""

import base64
import json
import requests

# global counter buat round robin
_key_index = 0


def get_next_mistral_key(config):
    """
    ambil key mistral berikutnya secara round-robin dari 7 key.
    return (key_name, key_value).
    """
    global _key_index
    keys_dict = config.get("mistral_keys", {})

    # urutkan berdasarkan nama (mistralkey1 - mistralkey7)
    sorted_keys = sorted(keys_dict.items(), key=lambda x: x[0])
    if not sorted_keys:
        raise ValueError("tidak ada mistral key di config.json!")

    # filter key yang masih placeholder
    valid_keys = [(k, v) for k, v in sorted_keys if v and "your_" not in v]
    if not valid_keys:
        raise ValueError("semua mistral key masih placeholder! isi dulu di config.json")

    # round robin
    name, value = valid_keys[_key_index % len(valid_keys)]
    _key_index += 1
    return name, value


def ocr(file_bytes, filename, config):
    """
    kirim file ke mistral ocr api buat extract teks.
    otomatis pakai key berikutnya (round-robin).
    return tuple (extracted_text, key_name_used).
    """
    key_name, api_key = get_next_mistral_key(config)

    b64_data = base64.b64encode(file_bytes).decode("utf-8")

    # tentukan mime type dari ekstensi file
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    mime_map = {
        "pdf": "application/pdf", "png": "image/png",
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "tiff": "image/tiff", "tif": "image/tiff",
        "bmp": "image/bmp", "webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "application/pdf")
    data_uri = f"data:{mime_type};base64,{b64_data}"

    url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": data_uri,
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # extract teks dari response
    if "pages" in data:
        texts = []
        for page in data["pages"]:
            if "markdown" in page:
                texts.append(page["markdown"])
            elif "text" in page:
                texts.append(page["text"])
        return "\n\n---\n\n".join(texts), key_name
    elif "choices" in data:
        return data["choices"][0].get("message", {}).get("content", ""), key_name
    else:
        return json.dumps(data), key_name