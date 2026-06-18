import os
import socket
import time

HOST = "0.0.0.0"
PORT = 9000

HEADER_SIZE = 32
BUFFER_SIZE = 1400
RESPONSE_SIZE = 16

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DIR = os.path.join(BASE_DIR, "received")
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB


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


def handle_client(conn: socket.socket, addr):
    print(f"[接続] {addr}")

    os.makedirs(RECEIVED_DIR, exist_ok=True)

    tmp_path = None

    try:
        header = recv_exact(conn, HEADER_SIZE)
        file_size_text = header.decode("utf-8").strip()

        if not file_size_text.isdigit():
            raise ValueError("ファイルサイズの形式が不正です。")

        file_size = int(file_size_text)

        if file_size <= 0:
            raise ValueError("ファイルサイズが0以下です。")

        if file_size > MAX_FILE_SIZE:
            raise ValueError("ファイルサイズが4GBを超えています。")

        print(f"[受信開始] file size: {file_size} bytes")

        timestamp = int(time.time())
        filename = f"received_{timestamp}_{addr[1]}.mp4"

        final_path = os.path.join(RECEIVED_DIR, filename)
        tmp_path = final_path + ".tmp"

        received_size = 0

        with open(tmp_path, "wb") as f:
            while received_size < file_size:
                remaining_size = file_size - received_size
                read_size = min(BUFFER_SIZE, remaining_size)

                data = conn.recv(read_size)

                if not data:
                    raise ConnectionError("ファイル受信中に接続が切断されました。")

                f.write(data)
                received_size += len(data)

        if received_size != file_size:
            raise ValueError("受信したファイルサイズが一致しません。")

        os.rename(tmp_path, final_path)

        print(f"[受信完了] saved: {final_path}")
        conn.sendall(make_response("SUCCESS"))

    except Exception as e:
        print(f"[エラー] {addr}: {e}")

        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

        try:
            conn.sendall(make_response("ERROR"))
        except Exception:
            pass

    finally:
        conn.close()
        print(f"[切断] {addr}")


def start_server():
    os.makedirs(RECEIVED_DIR, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            handle_client(conn, addr)


if __name__ == "__main__":
    start_server()