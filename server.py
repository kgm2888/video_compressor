import socket

HOST = "0.0.0.0"
PORT = 9000

HEADER_SIZE = 32


def recv_exact(conn: socket.socket, size: int) -> bytes:
    data = b""

    while len(data) < size:
        packet = conn.recv(size - len(data))

        if not packet:
            raise ConnectionError("接続が途中で切断されました。")

        data += packet

    return data


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")

            header = recv_exact(conn, HEADER_SIZE)
            file_size = int(header.decode("utf-8").strip())

            print(f"File size: {file_size} bytes")

            conn.close()


if __name__ == "__main__":
    start_server()