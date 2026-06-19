# video_compressor

## Stage 1

TCPを使って、クライアントからサーバへmp4ファイルを送信し、サーバ側で保存する。

この段階では、動画の圧縮処理は行わない。
圧縮処理はStage 2で実装する。

## File Structure

```text
video_compressor/
├── client.py
├── server.py
├── input/
├── received/
├── .gitignore
└── README.md
```

## How to run

### 1. 送信用ファイルを用意する

送信するmp4ファイルを `input/` フォルダに入れる。

例：

```text
input/sample.mp4
```

本物のmp4がない場合は、通信確認用の仮ファイルを作成してテストできる。

PowerShellの場合：

```powershell
[System.IO.File]::WriteAllBytes("input\sample.mp4", [byte[]](1..100))
```

### 2. サーバを起動する

1つ目のターミナルで以下を実行する。

```bash
python server.py
```

表示例：

```text
Server listening on 0.0.0.0:9000
```

### 3. クライアントを実行する

2つ目のターミナルで以下を実行する。

```bash
python client.py input/sample.mp4
```

Windows PowerShellの場合は以下でもよい。

```powershell
python client.py input\sample.mp4
```

成功すると、クライアント側に以下のように表示される。

```text
送信ファイル: input\sample.mp4
ファイルサイズ: 100 bytes
送信完了: 100 bytes
サーバ応答: SUCCESS
```

サーバ側には以下のように表示される。

```text
[接続] ...
[受信開始] file size: 100 bytes
[受信完了] saved: received\received_数字_数字.mp4
[切断] ...
```

## Stage 1 Rules

* ファイル名は `server.py` / `client.py` を基本にする
* 送信するmp4は `input/` に置く
* 受信したmp4は `received/` に保存する
* ポート番号は `9000`
* 送受信は `1400` バイトずつ行う
* 最初の `32` バイトでファイルサイズを送る
* 圧縮処理はStage 2から行う

## Notes

* mp4ファイルはGitHubにpushしない
* `input/*.mp4` と `received/*.mp4` は `.gitignore` で除外する
* 受信に成功すると、サーバ側の `received/` フォルダにmp4ファイルが保存される
* 仮の `sample.mp4` は本物の動画ではないため再生はできないが、送受信テストには使える
