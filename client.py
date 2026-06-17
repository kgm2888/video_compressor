import os
import socket
import sys

HOST = "127.0.0.1"
PORT = 9000

HEADER_SIZE = 32
BUFFER_SIZE = 1400
RESPONSE_SIZE = 16


def create_file_size_header(file_size: int) -> bytes:
    file_size_text = str(file_size)
    return file_size_text.rjust(HEADER_SIZE).encode("utf-8")


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = b""

    while len(data) < size:
        packet = sock.recv(size - len(data))

        if not packet:
            raise ConnectionError("接続が途中で切断されました。")

        data += packet

    return data


def main():
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
    else:
        file_path = input("送信するmp4ファイルのパスを入力してください: ").strip()

    file_size = os.path.getsize(file_path)
    header = create_file_size_header(file_size)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        client_socket.sendall(header)

        sent_size = 0

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)

                if not chunk:
                    break

                client_socket.sendall(chunk)
                sent_size += len(chunk)

        print(f"送信完了: {sent_size} bytes")

        response = recv_exact(client_socket, RESPONSE_SIZE)
        response_text = response.decode("utf-8").strip("\0")

        print(f"サーバ応答: {response_text}")


if __name__ == "__main__":
    main()