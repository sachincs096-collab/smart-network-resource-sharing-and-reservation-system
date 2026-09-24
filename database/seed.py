from werkzeug.security import generate_password_hash
from database.database import init_db, get_db
from config import DATABASE_PATH
import sqlite3


def seed():
    init_db()
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password_hash, role, ip_address) VALUES (?, ?, ?, ?, ?)",
        ("Network Admin", "admin@example.com", generate_password_hash("admin123"), "admin", "127.0.0.1"),
    )
    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password_hash, role, ip_address) VALUES (?, ?, ?, ?, ?)",
        ("Demo Student", "student@example.com", generate_password_hash("student123"), "user", "127.0.0.1"),
    )
    resources = [
        ("Printer-01", "Network Printer", "CN Lab", "192.168.1.20", 9100, "AVAILABLE", "Shared laser printer; sample private LAN address."),
        ("Projector-01", "Projector", "Seminar Hall", "192.168.1.21", 8080, "AVAILABLE", "Presentation projector; sample private LAN address."),
        ("Lab-PC-01", "Computer", "CN Lab", "192.168.1.31", 5001, "AVAILABLE", "Lab workstation; sample private LAN address."),
        ("Lab-PC-02", "Computer", "CN Lab", "192.168.1.32", 5002, "AVAILABLE", "Lab workstation; sample private LAN address."),
        ("File-Server", "Server", "Server Room", "192.168.1.40", 445, "AVAILABLE", "Network storage; sample private LAN address."),
    ]
    db.executemany(
        "INSERT OR IGNORE INTO resources (name, type, location, ip_address, port, status, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
        resources,
    )
    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
    print("Database initialized and seeded.")
