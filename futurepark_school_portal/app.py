import os
import sqlite3
import secrets
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "futurepark.db"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Configure these before deployment. Never use the demo defaults on a public server.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-before-deploying")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                classroom TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active'
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            # Fictional sample records only. Vorakorn Taychapan is intentionally absent.
            samples = [
                ("FP260001", "Nattapong Srisuk", "M.4/1", "Active"),
                ("FP260002", "Pimchanok Kittisak", "M.4/1", "Active"),
                ("FP260003", "Thanawat Wongsa", "M.4/2", "Active"),
                ("FP260004", "Kanyarat Chaiya", "M.5/1", "Active"),
                ("FP260005", "Phurinat Sombat", "M.6/2", "Active"),
            ]
            conn.executemany(
                "INSERT INTO students(student_id, full_name, classroom, status) VALUES(?,?,?,?)",
                samples
            )

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]

@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token, "is_admin": bool(session.get("admin"))}

@app.before_request
def protect_post_requests():
    if request.method == "POST":
        expected = session.get("_csrf")
        supplied = request.form.get("_csrf", "")
        if not expected or not secrets.compare_digest(expected, supplied):
            abort(400, description="Invalid or expired form token. Please reload and try again.")

@app.route("/")
def home():
    with db() as conn:
        student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    return render_template("home.html", student_count=student_count)

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        # Exact match or partial match, case-insensitive.
        with db() as conn:
            results = conn.execute(
                """SELECT student_id, full_name, classroom, status
                   FROM students
                   WHERE full_name LIKE ? OR student_id LIKE ?
                   ORDER BY full_name LIMIT 30""",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
    return render_template("search.html", query=query, results=results, searched=bool(query))

@app.route("/students")
def students():
    with db() as conn:
        rows = conn.execute(
            "SELECT student_id, full_name, classroom, status FROM students ORDER BY student_id"
        ).fetchall()
    return render_template("students.html", students=rows)

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # Constant-time password-hash check; password is configured via environment variable.
        stored_hash = generate_password_hash(ADMIN_PASSWORD)
        if secrets.compare_digest(username, ADMIN_USERNAME) and check_password_hash(stored_hash, password):
            session.clear()
            session["admin"] = True
            session["_csrf"] = secrets.token_urlsafe(32)
            flash("Signed in to the fictional administration portal.", "success")
            return redirect(url_for("admin"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")

@app.post("/admin/logout")
@admin_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin():
    with db() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()
    return render_template("admin.html", students=rows)

@app.post("/admin/students/add")
@admin_required
def add_student():
    student_id = request.form.get("student_id", "").strip()
    full_name = request.form.get("full_name", "").strip()
    classroom = request.form.get("classroom", "").strip()
    if not all((student_id, full_name, classroom)):
        flash("Please complete all student fields.", "error")
    else:
        try:
            with db() as conn:
                conn.execute(
                    "INSERT INTO students(student_id, full_name, classroom) VALUES(?,?,?)",
                    (student_id, full_name, classroom)
                )
            flash("Fictional student record added.", "success")
        except sqlite3.IntegrityError:
            flash("That student ID already exists.", "error")
    return redirect(url_for("admin"))

@app.post("/admin/students/<int:student_pk>/delete")
@admin_required
def delete_student(student_pk):
    with db() as conn:
        row = conn.execute("SELECT full_name FROM students WHERE id=?", (student_pk,)).fetchone()
        if row:
            conn.execute("DELETE FROM students WHERE id=?", (student_pk,))
            flash(f"Deleted fictional demo record: {row['full_name']}.", "success")
        else:
            flash("That record no longer exists.", "error")
    return redirect(url_for("admin"))

@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Bad request")), 400

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
