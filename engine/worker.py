"""
Single peer worker: handshake, BITFIELD -> update availability, download pieces (rarest-first / endgame).
PEX: on_extended callback pushes discovered peers to peer_queue.
"""
import asyncio
import struct

from core.peer_connection import PeerConnection
from core.messages import BITFIELD
from core.bencode import decode
from extensions.handshake import build_handshake
from extensions.pex import parse_pex
from .timeouts import with_timeout


async def connect_peer(ip, port, torrent, peer_id, download_path="download.bin", timeout=15):
    """
    Open connection, handshake, return (PeerConnection, None) or (None, error).
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
    except Exception as e:
        return None, e

    handshake = build_handshake(torrent.info_hash, peer_id, use_extensions=True)
    writer.write(handshake)
    await writer.drain()

    try:
        response = await asyncio.wait_for(reader.readexactly(68), timeout=timeout)
    except Exception as e:
        writer.close()
        return None, e

    if response[28:48] != torrent.info_hash:
        writer.close()
        return None, RuntimeError("Info hash mismatch")

    conn = PeerConnection(reader, writer, peer_id=peer_id, torrent=torrent, download_path=download_path)
    return conn, None


def _make_pex_callback(peer_queue):
    def on_extended(ext_id, payload):
        try:
            d = decode(payload)
            if b"added" not in d:
                return
            for ip, port in parse_pex(d):
                try:
                    peer_queue.put_nowait((ip, port))
                except asyncio.QueueFull:
                    pass
        except Exception:
            pass
    return on_extended


async def run_worker(ip, port, torrent, peer_id, piece_manager, download_path="download.bin", peer_queue=None):
    """
    Connect, process BITFIELD for availability, then pull pieces (rarest-first, endgame when applicable).
    If peer_queue is set, PEX messages are parsed and new peers are put on the queue.
    """
    conn, err = await connect_peer(ip, port, torrent, peer_id, download_path)
    if err is not None:
        return

    on_extended = _make_pex_callback(peer_queue) if peer_queue else None

    try:
        # BITFIELD often arrives right after handshake
        try:
            msgs = await with_timeout(conn.recv(), timeout=3)
            if msgs:
                for msg_id, payload in msgs:
                    if msg_id == BITFIELD and payload:
                        piece_manager.update_availability(payload)
        except Exception:
            pass

        while not piece_manager.is_done():
            piece = piece_manager.next_piece()
            if piece is None:
                await asyncio.sleep(0.1)
                continue

            endgame = piece_manager.endgame()
            try:
                await with_timeout(
                    conn.download_piece(piece, endgame_mode=endgame, on_extended=on_extended),
                    timeout=60
                )
            except (TimeoutError, ConnectionError, asyncio.TimeoutError):
                piece_manager.mark_in_progress_free(piece.index)
                break

            if not piece.verify():
                piece_manager.mark_in_progress_free(piece.index)
                continue

            with open(download_path, "r+b") as f:
                f.seek(piece.index * torrent.piece_length)
                f.write(piece.data())
            piece_manager.mark_completed(piece.index)
    finally:
        try:
            conn.writer.close()
            await conn.writer.wait_closed()
        except Exception:
            pass
