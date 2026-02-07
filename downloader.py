import asyncio
import struct
from peer_connection import PeerConnection
from piece import Piece
from message import BITFIELD


async def download_single_piece(ip, port, torrent, peer_id, piece_index):
    reader, writer = await asyncio.open_connection(ip, port)

    # ---- Handshake ----
    pstr = b"BitTorrent protocol"
    handshake = (
        struct.pack("!B", len(pstr)) +
        pstr +
        b"\x00" * 8 +
        torrent.info_hash +
        peer_id
    )

    writer.write(handshake)
    await writer.drain()
    await reader.readexactly(68)

    conn = PeerConnection(reader, writer)

    piece_hash = torrent.pieces[piece_index * 20:(piece_index + 1) * 20]

    piece_size = torrent.piece_length
    if piece_index == len(torrent.pieces) // 20 - 1:
        piece_size = torrent.length % torrent.piece_length

    piece = Piece(piece_index, piece_size, piece_hash)

    await conn.download_piece(piece)

    if not piece.verify():
        raise RuntimeError("Piece hash mismatch")

    with open("download.bin", "r+b") as f:
        f.seek(piece_index * torrent.piece_length)
        f.write(piece.data())

    writer.close()
