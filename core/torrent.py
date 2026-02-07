import hashlib
from .bencode import decode, encode


class Torrent:
    def __init__(self, path=None, *, meta=None, info=None, info_hash=None):
        if path is not None:
            with open(path, "rb") as f:
                self.raw = f.read()
            self.meta = decode(self.raw)
            self.info = self.meta[b"info"]
            self.info_hash = hashlib.sha1(encode(self.info)).digest()
            self.announce = self.meta.get(b"announce", b"").decode() or ""
        else:
            self.raw = None
            self.meta = {}
            self.info = info
            self.info_hash = info_hash
            self.announce = ""

        self.length = self.info[b"length"]
        self.piece_length = self.info[b"piece length"]
        self.pieces = self.info[b"pieces"]

    @classmethod
    def from_metadata(cls, info_dict: dict, info_hash: bytes):
        """Build Torrent from metadata (info dict) for magnet downloads."""
        return cls(info=info_dict, info_hash=info_hash)

    @classmethod
    def from_info_bytes(cls, info_bencoded: bytes):
        """Build Torrent from bencoded info dict (e.g. from ut_metadata)."""
        info = decode(info_bencoded)
        return cls(info=info, info_hash=hashlib.sha1(info_bencoded).digest())

    @property
    def num_pieces(self):
        return len(self.pieces) // 20
