# Presentation points

1. Problem: shared lab resources collide when coordination is manual.
2. Architecture: browsers are clients; one Flask process is the LAN server.
3. Network layer: private IP addresses identify hosts and ports identify services.
4. Application layer: browser HTTP/REST requests call resource and reservation APIs.
5. Database: SQLite gives a simple centralized source of truth.
6. Concurrency: a lock and immediate transaction reject the second overlapping request.
7. Monitoring: every request records IP, method, endpoint, status, and duration.
8. Direct sockets: port 5050 demonstrates TCP accept, receive, process, and reply.
9. Demo: show server IP, two clients, same reservation attempt, 201 versus 409.
10. Boundary: keep the service on a trusted LAN; do not expose demo credentials publicly.
