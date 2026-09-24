# NEXUS: Smart Network Resource Sharing and Reservation System

A beginner-friendly Computer Networks mini project built with Flask, SQLite, browser HTTP, and a direct TCP socket demonstration. It models a LAN resource manager where multiple clients reserve shared printers, lab computers, projectors, and servers through one central node.

## CN focus

This is intentionally more than a reservation CRUD page:

- Flask listens on a real TCP port and can bind to every LAN interface (`0.0.0.0`).
- Each request records its client IP, HTTP method, endpoint, status, and response duration.
- The dashboard exposes the server IP, service port, connected client table, and request path.
- Reservation creation uses an application lock plus `BEGIN IMMEDIATE` SQLite transaction, so simultaneous clients cannot double-book an overlapping slot.
- `network/socket_server.py` and `network/socket_client.py` demonstrate raw TCP request/response independently of HTTP.
- Connectivity checks use a fixed, validated `ping` command and never execute user-supplied shell text.

## Setup on Windows

1. Install Python 3.11 or newer from python.org and ensure **Add Python to PATH** is enabled.
2. Open PowerShell in this folder.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

4. Seed the demo database:

```powershell
py database\seed.py
```

5. Start the LAN server:

```powershell
py app.py
```

Open `http://127.0.0.1:5000` locally. The server prints its network endpoint in the admin dashboard. To find it directly:

```powershell
ipconfig
```

Use the active adapter's IPv4 address, for example `http://192.168.1.10:5000`, from another computer on the same trusted Wi-Fi/LAN.

### Windows Firewall

When Windows asks, allow Python through the firewall on **Private networks only**. If needed, create an inbound rule for TCP port `5000` in Windows Defender Firewall Advanced Security. Do not port-forward this service or expose it to the public internet. The raw socket demo uses TCP port `5050`.

## Demo accounts

- Admin: `admin@example.com` / `admin123`
- User: `student@example.com` / `student123`

Change these credentials before any real deployment.

## TCP socket demonstration

On the server computer, in a second PowerShell window:

```powershell
.\.venv\Scripts\Activate.ps1
py network\socket_server.py
```

From the same machine or another LAN computer:

```powershell
py network\socket_client.py 192.168.1.10 RESOURCE_STATUS:Printer01
```

Expected response: `Printer01: AVAILABLE`. This is a direct TCP socket exchange on port `5050`; the browser workflow remains HTTP on port `5000`.

## Multi-client reservation test

1. Log in from two browsers or two LAN computers.
2. Both clients open **Resources**.
3. Submit the same resource, date, and overlapping time range.
4. One request returns `201` and a success message.
5. The other returns `409` with `Resource is already reserved during this time.`
6. Admin can inspect both client IPs and the HTTP requests in **Request logs**.

## REST API

All protected endpoints use the browser session created by `/api/login`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/register` | Create a user |
| POST | `/api/login` | Start a session and capture client IP |
| POST | `/api/logout` | End the session |
| GET | `/api/resources` | List resources |
| GET/PUT/DELETE | `/api/resources/<id>` | Read or administer a resource |
| GET/POST | `/api/reservations` | List or create reservations |
| GET | `/api/network/status` | Read server and client network status |
| GET | `/api/network/clients` | Admin client connection monitor |
| POST | `/api/network/ping` | Admin connectivity check for a validated IPv4 |
| GET | `/api/network/logs` | Admin HTTP request log |

## Folder structure

```text
app.py                 Flask routes, sessions, REST API, logging
config.py              LAN host, ports, secret, database path
database/              SQLite schema, connection helper, demo seed
network/               TCP socket demo and safe connectivity helper
templates/             Responsive browser views
static/                CSS and reservation form JavaScript
requirements.txt       Minimal runtime dependencies
report/                Report-ready outline and Mermaid diagrams
```

## Project report and viva

See `report/project_report.md` for abstract through conclusion, test cases, diagrams, and viva questions. Mermaid diagrams can be rendered in VS Code, GitHub, or Mermaid Live Editor.
