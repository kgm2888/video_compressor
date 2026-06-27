import struct

#引数で受け取った各データのサイズ（整数）を、ネットワーク送信用の共通ヘッダーに梱包する関数。
def create_mmp_header(json_size, media_type_size, payload_size):
    return json_size.to_bytes(2, 'big') + media_type_size.to_bytes(1, 'big') + payload_size.to_bytes(5, 'big')

#引数で受け取った共通ヘッダーのバイト列を、各データのサイズ（整数）に分解する関数。
def unpack_mmp_header(header_bytes):
    json_size = int.from_bytes(header_bytes[0:2], 'big')
    media_type_size = int.from_bytes(header_bytes[2:3], 'big')
    payload_size = int.from_bytes(header_bytes[3:8], 'big')
    return json_size, media_type_size, payload_size 