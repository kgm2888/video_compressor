# Video Compressor

TCP通信を使って、クライアントからサーバーへ動画を送信し、FFmpegで処理したファイルをクライアントへ返すプログラムです。

## 主な機能

クライアントから次の処理を選択できます。

1. 動画の圧縮
2. 動画の解像度変更
3. 動画のアスペクト比変更
4. 動画から音声を抽出
5. 動画の指定範囲をGIFへ変換
6. 動画の指定範囲をWebMへ変換

## 使用技術

- Python
- TCPソケット通信
- JSON
- FFmpeg
- Git / GitHub

## ファイル構成

```text
video_compressor/
├── stage2/
│   ├── client.py
│   ├── server.py
│   ├── processor.py
│   ├── protocol.py
│   └── temp/
├── input/
├── received/
├── .gitignore
└── README.md
```

## 事前準備

### Python

Pythonをインストールしてください。

### FFmpeg

動画処理にFFmpegを使用します。

Windowsでは、PowerShellから次のコマンドでインストールできます。

```powershell
winget install --id Gyan.FFmpeg --exact --source winget
```

インストール後、新しいPowerShellを開き、次のコマンドで確認します。

```powershell
ffmpeg -version
```

## 実行方法

### 1. 動画を用意する

処理するmp4ファイルを `input/` フォルダへ入れます。

例：

```text
input/test_video.mp4
```

### 2. サーバーを起動する

1つ目のPowerShellで、リポジトリのルートから次を実行します。

```powershell
python stage2/server.py
```

正常に起動すると、次のように表示されます。

```text
starting up on 0.0.0.0 port 9001
```

### 3. クライアントを起動する

2つ目のPowerShellで次を実行します。

```powershell
python stage2/client.py
```

表示される案内に従って、次の内容を入力します。

- 実行する処理番号
- 処理する動画のパス
- サーバーのIPアドレス

同じパソコンで動作確認する場合、サーバーのIPアドレスには次を入力します。

```text
127.0.0.1
```

処理されたファイルは `output/` フォルダへ保存されます。

## 通信の流れ

1. クライアントが処理内容をJSONで作成する
2. MMPヘッダー、JSON、メディアタイプ、動画データをサーバーへ送信する
3. サーバーが動画を一時ファイルとして保存する
4. `processor.py`からFFmpegを実行する
5. 処理済みファイルをクライアントへ返す
6. クライアントが受信したファイルを保存する
7. サーバーが一時ファイルを削除する

## MMPヘッダー

通信では、最初に8バイトの共通ヘッダーを送信します。

```text
JSONサイズ：2バイト
メディアタイプサイズ：1バイト
動画データサイズ：5バイト
```

## 動作確認

動画圧縮について、次の処理が正常に完了することを確認しました。

- クライアントから動画を送信
- サーバーで動画を受信
- FFmpegで動画を圧縮
- 処理済み動画をクライアントへ送信
- クライアントで受信して保存
- サーバー側の一時ファイルを削除

確認結果：

```text
入力ファイル：46587 bytes
出力ファイル：43408 bytes
再生時間：3.018秒
```

## 注意事項

- 送信するファイルはmp4形式を使用してください
- サーバーとクライアントはポート番号 `9001` を使用します
- 動画ファイルや処理結果はGitHubへpushしません
- サーバーを先に起動してからクライアントを実行してください
