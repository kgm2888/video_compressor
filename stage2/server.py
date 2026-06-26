import json
import socket
from pathlib import Path

from processor import compress_video
from protocol import create_mmp_header, unpack_mmp_header


SERVER_ADDRESS = "0.0.0.0"
SERVER_PORT = 9001
HEADER_SIZE = 8
CHUNK_SIZE = 1400

TEMP_DIR = Path(__file__).resolve().parent / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def recv_exact(connection, size):
    """指定されたサイズを受信し終わるまで繰り返す。"""
    received = bytearray()

    while len(received) < size:
        chunk = connection.recv(size - len(received))

        if not chunk:
            raise ConnectionError("データ受信中に接続が切れました")

        received.extend(chunk)

    return bytes(received)


def receive_file(connection, file_path, file_size):
    """payloadを分割してファイルへ保存する。"""
    remaining_size = file_size

    with file_path.open("wb") as file:
        while remaining_size > 0:
            chunk = connection.recv(min(CHUNK_SIZE, remaining_size))

            if not chunk:
                raise ConnectionError("動画受信中に接続が切れました")

            file.write(chunk)
            remaining_size -= len(chunk)

            print(f"残り受信サイズ: {remaining_size} bytes")


def send_processed_file(connection, operation, output_path):
    """処理後ファイルをMMP形式でクライアントへ返す。"""
    response_data = {
        "status": "success",
        "operation": operation,
        "filename": output_path.name,
    }

    json_bytes = json.dumps(
        response_data,
        ensure_ascii=False,
    ).encode("utf-8")

    media_type_bytes = b"mp4"
    payload_size = output_path.stat().st_size

    header = create_mmp_header(
        len(json_bytes),
        len(media_type_bytes),
        payload_size,
    )

    connection.sendall(header)
    connection.sendall(json_bytes)
    connection.sendall(media_type_bytes)

    with output_path.open("rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            connection.sendall(chunk)

    print("処理後ファイルをクライアントへ送信しました")


def send_error(connection, error_code, description, solution):
    """エラー情報をJSONだけで返す。"""
    error_data = {
        "status": "error",
        "error_code": error_code,
        "description": description,
        "solution": solution,
    }

    json_bytes = json.dumps(
        error_data,
        ensure_ascii=False,
    ).encode("utf-8")

    header = create_mmp_header(
        len(json_bytes),
        0,
        0,
    )

    connection.sendall(header)
    connection.sendall(json_bytes)


def handle_client(connection, client_address):
    """1回のリクエストを受信・処理・返信する。"""
    print("connection from", client_address)

    # MMPヘッダーを受信する
    header = recv_exact(connection, HEADER_SIZE)

    json_size, media_type_size, payload_size = unpack_mmp_header(
        header
    )

    if json_size == 0:
        raise ValueError("JSONが送信されていません")

    if media_type_size == 0:
        raise ValueError("media typeが送信されていません")

    if payload_size == 0:
        raise ValueError("動画ファイルが送信されていません")

    # JSONを受信する
    json_bytes = recv_exact(connection, json_size)
    request_data = json.loads(json_bytes.decode("utf-8"))

    # media typeを受信する
    media_type_bytes = recv_exact(
        connection,
        media_type_size,
    )
    media_type = media_type_bytes.decode("utf-8")

    print("Request:", request_data)
    print("Media type:", media_type)

    # mp4またはvideo/mp4の両方に対応する
    if media_type not in {"mp4", "video/mp4"}:
        raise ValueError(
            f"対応していないmedia typeです: {media_type}"
        )

    input_path = TEMP_DIR / "uploaded_video.mp4"
    output_path = TEMP_DIR / "compressed_video.mp4"

    # 動画を受信して保存する
    receive_file(
        connection,
        input_path,
        payload_size,
    )

    print("動画ファイルの受信が完了しました")

    operation = request_data.get("operation")

    # client側の表記が未確定なので一時的に両方に対応する
    if operation not in {"compress", "compress_video"}:
        raise ValueError(
            f"対応していないoperationです: {operation}"
        )

    # processor.pyの圧縮処理を呼ぶ
    compress_video(
        input_path,
        output_path,
    )

    print("動画の圧縮が完了しました")

    # 圧縮後の動画を返信する
    send_processed_file(
        connection,
        operation,
        output_path,
    )


def start_server():
    """サーバーを起動して接続を待つ。"""
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as server_socket:
        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        server_socket.bind(
            (SERVER_ADDRESS, SERVER_PORT)
        )
        server_socket.listen(1)

        print(
            f"starting up on "
            f"{SERVER_ADDRESS} port {SERVER_PORT}"
        )

        while True:
            connection, client_address = (
                server_socket.accept()
            )

            with connection:
                try:
                    handle_client(
                        connection,
                        client_address,
                    )

                except Exception as error:
                    print("Error:", error)

                    try:
                        send_error(
                            connection,
                            "PROCESSING_ERROR",
                            str(error),
                            "送信内容と動画ファイルを確認してください",
                        )

                    except OSError:
                        print(
                            "クライアントへ"
                            "エラーを返信できませんでした"
                        )

                finally:
                    print("Closing current connection")


if __name__ == "__main__":
    start_server()