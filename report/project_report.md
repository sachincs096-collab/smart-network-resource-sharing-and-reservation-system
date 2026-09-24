# Smart Network Resource Sharing and Reservation System

## 1. Abstract

This project implements a centralized LAN service for discovering and reserving shared network resources. Multiple browser clients communicate with a Flask server through HTTP over TCP/IP. SQLite stores users, resources, reservations, clients, and request logs. A transaction-backed conflict check ensures that concurrent clients cannot reserve the same resource for overlapping times. A separate raw TCP socket server/client demonstrates reliable stream communication directly.

## 2. Problem statement

Shared lab devices are often coordinated manually, causing collisions, poor visibility, and no evidence of network activity. The system provides one network-accessible inventory and a controlled reservation workflow.

## 3. Objectives

1. Demonstrate client-server and LAN communication.
2. Identify clients and services through IP addresses and ports.
3. Provide resource discovery, reservation, cancellation, and administration.
4. Prevent overlapping bookings under concurrent requests.
5. Monitor clients, request counts, status codes, and latency.
6. Demonstrate direct TCP socket communication.

## 4. Existing and proposed system

The existing manual process uses messages or paper schedules. The proposed system centralizes state on a Flask server and exposes a browser client to every trusted LAN node.

## 5. System architecture

The browser is the client. The Flask process is the network server. HTTP requests travel over TCP/IP to the server port, then the API validates the request and calls SQLite through parameterized queries. The response returns to the browser.

## 6. Computer Network concepts used

| Concept | Use in this system |
|---|---|
| Client-server | Browsers use one central Flask server |
| LAN | Other computers use the server's private IPv4 address |
| IP addressing | Client IPs and resource IPs are displayed and logged |
| Port numbers | 5000 serves HTTP; 5050 serves the TCP demo |
| TCP | Reliable transport for HTTP and raw socket messages |
| REST | JSON endpoints model resources and reservations |
| Concurrent clients | Flask threaded mode handles independent requests |
| Concurrency control | Lock plus SQLite `BEGIN IMMEDIATE` prevents double booking |
| Monitoring | Client table, request duration, status code, and endpoint logs |
| Connectivity | Fixed `ping` invocation checks an admin-selected IPv4 |

## 7. Functional requirements

Authentication, role-based admin access, resource inventory, availability display, reservation conflict validation, cancellation, request logging, client monitoring, connectivity checks, and TCP socket exchange.

## 8. Non-functional requirements

The system is simple to install, responsive on desktop/mobile, parameterized against SQL injection, password-hashed, restricted to trusted LAN use, and explicit about failures.

## 9. Hardware and software requirements

A Windows computer with Python 3.11+, 2 GB RAM, and a private Wi-Fi/LAN connection. Software includes Flask, SQLite, a modern browser, and PowerShell for the socket demonstration.

## 10. Modules

- Authentication: registration, login, password hashes, IP capture.
- Resource discovery: shared device cards with status and endpoint.
- Reservation manager: date/time validation and overlap detection.
- Admin console: inventory, status, users, logs, and network clients.
- Network monitor: server endpoint, client presence, and request records.
- Socket demonstration: TCP accept/receive/process/respond cycle.

## 11. Database design

`users`, `resources`, `reservations`, `network_logs`, and `client_connections` are defined in `database/schema.sql`. Foreign keys connect reservations to users/resources; status fields use constrained values.

## 12. Diagrams

See `report/diagrams.md` for the ER diagram, data flow, sequence, and network architecture diagrams.

## 13. Implementation detail: conflict prevention

The reservation endpoint validates required values and checks overlap using:

```text
existing.start_time < requested.end_time
AND existing.end_time > requested.start_time
```

The application lock serializes local threaded requests, while `BEGIN IMMEDIATE` reserves the SQLite write transaction before the conflict query. If an overlap exists, the transaction rolls back and the server returns HTTP `409 Conflict`.

## 14. Test cases

| ID | Input | Expected result | Status |
|---|---|---|---|
| TC01 | Valid registration | Account created | Pass after run |
| TC02 | Valid login | Session and client IP captured | Pass after run |
| TC03 | Wrong password | HTTP 401 or friendly error | Pass after run |
| TC04 | GET resources | Resources and statuses shown | Pass after run |
| TC05 | Free time slot | HTTP 201 reservation created | Pass after run |
| TC06 | Same occupied slot | HTTP 409 conflict | Pass after run |
| TC07 | Partially overlapping slot | HTTP 409 conflict | Pass after run |
| TC08 | Cancel own reservation | Status becomes CANCELLED | Pass after run |
| TC09 | Admin adds resource | Valid resource enters inventory | Pass after run |
| TC10 | Admin changes/removes resource | Inventory reflects admin action | Pass after run |
| TC11 | Admin ping | ONLINE/OFFLINE result | Pass after run |
| TC12 | Two browser clients | Both appear in monitor | Pass after run |
| TC13 | Socket status message | TCP response returned | Pass after run |
| TC14 | Invalid IP | Request rejected with 400 | Pass after run |
| TC15 | Stopped server | Browser reports unavailable | Pass after run |

## 15. Results, advantages, and limitations

The result is a stable teaching demonstration of networked shared state. Advantages include low dependency count, visible network evidence, and reproducible conflict prevention. It is not intended for public internet deployment, distributed multi-server scaling, production identity management, or real device control.

## 16. Future enhancements

WebSocket status updates, email notifications, a production database, HTTPS, stronger account management, and device-specific health adapters can be added after the core CN demonstration is understood.

## 17. Conclusion

The project shows why computer networks matter: clients on different machines share one reliable, observable service. IPs locate nodes, ports locate services, TCP carries reliable messages, HTTP structures requests, and concurrency control protects shared state.

## 18. Viva questions and answers

**Q: Why use TCP?** A: Reservation requests require reliable, ordered delivery; TCP provides that transport for HTTP and the socket demo.

**Q: How does the server know the client?** A: Flask exposes the peer IP as `request.remote_addr`, which is stored at login and on each request.

**Q: How is double booking prevented?** A: The server serializes reservation transactions, starts an immediate SQLite write transaction, checks time overlap, then commits only one valid insert.

**Q: What is the difference between HTTP and the socket demo?** A: HTTP is the application protocol used by browsers; the socket demo uses Python TCP sockets directly and defines a tiny message format itself.

**Q: Why should the app not be public?** A: It is an educational LAN service with demo credentials and no HTTPS/reverse proxy hardening.
