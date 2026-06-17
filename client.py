import os
import socket
import sys

HOST = "127.0.0.1"
PORT = 9000

HEADER_SIZE = 32


def create_file_size_header(file_size: int) -> bytes:
    file_size_text = str(file_size)
    return file_size_text.rjust(HEADER_SIZE).encode("utf-8")


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

    print(f"Sent file size: {file_size} bytes")


if __name__ == "__main__":
    main()