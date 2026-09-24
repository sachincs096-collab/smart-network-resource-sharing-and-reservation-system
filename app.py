import json
import logging
import os
import platform
import re
import socket
import subprocess
import threading
import time
from datetime import datetime
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import FLASK_HOST, FLASK_PORT, SECRET_KEY
from database.database import close_db, get_db, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.teardown_appcontext(close_db)
app.config["network_lock"] = threading.Lock()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def server_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
        probe.close()
        return address
    except OSError:
        return "127.0.0.1"


def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access is required.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def validate_resource_payload(payload):
    name = str(payload.get("name", "")).strip()
    resource_type = str(payload.get("type", "")).strip()
    location = str(payload.get("location", "")).strip()
    ip_address = str(payload.get("ip_address", "")).strip()
    description = str(payload.get("description", "")).strip()
    try:
        port = int(payload.get("port", 0))
    except (TypeError, ValueError):
        port = 0
    if not all((name, resource_type, location, ip_address)) or not re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", ip_address):
        return None, "Name, type, location, and a valid IPv4 address are required."
    if any(int(part) > 255 for part in ip_address.split(".")) or not 1 <= port <= 65535:
        return None, "Use an IPv4 address and port between 1 and 65535."
    return (name, resource_type, location, ip_address, port, description), None


def record_client_activity(endpoint):
    db = get_db()
    ip = client_ip()
    db.execute(
        "INSERT INTO client_connections (client_ip, last_seen, request_count, last_request) VALUES (?, CURRENT_TIMESTAMP, 1, ?) "
        "ON CONFLICT(client_ip) DO UPDATE SET last_seen=CURRENT_TIMESTAMP, request_count=request_count+1, last_request=excluded.last_request",
        (ip, endpoint),
    )
    db.commit()


@app.before_request
def before_request():
    request._started_at = time.perf_counter()


