"""Snapchat Memories Download & Organization Tool

Author: Anton Johannesson
Description: Downloads Snapchat Memories from JSON export and organizes them by date
             into a folder structure (Year/Month). Single-threaded version.
Version: 1.1
License: MIT
"""

import json
import os
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime

JSON_FILE = r"" #Change to where JSON file is located
OUTPUT_DIR = r"" #Change to desired output directory

TIMEOUT = 30   # seconds per request
RETRIES = 3    # attempts per file

# Month names for folder creation
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Date field names to try (Snapchat exports vary)
DATE_FIELDS = ["Date", "Created", "Timestamp", "Creation Timestamp", "date", "created"]


def parse_date(item):
    """Try to extract a datetime from the item using known date field names."""
    for field in DATE_FIELDS:
        raw = item.get(field)
        if not raw:
            continue
        # Try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw.split(" UTC")[0].strip(), fmt)
            except ValueError:
                continue
    return None


def get_target_folder(base_dir, dt):
    """Return the folder path for a given datetime, or Unsorted if None."""
    if dt is None:
        return os.path.join(base_dir, "Unsorted")
    year = str(dt.year)
    month = MONTHS[dt.month - 1]
    return os.path.join(base_dir, year, month)


def build_existing_files_index(base_dir):
    """Build a set of all existing filenames across the entire folder structure."""
    existing = set()
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            existing.add(f)
    return existing


def fetch_to_file(url, filepath, retries=RETRIES, timeout=TIMEOUT):
    """Download url to filepath atomically (via .part) with timeout and retry."""
    if not url.lower().startswith("https://"):
        raise ValueError("Only https:// URLs are allowed")
    tmp = filepath + ".part"
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as out:
                shutil.copyfileobj(resp, out)
            os.replace(tmp, filepath)
            return
        except Exception as e:
            last_error = e
            if os.path.exists(tmp):
                os.remove(tmp)
            # Client errors (expired link etc.) will not fix themselves, except 429
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500 and e.code != 429:
                break
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise last_error


# ─────────────────────────────────────────────────────────────────────────────
# Main script
# ─────────────────────────────────────────────────────────────────────────────

if not JSON_FILE or not OUTPUT_DIR:
    raise SystemExit("Set JSON_FILE and OUTPUT_DIR at the top of the script first.")

print("Setting up output folder...")
os.makedirs(os.path.join(OUTPUT_DIR, "Unsorted"), exist_ok=True)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

media_items = data.get("Saved Media", [])
existing_files = build_existing_files_index(OUTPUT_DIR)

downloaded = 0
skipped = 0
failed = 0

for i, item in enumerate(media_items, start=1):
    media_type = item.get("Media Type", "").lower()
    ext = ".mp4" if media_type == "video" else ".jpg"
    filename = f"{i:05d}{ext}"

    if filename in existing_files:
        skipped += 1
        continue

    url = item.get("Media Download Url")
    if not url:
        continue

    dt = parse_date(item)
    folder = get_target_folder(OUTPUT_DIR, dt)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    date_label = dt.strftime("%Y-%m") if dt else "Unsorted"
    print(f"Downloading {filename} → {date_label}")

    try:
        fetch_to_file(url, filepath)
        downloaded += 1
    except Exception as e:
        print(f"❌ Failed {filename}: {e}")
        failed += 1

print(f"\n✅ Done! Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
