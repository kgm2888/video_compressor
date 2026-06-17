import socket

HOST = "0.0.0.0"
PORT = 9000
BUFFER_SIZE = 1400


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")

            data = conn.recv(BUFFER_SIZE)
            print(f"Received: {data.decode('utf-8')}")

            conn.close()


if __name__ == "__main__":
    start_server()