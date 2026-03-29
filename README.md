# Discord Drive Organizer Bot (Starter)

A starter scaffold for a Discord bot that organizes uploaded documents into a designated Google Drive folder and allows retrieval using slash commands.

## Implemented commands
- `/upload` — validates file, names it with convention, uploads via storage adapter, saves metadata.
- `/find` — searches metadata for matching files.

> Note: Google Drive adapter is currently a placeholder and returns mock IDs/links. Replace internals in `src/storage/drive_adapter.py` with real Drive API calls.

## Quick start
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env file and configure:
   ```bash
   cp .env.example .env
   ```
4. Run the bot:
   ```bash
   PYTHONPATH=src python src/main.py
   ```

## Structure
- `src/commands/` — slash command handlers.
- `src/services/` — naming and business logic.
- `src/storage/` — storage abstraction and Drive adapter.
- `src/repositories/` — metadata repository (in-memory for starter).
- `src/config/` — settings/logging.
