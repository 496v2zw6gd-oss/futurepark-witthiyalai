# Rongrien Futurepark Witthiyalai — fictional school portal

A responsive Flask + SQLite website for a fictional school series. It includes a bilingual-style school identity, student search, student directory, administrator login, and admin-only add/delete controls.

## Run locally

1. Install Python 3.10+.
2. In this folder, create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Set a strong secret and admin password (examples below).
5. Run: `python app.py`
6. Open `http://127.0.0.1:5000`.

### macOS / Linux
```bash
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="use-a-long-unique-password"
python app.py
```

### Windows PowerShell
```powershell
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "use-a-long-unique-password"
python app.py
```

The demo's local default login is `admin` / `change-this-before-deploying`. Change it before use. The app stores records in `futurepark.db`, created automatically on first run. The seeded student records are fictional. **Vorakorn Taychapan is intentionally absent**, so that search returns `STUDENT NOT FOUND`.

## Deployment / production notes

- Set `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` to strong unique values in your hosting provider's secret/environment settings.
- Use a production WSGI server such as Gunicorn (`gunicorn app:app`) behind HTTPS; do not expose Flask's development server.
- Use persistent disk storage for `futurepark.db`, or replace SQLite with a managed database for multi-instance deployments.
- Add rate limiting, audit logging, backups, and a proper account-management flow before real-world use.
- This is a fictional prop, not an official school system. Do not enter real student personal data. The deletion feature deletes only sample records in this local demo database.
