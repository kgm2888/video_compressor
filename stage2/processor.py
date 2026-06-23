import subprocess
from pathlib import Path

#FFmpeg専用の例外クラスを定義する。
class FFmpegProcessError(Exception):
    pass

# ffmpegコマンドを実行する共通処理
def run_ffmpeg(command):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        raise FFmpegProcessError(
            "ffmpeg がインストールされていません"
        )

    if result.returncode != 0:
        raise FFmpegProcessError(
            f"ffmpeg処理に失敗しました: {result.stderr}"
        )

#入力先のパスと、出力先のパスをパスオブジェクトへ変換。
def prepare_paths(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"入力ファイルが存在しません: {input_path}"
        )
    #output_pathまでに必要なフォルダを作成する。
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return input_path, output_path

# 共通の出力ファイル確認
def check_output_file(output_path):
    if not output_path.exists():
        raise FFmpegProcessError(
            f"出力ファイルが作成されませんでした: {output_path}"
        )


#動画の圧縮
def compress_video(input_path, output_path):
    input_path, output_path = prepare_paths(input_path, output_path)

    command = [
        #FFmpegを起動。上書き可否にyesを返す。
        "ffmpeg", "-y",
        #input→str型に直した(input_path)
        "-i", str(input_path),
        #映像をどの方式(コーデック)で保存するか。今回はH.264形式。
        "-vcodec", "libx264",
        #圧縮率の調整。今回の28はそこそこ画質くらい。
        "-crf", "28",
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path

#動画の解像度変更
def resize_video(input_path, output_path, width, height):
    input_path, output_path = prepare_paths(input_path, output_path)

    command = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        #動画に加工を加える→解像度変更
        "-vf", f"scale={width}:{height}",
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path

#動画のアスペクト比を変更する
def change_aspect_ratio(input_path, output_path, aspect_ratio):
    input_path, output_path = prepare_paths(input_path, output_path)

    if aspect_ratio == "16:9":
        crop_filter = "crop=ih*16/9:ih"
    elif aspect_ratio == "4:3":
        crop_filter = "crop=ih*4/3:ih"
    elif aspect_ratio == "1:1":
        crop_filter = "crop=min(iw\\,ih):min(iw\\,ih)"
    else:
        raise ValueError(
            f"未対応のアスペクト比です: {aspect_ratio}"
        )

    command = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        #動画に加工を加える→アスペクト比変更
        "-vf", crop_filter,
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path


#動画から音声だけを抽出してMP3に変換する
def convert_to_mp3(input_path, output_path):
    input_path, output_path = prepare_paths(input_path, output_path)

    command = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        #映像を捨てる
        "-vn",
        #音声の保存形式→MP3形式へ変換
        "-acodec", "libmp3lame",
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path


#指定範囲をGIFに変換する
def create_gif(input_path, output_path, start_time, duration):
    input_path, output_path = prepare_paths(input_path, output_path)

    command = [
        "ffmpeg", "-y",
        #開始時間
        "-ss", str(start_time),
        #切り抜く時間
        "-t", str(duration),
        "-i", str(input_path),
        #動画変更→fps=10,scale=480:-1.-1は自動比率
        "-vf", "fps=10,scale=480:-1",
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path


#指定範囲をWEBMに変換する
def create_webm(input_path, output_path, start_time, duration):
    input_path, output_path = prepare_paths(input_path, output_path)

    command = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(input_path),
        #映像のコーデック指定。映像をVP9形式で保存。
        "-c:v", "libvpx-vp9",
        #映像のビットレート。1Mbps。
        "-b:v", "1M",
        #音声を捨てる。
        "-an",
        str(output_path)
    ]

    run_ffmpeg(command)
    check_output_file(output_path)

    return output_path

#問題なく動くか、各務側で確認するようのコード。本来は不要。
#if __name__ == "__main__":
    #compress_video(
    #"input/sample.mp4",
    #"output/compressed_sample.mp4"
#)
