import hashlib
from bencode import decode, encode

class Torrent:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.raw = f.read()

        self.meta = decode(self.raw)
        self.info = self.meta[b'info']
        self.info_hash = hashlib.sha1(encode(self.info)).digest()

        self.announce = self.meta[b'announce'].decode()
        self.length = self.info[b'length']
        self.piece_length = self.info[b'piece length']
        self.pieces = self.info[b'pieces']
