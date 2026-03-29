# Document-Organizer-Bot

A Discord bot that stores project files in Google Drive, auto-organizes them into folders, and supports search/retrieval from Discord slash commands.

## Features
- `/upload` to validate and upload files to Drive folders: `Project / Category / YYYY-MM`
- Duplicate detection with checksum and automatic versioning
- `/find` for metadata search (query/project/category/tags/uploader)
- `/list_docs`, `/move`, `/new_version`, and `/help_docs`
- SQLite/Postgres-ready metadata persistence via SQLAlchemy

## 1) Google + Discord setup

### A. Create Google Drive service account
1. Create a Google Cloud project.
2. Enable **Google Drive API**.
3. Create a service account and download JSON credentials.
4. Save credentials to:
   - `secrets/google-service-account.json`
5. Share your target Drive root folder with the service account email.
6. Copy that folder ID into `.env` as `GOOGLE_DRIVE_ROOT_FOLDER_ID`.

### B. Create Discord bot app
1. Open Discord Developer Portal.
2. Create application + bot and copy token.
3. Enable **Message Content Intent** if needed (slash commands mainly do not require it).
4. Invite bot to your server with `applications.commands` + `bot` scopes.


### Discord role/channel example (from your server)
Use your real IDs in `.env` (these are safe to share; they are not secrets):

```env
DISCORD_ADMIN_ROLE_IDS=1487744861162573865
DISCORD_UPLOADER_ROLE_IDS=1487746052063756419
# Optional read-only role(s):
DISCORD_VIEWER_ROLE_IDS=
ALLOWED_CHANNEL_IDS=1479314479488696403
```

With this setup, only users with `Doc Admin` or `Doc Uploader` can run commands, and they can only run them in your documents channel.

## 2) Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`:
- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- role ID lists (`DISCORD_ADMIN_ROLE_IDS`, etc.)
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_ROOT_FOLDER_ID`

Run bot:

```bash
PYTHONPATH=src python src/main.py
```

## 3) Using in Discord

1. Give yourself a role listed in `DISCORD_UPLOADER_ROLE_IDS` (or admin role).
2. In allowed channel, run:
   - `/upload file:<attachment> project:<name> category:<name> title:<optional> tags:<optional>`
3. Retrieve files with:
   - `/find query:<keyword>`
   - `/find project:<project> category:<category>`
4. List recent docs:
   - `/list_docs limit:10`
5. Move a doc:
   - `/move doc_id:<id> project:<new> category:<new>`
6. Upload a new version:
   - `/new_version doc_id:<id> file:<attachment>`

## 4) Notes
- Database defaults to SQLite (`bot.db`). Change `DATABASE_URL` for Postgres.
- Slash commands are synced at startup (`setup_hook`).
- Files are private by Drive permissions; bot returns Drive links for retrieval.
