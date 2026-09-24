from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "network_resources.db"
SECRET_KEY = os.environ.get("SMART_NETWORK_SECRET", "change-this-local-secret")
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
SOCKET_HOST = os.environ.get("SOCKET_HOST", "0.0.0.0")
SOCKET_PORT = int(os.environ.get("SOCKET_PORT", "5050"))
