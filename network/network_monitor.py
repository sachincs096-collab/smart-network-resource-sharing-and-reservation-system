from database.database import get_db


def connected_clients():
    return get_db().execute("SELECT * FROM client_connections ORDER BY last_seen DESC").fetchall()
