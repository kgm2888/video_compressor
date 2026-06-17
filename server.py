import os
import socket

HOST = "0.0.0.0"
PORT = 9000

HEADER_SIZE = 32
BUFFER_SIZE = 1400
RESPONSE_SIZE = 16

RECEIVED_DIR = "received"


def recv_exact(conn: socket.socket, size: int) -> bytes:
    data = b""

    while len(data) < size:
        packet = conn.recv(size - len(data))

        if not packet:
            raise ConnectionError("接続が途中で切断されました。")

        data += packet

    return data


def make_response(message: str) -> bytes:
    return message.encode("utf-8")[:RESPONSE_SIZE].ljust(RESPONSE_SIZE, b"\0")


def start_server():
    os.makedirs(RECEIVED_DIR, exist_ok=True)

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

            received_path = os.path.join(RECEIVED_DIR, "received_sample.mp4")

            received_size = 0

            with open(received_path, "wb") as f:
                while received_size < file_size:
                    remaining_size = file_size - received_size
                    read_size = min(BUFFER_SIZE, remaining_size)

                    data = conn.recv(read_size)

                    if not data:
                        break

                    f.write(data)
                    received_size += len(data)

            print(f"受信完了: {received_size} bytes")
            print(f"保存先: {received_path}")

            conn.sendall(make_response("SUCCESS"))

            conn.close()


if __name__ == "__main__":
    start_server()