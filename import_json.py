"""Snapchat Memories Download & Organization Tool

Author: Anton Johannesson
Description: Downloads Snapchat Memories from JSON export and organizes them by date
             into a folder structure (Year/Month). Single-threaded version.
Version: 1.0
License: MIT
"""

import json
import os
import urllib.request
from datetime import datetime

JSON_FILE = r"" #Change to where JSON file is located
OUTPUT_DIR = r"" #Change to desired output directory

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


def ensure_folder_structure(base_dir):
    """Create Snapchat Memories/Year/Month folder structure."""
    for year in range(2016, 2026):  # change here for desired years
        for month in MONTHS:
            path = os.path.join(base_dir, str(year), month)
            os.makedirs(path, exist_ok=True)
    # Also create an "Unsorted" folder for items without dates
    os.makedirs(os.path.join(base_dir, "Unsorted"), exist_ok=True)


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


# ─────────────────────────────────────────────────────────────────────────────
# Main script
# ─────────────────────────────────────────────────────────────────────────────

print("Setting up folder structure...")
ensure_folder_structure(OUTPUT_DIR)

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
    filepath = os.path.join(folder, filename)

    date_label = dt.strftime("%Y-%m") if dt else "Unsorted"
    print(f"Downloading {filename} → {date_label}")

    try:
        urllib.request.urlretrieve(url, filepath)
        downloaded += 1
    except Exception as e:
        print(f"❌ Failed {filename}: {e}")
        failed += 1

print(f"\n✅ Done! Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
