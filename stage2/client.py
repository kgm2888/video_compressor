import os
import sys
import time
import json
import socket
from pathlib import Path
from protocol import create_mmp_header, unpack_mmp_header

# 1. メニュー表示と操作番号の選択
print("動画処理を行うプログラムです。")
print("1:動画の圧縮")
print("2:動画の解像度変更")
print("3:動画のアスペクト比を変更")
print("4:動画の音声抽出")
print("5:動画の指定範囲をGIFに変換")
print("6:動画の指定範囲をWEBMに変換する")

# ユーザーに入力してもらい、1〜6以外の不正な入力ならエラーにして終了する
try:
    FunctionNumber = input("処理番号を入力してください: ")
    if FunctionNumber not in ["1", "2", "3", "4", "5", "6"]:
        raise ValueError("Invalid input")
except ValueError as err:
    print("1~6の数字を入力してください。")
    sys.exit(1)

# 2. 選択された機能に応じたJSONデータの作成（引数の梱包）
if FunctionNumber == "1":
    json_string = f'{{"operation": "compress"}}'
    json_bytes = json_string.encode("utf-8")  # 通信用にバイナリ（バイト列）に変換
    json_size = len(json_bytes)               # ヘッダー用のJSONサイズを計測

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

# 3. アップロードするローカルファイルの検証
filepath = input('type in a file to upload: ')
if not os.path.exists(filepath):
    print("指定されたファイルが存在しません。")
    sys.exit(1)
if not os.path.isfile(filepath):
    print("指定されたパスはファイルではありません。")
    sys.exit(1)
if not filepath.lower().endswith(".mp4"):
    print("mp4ファイルのみ送信できます。")
    sys.exit(1)

file_size = os.path.getsize(filepath)
if file_size <= 0:
    print("空のファイルは送信できません。")
    sys.exit(1)

print(f"送信ファイル: {filepath}")
print(f"ファイルサイズ: {file_size} bytes")
payload_size = os.path.getsize(filepath)  # ヘッダー用の動画サイズ（ペイロードサイズ）を確定

# 4. サーバーへのソケット接続と各種情報の準備
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCPソケットの作成
server_address = input("サーバーのIPアドレスを入力してください: ")
server_port = 9001

# ファイルパスから拡張子（.mp4）を切り離し、ドット抜きのメディアタイプ（mp4）を作る
root, ext = os.path.splitext(filepath)
media_type = ext[1:]
media_type_size = len(media_type)  # ヘッダー用のメディアタイプサイズを計測

print('connecting to {}'.format(server_address, server_port))

# サーバーに接続要求を出す
try:
    sock.connect((server_address, server_port))
except socket.error as err:
    print(err)
    sys.exit(1)

# 5. 【送信フェーズ】MMPプロトコルに従って一列にデータを送信
# 固定8バイトの共通ヘッダー（送り状）を作成して送信
try:
    header = create_mmp_header(json_size, media_type_size, payload_size)
    sock.send(header)
except socket.error as err:
    print(err)
    sys.exit(1)

# 指示書である JSON データを送信
try:
    sock.send(json_bytes)
except socket.error as err:
    print(err)
    sys.exit(1)

# 動画の形式を表す メディアタイプ文字("mp4") を送信
try:
    sock.send(media_type.encode("utf-8"))
except socket.error as err:
    print(err)
    sys.exit(1)

# 動画ファイルそのものを 4,096バイトずつループで読み込みながら全て送信
try:
    with open(filepath, 'rb') as f:
        data = f.read(4096)
        while data:
            print("Sending...")
            sock.send(data)
            data = f.read(4096)
except socket.error as err:
    print(err)
    sys.exit(1)

# 6. 【確認フェーズ】60秒ごとにサーバーの処理状況（ステータス）を確認
#try:
    # 最初の確認用シグナルを準備（文字列をバイナリに変換）
#ターミナル    Progressconfirmation = "False".encode("utf-8")
#    while True:
#       sock.send(Progressconfirmation)           
#        Progressconfirmation = sock.recv(4096)  
        
        # もし返事が "False"（まだ処理中）なら、60秒待ってからループの先頭に戻る
#       if Progressconfirmation == b"False" or Progressconfirmation == "False":
#          print("サーバー側で処理中です")
#            time.sleep(60)
        #"True"が来たら、ループを脱出して受信フェーズへ進む
#        else:
#           break
#except socket.error as err:
#    print(err)
#    sys.exit(1)

# 7. 【受信フェーズ】変換完了後の動画データをサーバーからダウンロードして保存
dpath = 'output'
if not os.path.exists(dpath):
    os.makedirs(dpath)  # 保存用の 'output' フォルダがなければ自動作成

try:
    # サーバーから返ってくる「ダウンロード用MMPヘッダー（8バイト）」を受信
    header = sock.recv(8)
    # ヘッダーを分解し、これから届く返信用データの各サイズ（定規）を取得
    json_size, media_type_size, payload_size = unpack_mmp_header(header)
    sock.recv(json_size)
    sock.recv(media_type_size)
except socket.error as err:
    print(err)
    sys.exit(1)

# 残った動画データを 4,096バイトずつ安全に受け取り、ファイルに書き込む
try:
    filename = os.path.basename(filepath)
    save_path = os.path.join(dpath, filename)
    with open(save_path, 'wb') as f:  
        while payload_size > 0:  
            data = sock.recv(4096)    
            f.write(data)             
            print('recieved {} bytes'.format(len(data)))
            payload_size -= len(data)
            print(f"Remaining bytes: {payload_size}") 
            
    print('Finished downloading the file from server.')
    print(f'保存先: {save_path}') 

except Exception as e:
    print('Error: ' + str(e))

except Exception as e:
    print('Error: ' + str(e))

# エラーが起きても成功しても、最後は必ずソケットを綺麗に閉じてプログラムを終了する
finally:
    print('closing socket')
    sock.close()