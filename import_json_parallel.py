import json
import os
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

JSON_FILE = r"/path/to/memories_history.json"
OUTPUT_DIR = r"/path/to/Snapchat Memories Memories Parallel Download"
FAILED_LOG = os.path.join(OUTPUT_DIR, "failed_downloads.txt")

# Number of parallel downloads (5-10 is usually safe)
MAX_WORKERS = 8

# Month names for folder creation
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Date field names to try (Snapchat exports vary)
DATE_FIELDS = ["Date", "Created", "Timestamp", "Creation Timestamp", "date", "created"]

# Thread-safe counters
lock = threading.Lock()
stats = {"downloaded": 0, "skipped": 0, "failed": 0, "processed": 0}
failed_items = []  # Store failed downloads for retry
start_time = None


def parse_date(item):
    """Try to extract a datetime from the item using known date field names."""
    for field in DATE_FIELDS:
        raw = item.get(field)
        if not raw:
            continue
        for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw.split(" UTC")[0].strip(), fmt)
            except ValueError:
                continue
    return None


def ensure_folder_structure(base_dir):
    """Create Snapchat Memories/Year/Month folder structure."""
    for year in range(2016, 2026):
        for month in MONTHS:
            path = os.path.join(base_dir, str(year), month)
            os.makedirs(path, exist_ok=True)
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


def download_item(item, index, existing_files, base_dir, total_items):
    """Download a single item. Returns (filename, status, message, item_data)."""
    media_type = item.get("Media Type", "").lower()
    ext = ".mp4" if media_type == "video" else ".jpg"
    filename = f"{index:05d}{ext}"

    if filename in existing_files:
        with lock:
            stats["skipped"] += 1
            stats["processed"] += 1
        return (filename, "skipped", None, None)

    url = item.get("Media Download Url")
    if not url:
        with lock:
            stats["processed"] += 1
        return (filename, "no_url", None, None)

    dt = parse_date(item)
    folder = get_target_folder(base_dir, dt)
    filepath = os.path.join(folder, filename)
    date_label = dt.strftime("%Y-%m") if dt else "Unsorted"

    try:
        urllib.request.urlretrieve(url, filepath)
        with lock:
            stats["downloaded"] += 1
            stats["processed"] += 1
        return (filename, "ok", date_label, None)
    except Exception as e:
        with lock:
            stats["failed"] += 1
            stats["processed"] += 1
        return (filename, "failed", str(e), {"index": index, "url": url, "item": item})


def format_time(seconds):
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def get_progress_string(total_items):
    """Generate progress string with ETA."""
    processed = stats["processed"]
    
    if start_time is None or processed == 0:
        return f"[0/{total_items}] Starting..."
    
    elapsed = time.time() - start_time
    
    rate = processed / elapsed  # items per second
    remaining = total_items - processed
    eta_seconds = remaining / rate if rate > 0 else 0
    
    percent = (processed / total_items) * 100
    return f"[{processed}/{total_items}] {percent:.1f}% | ETA: {format_time(eta_seconds)}"


def save_failed_log():
    """Save failed downloads to a file for retry."""
    if not failed_items:
        return
    
    with open(FAILED_LOG, "w", encoding="utf-8") as f:
        f.write(f"# Failed downloads - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total failed: {len(failed_items)}\n\n")
        for item in failed_items:
            f.write(f"Index: {item['index']}\n")
            f.write(f"URL: {item['url']}\n")
            f.write(f"Error: {item.get('error', 'Unknown')}\n")
            f.write("-" * 50 + "\n")
    print(f"\n📝 Failed downloads saved to: {FAILED_LOG}")


# ─────────────────────────────────────────────────────────────────────────────
# Main script
# ─────────────────────────────────────────────────────────────────────────────

print(f"Setting up folder structure...")
ensure_folder_structure(OUTPUT_DIR)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

media_items = data.get("Saved Media", [])
existing_files = build_existing_files_index(OUTPUT_DIR)
total_items = len(media_items)

print(f"Found {total_items} items. Downloading with {MAX_WORKERS} parallel workers...\n")

start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(download_item, item, i, existing_files, OUTPUT_DIR, total_items): i
        for i, item in enumerate(media_items, start=1)
    }

    for future in as_completed(futures):
        filename, status, msg, item_data = future.result()
        progress = get_progress_string(total_items)
        
        if status == "ok":
            print(f"✓ {filename} → {msg}  {progress}")
        elif status == "failed":
            print(f"❌ {filename}: {msg}  {progress}")
            if item_data:
                item_data["error"] = msg
                failed_items.append(item_data)
        # skipped and no_url are silent

elapsed = time.time() - start_time
print(f"\n{'='*60}")
print(f"✅ Done in {format_time(elapsed)}!")
print(f"   Downloaded: {stats['downloaded']}")
print(f"   Skipped:    {stats['skipped']}")
print(f"   Failed:     {stats['failed']}")

# Save failed downloads for retry
save_failed_log()
