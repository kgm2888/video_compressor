import socket
import os
from pathlib import Path

#socket.AF_INETでIPv4を使うことを宣言、socket.SOCK_STREAMがTCP。
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#全部のIPアドレスで待ち受ける。
server_address = '0.0.0.0'
server_port = 9000

#receivedというフォルダがなければ作成。
dpath = 'received'
#os.pathでosの機能。Pathとは別。実際にフォルダの存在を問い合わせている。
if not os.path.exists(dpath):
    os.makedirs(dpath)

#開始を宣言。
print(f"Starting up on {server_address} port {server_port}")
# server_address = '0.0.0.0'にbindすることで、どのIPアドレスでも受け取れる電話機を宣言。
sock.bind((server_address, server_port))
# 着信可能状態にする。
sock.listen(1)

while True:
    #クライアントからの接続要求をまつ。
    # 要求がきたら、sock.accept()によりconnection にクライアントとの専用通信路(socketオブジェクト)、
    # client_address にクライアントのIPアドレス, ポート番号が代入される。
    # accept() はクライアント側の sock.connect() とペア。
    connection, client_address = sock.accept()

    #接続に成功したら、クライアントのアドレス,ポート番号を返す。
    print('connection from', client_address)
    #クライアント側から、最初にデータサイズを受け取る。
    header = connection.recv(32)
    print(len(header))
    #decode()でバイト型→文字列型にし、追加した空白をstrip()で消している。
    #ある種のプレゼンテーション層みたいな役割。
    file_size = int(header.decode().strip())
    print("file size:",file_size)

    #受信済みサイズを0にする。
    received_size = 0
    #保存先のファイルパスを指定する。
    output_path = Path("received/sample.mp4")

    #received/sample.mp4 を書き込みモードで開く。
    #sample.mp4が無ければ空のsample.mp4を作成する。
    #fileは変数名。
    with open(output_path, "wb") as file:
        while received_size < file_size:

            #クライアント側から送られてきたデータをchunkへ代入。
            #1400バイトずつ受け取り都度書き込む。
            chunk = connection.recv(1400)
            
            #ファイル分受け取ったら終了
            if not chunk:
                print("no chunk")
                break

            file.write(chunk)

            #後で元データと比較するため、総保存データを残す。
            received_size += len(chunk)
    #受け取ったデータサイズと、最初に通知されたファイルサイズが同じなら、成功を報告。
    #同じでないなら失敗を報告する。
    if received_size == file_size:
        print("receive completed")
        #クライアント側へ、成功の報告をバイナリ16バイトで行う。
        connection.sendall(b"UPLOAD_SUCCESS".ljust(16, b" "))
    else:
        print("receive failed")
        
        connection.sendall(b"UPLOAD_FAILED".ljust(16, b" "))
    # このクライアントとの1回分の通信セッションを終了する。    
    connection.close()
