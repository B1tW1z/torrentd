"""
Handle REQUEST messages: read block from disk and send PIECE.
Seed-only mode: run_seeder() starts a TCP server that handshakes and serves REQUESTs.
"""
import asyncio
import struct
import os

from core.torrent import Torrent
from core.peer_connection import PeerConnection
from core.messages import REQUEST, PIECE, build_message
from extensions.handshake import build_handshake


async def handle_request(payload, path, piece_length, send):
    if len(payload) < 12:
        return
    index, begin, length = struct.unpack("!III", payload[:12])
    try:
        with open(path, "rb") as f:
            f.seek(index * piece_length + begin)
            block = f.read(length)
    except (OSError, IOError):
        return
    msg = struct.pack("!II", index, begin) + block
    await send(build_message(PIECE, msg))


async def _handle_seed_client(reader, writer, torrent, download_path, peer_id):
    try:
        their_handshake = await asyncio.wait_for(reader.readexactly(68), timeout=10)
        if their_handshake[28:48] != torrent.info_hash:
            writer.close()
            return
        our_handshake = build_handshake(torrent.info_hash, peer_id, use_extensions=True)
        writer.write(our_handshake)
        await writer.drain()

        conn = PeerConnection(reader, writer, torrent=torrent, download_path=download_path)
        while True:
            msgs = await conn.recv()
            for msg_id, payload in msgs:
                if msg_id == REQUEST:
                    await handle_request(
                        payload,
                        download_path,
                        torrent.piece_length,
                        conn.send,
                    )
    except (ConnectionError, asyncio.TimeoutError, asyncio.IncompleteReadError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run_seeder(torrent_path, download_path, port=6881, peer_id=None):
    """
    Run a TCP server that seeds the given torrent. Each connection: handshake then serve REQUESTs.
    """
    torrent = Torrent(torrent_path)
    peer_id = peer_id or (b"-PC0001-" + os.urandom(12))
    server = await asyncio.start_server(
        lambda r, w: _handle_seed_client(r, w, torrent, download_path, peer_id),
        "0.0.0.0",
        port,
    )
    async with server:
        await server.serve_forever()
