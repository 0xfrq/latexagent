"""
youtube.py - extract caption/subtitle dari video youtube
support berbagai format url dan multiple language
"""

import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url):
    """extract video id dari berbagai format url youtube"""
    patterns = [r"(?:v=|/v/|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_captions(url):
    """
    extract caption/subtitle dari video youtube dengan timestamp.
    return string dengan format [mm:ss] text per baris.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"tidak bisa extract video id dari url: {url}")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        raise ValueError(f"gagal ambil daftar transcript: {e}")

    # prioritaskan: manual > auto (en/id) > apapun yang ada
    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript()
    except Exception:
        pass
    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(["en", "id"])
        except Exception:
            pass
    if transcript is None:
        try:
            for t in transcript_list:
                transcript = t
                break
        except Exception:
            pass
    if transcript is None:
        raise ValueError(f"tidak ada transcript untuk video {video_id}")

    entries = transcript.fetch()
    lines = []
    for entry in entries:
        if isinstance(entry, dict):
            ts = entry.get("start", 0)
            text = entry.get("text", "")
        else:
            ts = entry.start
            text = entry.text
        minutes = int(ts // 60)
        seconds = int(ts % 60)
        lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")

    return f"youtube video id: {video_id}\n\n" + "\n".join(lines)