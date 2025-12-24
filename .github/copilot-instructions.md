# AI Coding Agent Instructions

These instructions help AI agents work productively in this repository.

## Big Picture
- Downloads Snapchat Memories from a JSON export and organizes them into `Year/Month/` folders.
- Two scripts: sequential (`import_json.py`) and parallel (`import_json_parallel.py`).
- **Standard library only**—no external packages. Keep solutions simple and Windows-friendly.

## Code Map
| File | Purpose |
|------|---------|
| `import_json.py` | Sequential downloader (simple, single-threaded) |
| `import_json_parallel.py` | Parallel downloader (`ThreadPoolExecutor`, 8 workers, progress/ETA display) |
| `README.md` | User-facing documentation with setup instructions |

## Data & Behavior
- **Input:** JSON with `"Saved Media"` array. Each item has `Media Type`, `Media Download Url`, and a date field.
- **Date fields tried:** `Date`, `Created`, `Timestamp`, `Creation Timestamp` (case variations).
- **Date formats:** `%Y-%m-%d %H:%M:%S %Z`, `%Y-%m-%d %H:%M:%S`, `%Y-%m-%dT%H:%M:%SZ`, `%Y-%m-%d`.
- **Extension:** `.mp4` for `video`, `.jpg` otherwise.
- **Filename:** 5-digit zero-padded index from array order (`00001.jpg`, `00002.mp4`, …).
- **Folder structure:** `OUTPUT_DIR/Year/Month/` (2016–2025) + `Unsorted/` for items missing dates.
- **Idempotency:** Scans entire tree for existing filenames before downloading.

## How To Run
1. Set constants at top of script:
   ```python
   JSON_FILE = r"C:\path\to\memories_history.json"
   OUTPUT_DIR = r"C:\path\to\Snapchat Memories"
   ```
2. Run: `python import_json.py` or `python import_json_parallel.py`

## Project Conventions
- **Standard library only:** `json`, `os`, `urllib.request`, `datetime`, `threading`, `concurrent.futures`.
- Use `os.path.join()` for paths; handle Windows backslashes with raw strings.
- Preserve 5-digit filename scheme and `.mp4`/`.jpg` extension mapping.
- Maintain skip-on-exist idempotency for safe reruns.
- Prefer defensive access (`.get(...)`) for JSON fields.

## Parallel Script Specifics
- `MAX_WORKERS = 8` controls thread count.
- Thread-safe counters via `threading.Lock()`.
- Failed downloads logged to `failed_downloads.txt` in output dir.
- Progress shows `[processed/total] percent | ETA: Xm Ys`.

## Safe Changes For Agents
- Keep current constants as defaults when adding CLI flags (`argparse`).
- Gate new features behind opt-in switches; don't break default behavior.
- Keep both scripts in sync when modifying shared logic (date parsing, folder structure).

## Gotchas
- Snapchat URLs expire; failures are logged per-item but don't halt the script.
- Year range (2016–2025) is hardcoded in `ensure_folder_structure()`—extend if needed.
- JSON schema may vary; handle missing fields gracefully.

## Scope & Style
- Minimal, focused patches. Procedural style, no classes or frameworks.
- Don't introduce test harnesses or complex structure unless explicitly requested.
