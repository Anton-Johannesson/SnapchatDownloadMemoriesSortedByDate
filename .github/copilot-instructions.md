# AI Coding Agent Instructions

These instructions help AI agents work productively in this repository.

## Big Picture
- Single-purpose Python script that downloads Snapchat Memories from a JSON export and saves them to disk.
- No frameworks, tests, or external packages; standard library only. Keep solutions simple, surgical, and Windows-friendly.

## Code Map
- import_json.py — Entry script. Configure `JSON_FILE` (input export) and `OUTPUT_DIR` (download target). Uses `json`, `os`, and `urllib.request` only.
- README.md — Short, high-level description.

## Data & Behavior
- Input JSON must contain top-level key: `Saved Media` (array of items).
- Each item: `Media Type` (e.g., "Video"), `Media Download Url` (HTTP link), and a date field.
- Date detection: tries `Date`, `Created`, `Timestamp`, `Creation Timestamp` in multiple formats.
- File extension: `.mp4` when `media_type.lower() == "video"`, otherwise `.jpg`.
- Filenames: zero-padded sequence `00001.ext`, `00002.ext`, … determined by array order.
- **Folder structure:** Creates `OUTPUT_DIR/Year/Month/` (2016–2025, January–December) plus `Unsorted/` for items missing dates.
- Idempotency: scans entire folder tree for existing filenames to avoid re-downloads.
- Creates folders if missing; prints progress; download errors are caught and logged per item.

## How To Run (Windows)
- Edit constants at top of `import_json.py`:
  - `JSON_FILE = "C:\\path\\to\\memories_history.json"`
  - `OUTPUT_DIR = "C:\\path\\to\\Downloads\\Snapchat"`
- Run from repo root:
  - PowerShell: `python .\import_json.py`
- Python 3 is required; there are no extra dependencies.

## Project Conventions
- Keep standard-library only unless asked otherwise; prefer `urllib.request` for downloads.
- Preserve the current filename scheme (5-digit zero-padding) and extension mapping.
- Maintain skip-on-exist behavior for idempotent reruns.
- Use `os.path` joins and handle Windows paths carefully.

## Safe Changes For Agents
- When adding functionality (e.g., CLI flags via `argparse`), keep current constants as defaults for backward compatibility.
- If introducing date-based organization (when specifically requested), gate behind an option and keep skip/idempotency logic intact.
- Avoid breaking changes to the default behavior without an opt-in switch.

## Gotchas
- Snapchat download URLs may expire; failures will print but be resilient per-item.
- If the JSON schema differs, prefer defensive access (e.g., `.get(...)`) and keep non-fatal on missing fields.

## Scope & Style
- Make minimal, focused patches.
- Don’t introduce heavy structure (no frameworks, no test harness) unless requested.
- Follow the existing straightforward, procedural style.
