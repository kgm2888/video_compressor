import json
import os
import socket

from processor import compress_video
from protocol import create_mmp_header, unpack_mmp_header

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = "0.0.0.0"
server_port = 9001
dpath = "temp"
if not os.path.exists(dpath):
    os.makedirs(dpath)
print("starting up on {} port {}".format(server_address, server_port))
sock.bind((server_address, server_port))
sock.listen(1)
while True:
    connection, client_address = sock.accept()
    try:
        print("connection from", client_address)
        header = connection.recv(8)
        json_size, media_type_size, payload_size = unpack_mmp_header(header)

        json_bytes = connection.recv(json_size)
        request_data = json.loads(json_bytes.decode("utf-8"))

        media_type_bytes = connection.recv(media_type_size)
        media_type = media_type_bytes.decode("utf-8")

        stream_rate = 1400

        print(
            "Received MMP header. "
            f"JSON: {json_size}, "
            f"Media type: {media_type_size}, "
            f"Payload: {payload_size}"
        )
        print("Request:", request_data)
        print("Media type:", media_type)

        if payload_size == 0:
            raise Exception("No payload to read from client")

        data_length = payload_size
        filename = "uploaded_video.mp4"
        with open(os.path.join(dpath, filename), "wb+") as f:
            while data_length > 0:
                data = connection.recv(data_length if data_length <= stream_rate else stream_rate)
                f.write(data)
                print("recieved {} bytes ".format(len(data)))
                data_length -= len(data)
                print(data_length)
            print("Finished downloading the file from client.")
    except Exception as e:
        print("Error: " + str(e))
    finally:
        print("Closing current connection")
        connection.close()