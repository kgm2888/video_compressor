import json
import socket
import tempfile
from pathlib import Path

try:
    from .protocol import unpack_mmp_header
except ImportError:
    from protocol import unpack_mmp_header


HOST = "0.0.0.0"
PORT = 9000

HEADER_SIZE = 8
BUFFER_SIZE = 64 * 1024

# protocol.pyではJSONサイズを2バイトで表す
MAX_JSON_SIZE = (1 << 16) - 1

# メディアタイプサイズは1バイト
MAX_MEDIA_TYPE_SIZE = (1 << 8) - 1

# 動画サイズは5バイトだが、
# 今回はStage1と同じく最大4GBに制限する
MAX_PAYLOAD_SIZE = 4 * 1024 * 1024 * 1024


MEDIA_TYPE_SUFFIXES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
    "audio/mpeg": ".mp3",
    "image/gif": ".gif",
}


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


def validate_request_sizes(
    json_size: int,
    media_type_size: int,
    payload_size: int,
) -> None:
    """
    共通ヘッダーに書かれていた各サイズが、
    サーバーで受け付けられる範囲か確認する。
    """
    if json_size <= 0:
        raise ValueError("JSONサイズが0以下です。")

    if json_size > MAX_JSON_SIZE:
        raise ValueError("JSONサイズが大きすぎます。")

    if media_type_size <= 0:
        raise ValueError("メディアタイプが指定されていません。")

    if media_type_size > MAX_MEDIA_TYPE_SIZE:
        raise ValueError("メディアタイプが長すぎます。")

    if payload_size <= 0:
        raise ValueError("動画ファイルサイズが0以下です。")

    if payload_size > MAX_PAYLOAD_SIZE:
        raise ValueError("動画ファイルサイズが4GBを超えています。")


def decide_input_suffix(
    request_data: dict,
    media_type: str,
) -> str:
    """
    JSON内のfilename、またはメディアタイプから
    入力ファイルの拡張子を決める。
    """
    filename = request_data.get("filename")

    if isinstance(filename, str):
        suffix = Path(filename).suffix.lower()

        if suffix:
            return suffix

    return MEDIA_TYPE_SUFFIXES.get(media_type, ".bin")


def receive_file(
    conn: socket.socket,
    file_path: Path,
    file_size: int,
) -> None:
    """
    クライアントから送られてくる動画ファイルを
    分割して受信し、file_pathへ保存する。
    """
    received_size = 0

    with file_path.open("wb") as output_file:
        while received_size < file_size:
            remaining_size = file_size - received_size
            read_size = min(BUFFER_SIZE, remaining_size)

            data = conn.recv(read_size)

            if not data:
                raise ConnectionError(
                    "動画受信中にクライアントとの接続が切れました。"
                )

            output_file.write(data)
            received_size += len(data)

    if received_size != file_size:
        raise ValueError(
            "受信した動画サイズがヘッダーの値と一致しません。"
        )


def handle_client(conn: socket.socket, addr) -> None:
    """
    1人のクライアントから、
    JSON・メディアタイプ・動画を受信する。
    """
    print(f"[接続] {addr}")

    try:
        header_bytes = recv_exact(conn, HEADER_SIZE)

        json_size, media_type_size, payload_size = unpack_mmp_header(
            header_bytes
        )

        validate_request_sizes(
            json_size,
            media_type_size,
            payload_size,
        )

        # JSONデータを受信する
        json_bytes = recv_exact(conn, json_size)
        json_text = json_bytes.decode("utf-8")
        request_data = json.loads(json_text)

        if not isinstance(request_data, dict):
            raise ValueError(
                "JSONの一番外側はオブジェクトである必要があります。"
            )

        # メディアタイプを受信する
        media_type_bytes = recv_exact(conn, media_type_size)
        media_type = media_type_bytes.decode("utf-8")

        input_suffix = decide_input_suffix(
            request_data,
            media_type,
        )

        # 一時フォルダは処理終了後に自動削除される
        with tempfile.TemporaryDirectory(
            prefix="video_compressor_"
        ) as temporary_directory:

            work_dir = Path(temporary_directory)
            input_path = work_dir / f"input{input_suffix}"

            receive_file(
                conn,
                input_path,
                payload_size,
            )

            print(f"[JSON受信] {request_data}")
            print(f"[メディアタイプ] {media_type}")
            print(f"[動画受信完了] {input_path}")
            print(f"[動画サイズ] {input_path.stat().st_size} bytes")

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