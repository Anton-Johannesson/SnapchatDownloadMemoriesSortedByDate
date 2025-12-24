# SnapchatDownloadMemoriesSortedByDate

Download your Snapchat memories and have them automatically sorted into Year/Month folders.

---

## Why?

Snapchat introduced a **5GB limit on Memories**. To keep a complete backup, you need to download your data manually. This Python script downloads all your Snapchat memories from a JSON export and organizes them by date.

As seen on: https://www.tiktok.com/@giraintech/video/7583879890265558280

---

## Features

- **Auto-sorted by date:** Creates `Year/Month/` folders (2016–2025, January–December)
- **Auto-sorted by date:** Creates `Year/Month/` folders (2016–2025, January–December), dates can be changed, see code
- **Unsorted fallback:** Items without dates go to an `Unsorted/` folder
- **Idempotent:** Re-run safely — already downloaded files are skipped
- **Resilient:** Failed downloads are logged but don't stop the script
- **No dependencies:** Uses only Python standard library

---

## Scripts

| Script | Speed | Best for |
|--------|-------|----------|
| `import_json.py` | Sequential (1 at a time) | Small exports, simple use |
| `import_json_parallel.py` | **Parallel (8 at a time)** | Large exports, 3-5x faster |

---

## Getting Your Snapchat Data

1. Open Snapchat → Settings → My Data
2. Request your Memories and select **JSON formatting**
3. Snapchat will email you a download link (ZIP file)
4. Extract the ZIP and find the `memories_history.json` file

---

## How to Use

### Option 1: Standard Download

1. Open `import_json.py` and set these two variables:

```python
JSON_FILE = r"C:\path\to\memories_history.json"
OUTPUT_DIR = r"C:\path\to\Snapchat Memories"
```

2. Run the script:

```bash
python import_json.py
```

### Option 2: Fast Parallel Download (Recommended)

1. Open `import_json_parallel.py` and set:

```python
JSON_FILE = r"C:\path\to\memories_history.json"
OUTPUT_DIR = r"C:\path\to\Snapchat Memories"
```

2. Run the script:

```bash
python import_json_parallel.py
```

**Parallel features:**
- Downloads 8 files simultaneously (configurable via `MAX_WORKERS`)
- Shows real-time progress with ETA: `[150/3687] 4.1% | ETA: 11m 22s`
- Saves failed downloads to `failed_downloads.txt` for retry

> **Tip:** Use `r"..."` (raw strings) on Windows to avoid backslash issues.  
> **macOS/Linux:** Use forward slashes, e.g., `/Volumes/Drive/Snapchat Memories`

---

## Output Structure

```
Snapchat Memories/
├── 2024/
│   ├── January/
│   ├── February/
│   └── ...
├── 2025/
│   ├── November/
│   └── December/
└── Unsorted/
```

---

## Requirements

- Python 3.x
- Internet connection
- Snapchat JSON export (`memories_history.json`)

---

## Acknowledgments

Inspired by [girachawda](https://github.com/girachawda)'s work on Snapchat memory management.
