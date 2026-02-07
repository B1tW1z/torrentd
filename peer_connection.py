import asyncio
import struct
from message import parse_messages, interested, request, UNCHOKE, PIECE


class PeerConnection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.buffer = b""
        self.choked = True

    async def send(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def recv(self):
        data = await self.reader.read(4096)
        if not data:
            raise ConnectionError
        self.buffer += data
        messages, self.buffer = parse_messages(self.buffer)
        return messages

    async def wait_for_unchoke(self):
        while self.choked:
            for msg_id, _ in await self.recv():
                if msg_id == UNCHOKE:
                    self.choked = False

    async def download_piece(self, piece):
        await self.send(interested())
        await self.wait_for_unchoke()

        while not piece.complete():
            req = piece.next_request()
            if not req:
                break

            offset, length = req
            await self.send(request(piece.index, offset, length))

            for msg_id, payload in await self.recv():
                if msg_id == PIECE:
                    index, begin = struct.unpack("!II", payload[:8])
                    block = payload[8:]
                    if index == piece.index:
                        piece.add_block(begin, block)