@app.after_request
def after_request(response):
    try:
        duration_ms = round((time.perf_counter() - request._started_at) * 1000, 2)
        record_client_activity(request.path)
        db = get_db()
        db.execute(
            "INSERT INTO network_logs (client_ip, method, endpoint, status_code, request_time, response_time) VALUES (?, ?, ?, ?, ?, ?)",
            (client_ip(), request.method, request.path, response.status_code, int(time.time() * 1000), duration_ms),
        )
        db.commit()
    except Exception:
        app.logger.exception("Unable to write network log")
    return response


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.update(user_id=user["id"], name=user["name"], role=user["role"], ip_address=client_ip())
            get_db().execute("UPDATE users SET ip_address = ? WHERE id = ?", (client_ip(), user["id"]))
            get_db().commit()
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter a name, valid email, and password of at least 6 characters.", "error")
        else:
            try:
                db = get_db()
                db.execute("INSERT INTO users (name, email, password_hash, ip_address) VALUES (?, ?, ?, ?)", (name, email, generate_password_hash(password), client_ip()))
                db.commit()
                flash("Registration complete. You can now sign in.", "success")
                return redirect(url_for("login"))
            except Exception:
                flash("That email is already registered.", "error")
    return render_template("register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(message="Logged out")


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = db.execute("SELECT COUNT(*) total, SUM(status='AVAILABLE') available, SUM(status='RESERVED') reserved, SUM(status='OFFLINE') offline FROM resources").fetchone()
    active = db.execute("SELECT COUNT(*) FROM reservations WHERE user_id = ? AND status IN ('APPROVED', 'ACTIVE')", (session["user_id"],)).fetchone()[0]
    upcoming = db.execute("SELECT r.*, x.name resource_name FROM reservations r JOIN resources x ON x.id = r.resource_id WHERE r.user_id = ? AND r.status != 'CANCELLED' ORDER BY r.reservation_date, r.start_time LIMIT 4", (session["user_id"],)).fetchall()
    return render_template("dashboard.html", stats=stats, active=active, upcoming=upcoming, server_ip=server_ip(), port=FLASK_PORT)


@app.route("/resources")
@login_required
def resources_page():
    resources = get_db().execute("SELECT r.*, (SELECT u.name FROM reservations v JOIN users u ON u.id = v.user_id WHERE v.resource_id = r.id AND v.status IN ('APPROVED','ACTIVE') ORDER BY v.reservation_date, v.start_time LIMIT 1) current_user FROM resources r ORDER BY r.name").fetchall()
    return render_template("resources.html", resources=resources)


@app.route("/reservations")
@login_required
def reservations_page():
    reservations = get_db().execute("SELECT v.*, r.name resource_name, r.ip_address FROM reservations v JOIN resources r ON r.id = v.resource_id WHERE v.user_id = ? ORDER BY v.reservation_date DESC, v.start_time DESC", (session["user_id"],)).fetchall()
    return render_template("reservations.html", reservations=reservations)


@app.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    db = get_db()
    db.execute("UPDATE reservations SET status = 'CANCELLED' WHERE id = ? AND user_id = ? AND status IN ('PENDING','APPROVED')", (reservation_id, session["user_id"]))
    db.commit()
    flash("Reservation cancelled.", "success")
    return redirect(url_for("reservations_page"))


@app.route("/network")
@login_required
def network_page():
    return render_template("network.html", server_ip=server_ip(), port=FLASK_PORT, platform=platform.system())


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    counts = db.execute("SELECT COUNT(*) total, SUM(status='AVAILABLE') available, SUM(status='RESERVED') reserved, SUM(status='IN_USE') in_use, SUM(status='OFFLINE') offline FROM resources").fetchone()
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_reservations = db.execute("SELECT COUNT(*) FROM reservations WHERE status IN ('APPROVED','ACTIVE')").fetchone()[0]
    clients = db.execute("SELECT COUNT(*) FROM client_connections WHERE datetime(last_seen) >= datetime('now', '-10 minutes')").fetchone()[0]
    return render_template("admin_dashboard.html", counts=counts, users=users, active_reservations=active_reservations, clients=clients, server_ip=server_ip(), port=FLASK_PORT)


@app.route("/admin/resources", methods=["GET", "POST"])
@login_required
@admin_required
def admin_resources():
    db = get_db()
    if request.method == "POST":
        values, error = validate_resource_payload(request.form)
        if error:
            flash(error, "error")
        else:
            db.execute("INSERT INTO resources (name, type, location, ip_address, port, description) VALUES (?, ?, ?, ?, ?, ?)", values)
            db.commit()
            flash("Resource added to the LAN inventory.", "success")
    resources = db.execute("SELECT * FROM resources ORDER BY name").fetchall()
    return render_template("admin_resources.html", resources=resources)


@app.route("/admin/resources/<int:resource_id>/status", methods=["POST"])
@login_required
@admin_required
def update_resource_status(resource_id):
    status = request.form.get("status", "")
    if status in {"AVAILABLE", "RESERVED", "IN_USE", "OFFLINE"}:
        db = get_db()
        db.execute("UPDATE resources SET status = ? WHERE id = ?", (status, resource_id))
        db.commit()
    return redirect(url_for("admin_resources"))


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    return render_template("admin_users.html", users=get_db().execute("SELECT id, name, email, role, ip_address, created_at FROM users ORDER BY created_at DESC").fetchall())


@app.route("/admin/logs")
@login_required
@admin_required
def logs_page():
    return render_template("logs.html", logs=get_db().execute("SELECT * FROM network_logs ORDER BY id DESC LIMIT 100").fetchall())


@app.route("/api/register", methods=["POST"])
def api_register():
    payload = request.get_json(silent=True) or {}
    try:
        db = get_db()
        db.execute("INSERT INTO users (name, email, password_hash, ip_address) VALUES (?, ?, ?, ?)", (payload.get("name", "").strip(), payload.get("email", "").strip().lower(), generate_password_hash(payload.get("password", "")), client_ip()))
        db.commit()
        return jsonify(message="Registration successful"), 201
    except Exception:
        return jsonify(error="Registration failed; check required fields and email uniqueness."), 400


@app.route("/api/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    user = get_db().execute("SELECT * FROM users WHERE email = ?", (str(payload.get("email", "")).lower(),)).fetchone()
    if not user or not check_password_hash(user["password_hash"], payload.get("password", "")):
        return jsonify(error="Invalid credentials"), 401
    session.update(user_id=user["id"], name=user["name"], role=user["role"], ip_address=client_ip())
    return jsonify(message="Logged in", user={"id": user["id"], "name": user["name"], "role": user["role"], "ip_address": client_ip()})


@app.route("/api/resources", methods=["GET", "POST"])
@login_required
def api_resources():
    db = get_db()
    if request.method == "POST":
        if session.get("role") != "admin":
            return jsonify(error="Admin access required"), 403
        values, error = validate_resource_payload(request.get_json(silent=True) or {})
        if error:
            return jsonify(error=error), 400
        cursor = db.execute("INSERT INTO resources (name, type, location, ip_address, port, description) VALUES (?, ?, ?, ?, ?, ?)", values)
        db.commit()
        return jsonify(id=cursor.lastrowid, message="Resource created"), 201
    rows = db.execute("SELECT * FROM resources ORDER BY name").fetchall()
    return jsonify(resources=[dict(row) for row in rows])


@app.route("/api/resources/<int:resource_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_resource(resource_id):
    db = get_db()
    row = db.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    if row is None:
        return jsonify(error="Resource not found"), 404
    if request.method == "GET":
        return jsonify(resource=dict(row))
    if session.get("role") != "admin":
        return jsonify(error="Admin access required"), 403
    if request.method == "DELETE":
        db.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    else:
        fields = request.get_json(silent=True) or {}
        status = fields.get("status", row["status"])
        if status not in {"AVAILABLE", "RESERVED", "IN_USE", "OFFLINE"}:
            return jsonify(error="Invalid status"), 400
        db.execute("UPDATE resources SET status = ? WHERE id = ?", (status, resource_id))
    db.commit()
    return jsonify(message="Resource updated")


@app.route("/api/reservations", methods=["GET", "POST"])
@login_required
def api_reservations():
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT v.*, r.name resource_name FROM reservations v JOIN resources r ON r.id = v.resource_id WHERE v.user_id = ? ORDER BY v.reservation_date DESC", (session["user_id"],)).fetchall()
        return jsonify(reservations=[dict(row) for row in rows])
    payload = request.get_json(silent=True) or {}
    required = [payload.get(key) for key in ("resource_id", "reservation_date", "start_time", "end_time", "purpose")]
    if not all(required) or payload["start_time"] >= payload["end_time"]:
        return jsonify(error="Valid resource, date, purpose, and time range are required."), 400
    with app.config["network_lock"]:
        try:
            db.execute("BEGIN IMMEDIATE")
            resource = db.execute("SELECT * FROM resources WHERE id = ?", (payload["resource_id"],)).fetchone()
            if resource is None:
                db.rollback()
                return jsonify(error="Resource not found"), 404
            if resource["status"] == "OFFLINE":
                db.rollback()
                return jsonify(error="Resource is currently offline."), 409
            overlap = db.execute(
                "SELECT id FROM reservations WHERE resource_id = ? AND reservation_date = ? AND status != 'CANCELLED' AND start_time < ? AND end_time > ?",
                (payload["resource_id"], payload["reservation_date"], payload["end_time"], payload["start_time"]),
            ).fetchone()
            if overlap:
                db.rollback()
                return jsonify(error="Reservation failed. Resource is already reserved during this time."), 409
            cursor = db.execute("INSERT INTO reservations (resource_id, user_id, reservation_date, start_time, end_time, purpose) VALUES (?, ?, ?, ?, ?, ?)", (payload["resource_id"], session["user_id"], payload["reservation_date"], payload["start_time"], payload["end_time"], payload["purpose"].strip()))
            db.commit()
            return jsonify(id=cursor.lastrowid, message="Resource reserved successfully"), 201
        except Exception:
            db.rollback()
            app.logger.exception("Reservation transaction failed")
            return jsonify(error="Database error while creating reservation"), 500


@app.route("/api/network/status")
@login_required
def api_network_status():
    db = get_db()
    return jsonify(server_ip=server_ip(), server_port=FLASK_PORT, protocol="TCP/IP + HTTP", connected_clients=db.execute("SELECT COUNT(*) FROM client_connections WHERE datetime(last_seen) >= datetime('now', '-10 minutes')").fetchone()[0], client_ip=client_ip())


@app.route("/api/network/clients")
@login_required
@admin_required
def api_network_clients():
    rows = get_db().execute("SELECT * FROM client_connections ORDER BY last_seen DESC").fetchall()
    return jsonify(clients=[dict(row) for row in rows])


@app.route("/api/network/ping", methods=["POST"])
@login_required
@admin_required
def api_network_ping():
    payload = request.get_json(silent=True) or {}
    ip_address = str(payload.get("ip_address", ""))
    if not re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", ip_address) or any(int(part) > 255 for part in ip_address.split(".")):
        return jsonify(error="Invalid IPv4 address"), 400
    command = ["ping", "-n", "1", "-w", "1000", ip_address] if platform.system() == "Windows" else ["ping", "-c", "1", "-W", "1", ip_address]
    result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    return jsonify(ip_address=ip_address, status="ONLINE" if result.returncode == 0 else "OFFLINE", output=result.stdout[-500:])


@app.route("/api/network/logs")
@login_required
@admin_required
def api_network_logs():
    return jsonify(logs=[dict(row) for row in get_db().execute("SELECT * FROM network_logs ORDER BY id DESC LIMIT 100").fetchall()])


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)
