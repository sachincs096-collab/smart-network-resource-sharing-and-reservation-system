import socket
from config import SOCKET_HOST, SOCKET_PORT


def resource_response(message):
    if message.strip().upper() == "RESOURCE_STATUS:PRINTER01":
        return "Printer01: AVAILABLE"
    return "ACK: " + message.strip()


def serve():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((SOCKET_HOST, SOCKET_PORT))
        server.listen(5)
        print(f"TCP socket server listening on {SOCKET_HOST}:{SOCKET_PORT}")
        while True:
            connection, address = server.accept()
            with connection:
                print(f"RECEIVE from {address[0]}: ", end="")
                message = connection.recv(1024).decode("utf-8")
                print(message)
                connection.sendall(resource_response(message).encode("utf-8"))


if __name__ == "__main__":
    serve()
