import json
import socket
import tempfile
from pathlib import Path

try:
    from .processor import (
        change_aspect_ratio,
        compress_video,
        convert_to_mp3,
        create_gif,
        create_webm,
        resize_video,
    )
    from .protocol import unpack_mmp_header
except ImportError:
    from processor import (
        change_aspect_ratio,
        compress_video,
        convert_to_mp3,
        create_gif,
        create_webm,
        resize_video,
    )
    from protocol import unpack_mmp_header


HOST = "0.0.0.0"
PORT = 9000

HEADER_SIZE = 8
BUFFER_SIZE = 64 * 1024

MAX_JSON_SIZE = (1 << 16) - 1
MAX_MEDIA_TYPE_SIZE = (1 << 8) - 1
MAX_PAYLOAD_SIZE = 4 * 1024 * 1024 * 1024


MEDIA_TYPE_SUFFIXES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
    "audio/mpeg": ".mp3",
    "image/gif": ".gif",
}


OUTPUT_SUFFIXES = {
    "compress_video": ".mp4",
    "resize_video": ".mp4",
    "change_aspect_ratio": ".mp4",
    "convert_to_mp3": ".mp3",
    "create_gif": ".gif",
    "create_webm": ".webm",
}


def recv_exact(conn: socket.socket, size: int) -> bytes:
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


def get_params(request_data: dict) -> dict:
    """
    JSONのparamsを取得する。
    paramsがない場合は空の辞書として扱う。
    """
    params = request_data.get("params", {})

    if not isinstance(params, dict):
        raise ValueError("paramsはJSONオブジェクトにしてください。")

    return params


def require_positive_integer(
    params: dict,
    parameter_name: str,
) -> int:
    """
    0より大きい整数の引数を取得する。
    boolはPythonではintの一種なので明示的に除外する。
    """
    value = params.get(parameter_name)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{parameter_name}は整数で指定してください。"
        )

    if value <= 0:
        raise ValueError(
            f"{parameter_name}は0より大きい値にしてください。"
        )

    return value


def require_non_negative_number(
    params: dict,
    parameter_name: str,
) -> float:
    """
    0以上の数値の引数を取得する。
    """
    value = params.get(parameter_name)

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ValueError(
            f"{parameter_name}は数値で指定してください。"
        )

    if value < 0:
        raise ValueError(
            f"{parameter_name}は0以上にしてください。"
        )

    return float(value)


def require_positive_number(
    params: dict,
    parameter_name: str,
) -> float:
    """
    0より大きい数値の引数を取得する。
    """
    value = params.get(parameter_name)

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ValueError(
            f"{parameter_name}は数値で指定してください。"
        )

    if value <= 0:
        raise ValueError(
            f"{parameter_name}は0より大きい値にしてください。"
        )

    return float(value)


def dispatch_operation(
    request_data: dict,
    input_path: Path,
    work_dir: Path,
) -> Path:
    """
    operationの内容に応じて、
    processor.pyの対応する関数を呼び出す。
    """
    operation = request_data.get("operation")

    if not isinstance(operation, str) or not operation:
        raise ValueError("operationが指定されていません。")

    if operation not in OUTPUT_SUFFIXES:
        raise ValueError(
            f"未対応のoperationです: {operation}"
        )

    params = get_params(request_data)

    output_suffix = OUTPUT_SUFFIXES[operation]
    output_path = work_dir / f"output{output_suffix}"

    if operation == "compress_video":
        result_path = compress_video(
            input_path,
            output_path,
        )

    elif operation == "resize_video":
        width = require_positive_integer(
            params,
            "width",
        )
        height = require_positive_integer(
            params,
            "height",
        )

        result_path = resize_video(
            input_path,
            output_path,
            width,
            height,
        )

    elif operation == "change_aspect_ratio":
        aspect_ratio = params.get("aspect_ratio")

        if aspect_ratio not in {"16:9", "4:3", "1:1"}:
            raise ValueError(
                "aspect_ratioは16:9、4:3、1:1の"
                "いずれかを指定してください。"
            )

        result_path = change_aspect_ratio(
            input_path,
            output_path,
            aspect_ratio,
        )

    elif operation == "convert_to_mp3":
        result_path = convert_to_mp3(
            input_path,
            output_path,
        )

    elif operation == "create_gif":
        start_time = require_non_negative_number(
            params,
            "start_time",
        )
        duration = require_positive_number(
            params,
            "duration",
        )

        result_path = create_gif(
            input_path,
            output_path,
            start_time,
            duration,
        )

    elif operation == "create_webm":
        start_time = require_non_negative_number(
            params,
            "start_time",
        )
        duration = require_positive_number(
            params,
            "duration",
        )

        result_path = create_webm(
            input_path,
            output_path,
            start_time,
            duration,
        )

    else:
        raise ValueError(
            f"未対応のoperationです: {operation}"
        )

    result_path = Path(result_path)

    if not result_path.is_file():
        raise FileNotFoundError(
            "processor.pyの処理後ファイルが見つかりません。"
        )

    return result_path


def handle_client(conn: socket.socket, addr) -> None:
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

        json_bytes = recv_exact(conn, json_size)
        json_text = json_bytes.decode("utf-8")
        request_data = json.loads(json_text)

        if not isinstance(request_data, dict):
            raise ValueError(
                "JSONの一番外側はオブジェクトである必要があります。"
            )

        media_type_bytes = recv_exact(conn, media_type_size)
        media_type = media_type_bytes.decode("utf-8")

        input_suffix = decide_input_suffix(
            request_data,
            media_type,
        )

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

            result_path = dispatch_operation(
                request_data,
                input_path,
                work_dir,
            )

            print(f"[動画処理完了] {result_path}")
            print(
                f"[処理後サイズ] "
                f"{result_path.stat().st_size} bytes"
            )

    except Exception as exc:
        print(f"[エラー] {addr}: {exc}")

    finally:
        conn.close()
        print(f"[切断] {addr}")


def start_server() -> None:
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