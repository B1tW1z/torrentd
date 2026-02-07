"""
Peer wire protocol: handshake, message loop, download blocks, respond to REQUEST (seeding).
"""
import asyncio
import struct
from .messages import (
    parse_messages,
    interested,
    request,
    UNCHOKE,
    PIECE,
    REQUEST,
    EXTENDED,
    build_message,
)


class PeerConnection:
    def __init__(self, reader, writer, peer_id=None, torrent=None, download_path=None):
        self.reader = reader
        self.writer = writer
        self.peer_id = peer_id
        self.torrent = torrent
        self.download_path = download_path or "download.bin"
        self.buffer = b""
        self.choked = True
        self._pending_requests = set()  # (index, begin) for endgame duplicate requests

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

    async def wait_for_unchoke(self, timeout=30):
        try:
            while self.choked:
                for msg_id, _ in await asyncio.wait_for(self.recv(), timeout=timeout):
                    if msg_id == UNCHOKE:
                        self.choked = False
                        return
        except asyncio.TimeoutError:
            raise TimeoutError("Peer did not unchoke")

    async def _handle_request(self, payload, piece_length):
        """Serve a REQUEST (upload / seeding)."""
        if len(payload) < 12:
            return
        index, begin, length = struct.unpack("!III", payload[:12])
        try:
            with open(self.download_path, "rb") as f:
                f.seek(index * piece_length + begin)
                block = f.read(length)
        except (OSError, IOError):
            return
        msg = struct.pack("!II", index, begin) + block
        await self.send(build_message(PIECE, msg))

    async def recv_messages(self, on_piece=None, on_request=None, piece_length=None):
        """
        Process incoming messages. If torrent is set and we have download_path, handle REQUEST (seeding).
        on_piece: optional callback (index, begin, block_data) for PIECE messages.
        on_request: optional async callback(payload) for REQUEST; if None and we have torrent, we serve from file.
        """
        for msg_id, payload in await self.recv():
            if msg_id == UNCHOKE:
                self.choked = False
            elif msg_id == REQUEST:
                if on_request:
                    await on_request(payload)
                elif self.torrent and piece_length is not None:
                    await self._handle_request(payload, piece_length)
            elif msg_id == PIECE and on_piece and len(payload) >= 8:
                index, begin = struct.unpack("!II", payload[:8])
                block = payload[8:]
                on_piece(index, begin, block)

    async def download_piece(self, piece, endgame_mode=False, on_extended=None):
        await self.send(interested())
        await self.wait_for_unchoke()

        while not piece.complete():
            req = piece.next_request()
            if not req:
                break
            offset, length = req
            await self.send(request(piece.index, offset, length))

            while True:
                got = False
                for msg_id, payload in await self.recv():
                    if msg_id == EXTENDED and len(payload) >= 1 and on_extended:
                        on_extended(payload[0], payload[1:])
                    if msg_id == PIECE and len(payload) >= 8:
                        idx, begin = struct.unpack("!II", payload[:8])
                        block = payload[8:]
                        if idx == piece.index:
                            piece.add_block(begin, block)
                            got = True
                            break
                if got or not endgame_mode:
                    break
                if piece.complete():
                    break
