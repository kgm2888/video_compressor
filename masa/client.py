import socket
import sys
import os
def protocol_header(data_length):
    return data_length.to_bytes(4, "big")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = input("Type in the server's address to connect to: ")
server_port = 9001
print('connecting to {}'.format(server_address, server_port))
try:
    sock.connect((server_address, server_port))
except socket.error as err:
    print(err)
    sys.exit(1)
try:
    filepath = input('type in a file to upload: ')
    with open(filepath, 'rb') as f:
        f.seek(0, os.SEEK_END)
        filesize = f.tell()
        f.seek(0, 0)
        if filesize > pow(2, 32):
            raise Exception('File must be below 4GB in size')
        header = protocol_header(filesize)
        sock.send(header)
        data = f.read(1400)
        while data:
            sock.send(data)
            data = f.read(1400)
except Exception as err:
    print(err)
    sys.exit(1)
finally:
    print('closing socket')
    sock.close()

