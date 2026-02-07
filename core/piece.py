import hashlib

BLOCK_SIZE = 16384


class Piece:
    def __init__(self, index, size, hash_bytes):
        self.index = index
        self.size = size
        self.hash = hash_bytes
        self.blocks = {}
        self.received = 0

    def next_request(self):
        for offset in range(0, self.size, BLOCK_SIZE):
            if offset not in self.blocks:
                length = min(BLOCK_SIZE, self.size - offset)
                return offset, length
        return None

    def add_block(self, offset, data):
        if offset not in self.blocks:
            self.blocks[offset] = data
            self.received += len(data)

    def complete(self):
        return self.received == self.size

    def verify(self):
        data = b''.join(self.blocks[o] for o in sorted(self.blocks))
        return hashlib.sha1(data).digest() == self.hash

    def data(self):
        return b''.join(self.blocks[o] for o in sorted(self.blocks))
