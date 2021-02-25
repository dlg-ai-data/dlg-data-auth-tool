import base64
from Cryptodome import Random
from Cryptodome.Cipher import AES
from vaiv import settings


class AESCipher:
    def __init__(self):
        self.bs = AES.block_size
        self.pad = lambda s: s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
        self.unpad = lambda s: s[0:-s[-1]]
        self.key = settings.ENCRYPT_KEY.encode('utf-8')

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = self.key
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = self.key
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc)).decode('utf-8')

    def encrypt_str(self, raw):
        return self.encrypt(raw).decode('utf-8')

    def decrypt_str(self, enc):
        if type(enc) == str:
            enc = str.encode(enc)
        return self.decrypt(enc).decode('utf-8')

