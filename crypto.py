from Crypto.Cipher import AES
from hashlib import sha256
from base64 import b64decode


def decrypt(encrypted: str | bytes,
            key: str | bytes = 'zG2nSeEfSHfvTCHy5LCcqtBbQehKNLXn') -> bytes:
    if isinstance(key, str):
        key = key.encode()
    ekey = sha256(key).digest()
    iv = b'\0' * 16
    aes = AES.new(ekey, AES.MODE_CBC, iv)
    data = aes.decrypt(b64decode(encrypted))
    return data[0:len(data) - ord(chr(data[len(data) - 1]))]
