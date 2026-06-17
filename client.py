import socket

HOST = "127.0.0.1"
PORT = 9000


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(b"hello")
        print("Sent: hello")


if __name__ == "__main__":
    main()