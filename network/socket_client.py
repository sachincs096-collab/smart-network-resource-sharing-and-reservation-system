import socket
import sys
from config import SOCKET_PORT


def send_message(server_ip, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((server_ip, SOCKET_PORT))
        client.sendall(message.encode("utf-8"))
        print("SEND:", message)
        print("RESPONSE:", client.recv(1024).decode("utf-8"))


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    message = sys.argv[2] if len(sys.argv) > 2 else "RESOURCE_STATUS:Printer01"
    send_message(target, message)
