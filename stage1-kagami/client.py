import socket
from pathlib import Path
import sys

#初見だと引数が必要だと分からないと思うので、説明文を追加。
if len(sys.argv) < 2:
    print("使い方: python3 client.py sample.mp4")
    sys.exit(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = "127.0.0.1"
server_port = 9000

#サーバー側へTCPセッション開始の接続要求する。サーバー側accept()がこれを受理する仕組み。
#クライアント自身のIPアドレス・ポート番号はOSに自動で決めさせている。bindで設定はしない。
#ただし、接続先のアドレス、ポート番号はクライアント側で指定する。
sock.connect((server_address, server_port))

#サーバーへの接続成功を報告。
#以降はsock.sendall()で()内のデータを接続先(サーバー)へ送信できる。
print("connected")

#CLIコマンドで受け取った動画データ名の引数を代入。
filename = sys.argv[1]
#osコマンドでも同じことは出来るが、見た目が良いのでPathを使用。
#file_pathにinput/sample.mp4 というパスを代入。
file_path = Path("input") / filename
#動画のサイズを代入。stat() ではじめて動画の実ファイルを見にいっている。
file_size = file_path.stat().st_size
#ファイルサイズを数値→文字列→バイト形式に変えて、32バイト丁度のサイズに修正。
#ある種のプレゼンテーション層っぽい役割。
header = str(file_size).encode().ljust(32, b" ")

#サーバー側に上記で調整したデータを送信。
sock.sendall(header)

#rbより、動画をバイナリデータ読込専用で開き、1400バイト読んだのち送信。なくなるまで繰り返す。
with open(file_path, "rb") as file:
    while True:
        #最大1400バイトまで読み込む。
        chunk = file.read(1400)

        if not chunk:
            break

        sock.sendall(chunk)

#サーバー側から返ってきた成否報告を受信。
response = sock.recv(16)
#報告データを文字列へ変換、空白行削除して出力。
print(response.decode().strip())    
#今回のファイル送信セッションを終了する。
sock.close()