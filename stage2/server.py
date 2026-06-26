import socket

try:
    from .protocol import unpack_mmp_header
except ImportError:
    from protocol import unpack_mmp_header


HOST = "0.0.0.0"
PORT = 9000

# protocol.pyで作成される共通ヘッダーのサイズ
# JSONサイズ2バイト + メディアタイプサイズ1バイト + 動画サイズ5バイト
HEADER_SIZE = 8


def recv_exact(conn: socket.socket, size: int) -> bytes:
    """
    指定されたsizeバイトを受信し終わるまで、
    conn.recv()を繰り返す。
    """
    data = b""

    while len(data) < size:
        packet = conn.recv(size - len(data))

        if not packet:
            raise ConnectionError(
                "データ受信中にクライアントとの接続が切れました。"
            )

        data += packet

    return data


def handle_client(conn: socket.socket, addr) -> None:
    """
    1人のクライアントとの通信を処理する。
    """
    print(f"[接続] {addr}")

    try:
        # 最初に8バイトの共通ヘッダーを受信する
        header_bytes = recv_exact(conn, HEADER_SIZE)

        # ヘッダーから各データのサイズを取り出す
        json_size, media_type_size, payload_size = unpack_mmp_header(
            header_bytes
        )

        print(f"[JSONサイズ] {json_size} bytes")
        print(f"[メディアタイプサイズ] {media_type_size} bytes")
        print(f"[動画サイズ] {payload_size} bytes")

    except Exception as exc:
        print(f"[エラー] {addr}: {exc}")

    finally:
        conn.close()
        print(f"[切断] {addr}")


def start_server() -> None:
    """
    TCPサーバーを起動し、クライアントからの接続を待つ。
    """
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as server_socket:

        # サーバーを終了してすぐ再起動した場合にも
        # 同じポートを再利用しやすくする
        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            handle_client(conn, addr)


if __name__ == "__main__":
    start_server()