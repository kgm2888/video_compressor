import os
import sys
import socket
from protocol import create_mmp_header

def main(number):
    #メニュー表示
    print("動画処理を行うプログラムです。")
    print("1:動画の圧縮")
    print("2:動画の解像度変更")
    print("3:動画のアスペクト比を変更")
    print("4:動画の音声抽出")
    print("5:動画の指定範囲をGIFに変換")
    print("6:動画の指定範囲をWEBMに変換する")
    #ターミナルで処理番号を選択してもらう。
    try:
        FunctionNumber = input("処理番号を入力してください: ")
        if FunctionNumber not in ["1", "2", "3", "4", "5", "6"]:
            raise ValueError("Invalid input")
    except ValueError as err:
        print("1~6の数字を入力してください。")
        sys.exit(1)
    #それぞれの番号に合わせて、jsonファイルを作成
    if FunctionNumber == "1":
        json_string = f'{{"operation": "compress"}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)

    elif FunctionNumber == "2":
        input_width = int(input("動画の幅を入力してください:"))
        input_height = int(input("動画の高さを入力してください:"))
        json_string = f'{{"operation": "resize", "width": {input_width}, "height": {input_height}}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)

    elif FunctionNumber == "3":
        input_aspect_ratio = input("動画のアスペクト比をこの中から16:9,4:3,1:1選んでください:")
        json_string = f'{{"operation": "change_aspect_ratio", "aspect_ratio": "{input_aspect_ratio}"}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)

    elif FunctionNumber == "4":
        json_string = f'{{"operation": "convert_to_mp3"}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)

    elif FunctionNumber == "5":
        input_start_time = int(input("開始時間を入力してください"))
        input_duration = int(input("間隔時間を入力してください"))
        json_string = f'{{"operation": "create_gif","start_time":{input_start_time},"duration":{input_duration}}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)

    elif FunctionNumber == "6":
        input_start_time = int(input("開始時間を入力してください"))
        input_duration = int(input("間隔時間を入力してください"))
        json_string = f'{{"operation": "create_webm","start_time":{input_start_time},"duration":{input_duration}}}'
        json_bytes = json_string.encode("utf-8")
        json_size = len(json_bytes)
    