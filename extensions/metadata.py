"""
Metadata (BEP 9): fetch metadata via ut_metadata for magnet links.
"""
import asyncio
from core.bencode import encode, decode, decode_one
from core.messages import EXTENDED, build_message

METADATA_SIZE_KEY = b"metadata_size"
UT_METADATA = b"ut_metadata"
METADATA_PIECE_SIZE = 16384


def _build_extended(ext_id: int, payload: bytes) -> bytes:
    return build_message(EXTENDED, bytes([ext_id]) + payload)


async def fetch_metadata(conn, timeout=15):
    """
    Send extended handshake, get metadata_size and ut_metadata id, request all pieces, return bencoded info.
    conn must have .send() and .recv() (returns list of (msg_id, payload)).
    """
    handshake_req = encode({b"m": {b"ut_metadata": 1}})
    await conn.send(_build_extended(0, handshake_req))

    metadata_size = None
    ut_metadata_id = None
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        msgs = await conn.recv()
        for msg_id, payload in msgs:
            if msg_id != 20 or len(payload) < 2:
                continue
            ext_id = payload[0]
            sub = payload[1:]
            if ext_id == 0:
                try:
                    d = decode(sub)
                except Exception:
                    continue
                metadata_size = d.get(METADATA_SIZE_KEY)
                if d.get(b"m") and UT_METADATA in d[b"m"]:
                    ut_metadata_id = d[b"m"][UT_METADATA]
                if metadata_size is not None and ut_metadata_id is not None:
                    break
        if metadata_size is not None and ut_metadata_id is not None:
            break
        await asyncio.sleep(0.05)

    if metadata_size is None or ut_metadata_id is None:
        raise RuntimeError("Could not get metadata size / ut_metadata id")

    n_pieces = (metadata_size + METADATA_PIECE_SIZE - 1) // METADATA_PIECE_SIZE
    pieces = [None] * n_pieces
    received = 0

    for i in range(n_pieces):
        req = encode({b"msg_type": 0, b"piece": i})
        await conn.send(_build_extended(ut_metadata_id, req))

    while received < n_pieces and loop.time() < deadline:
        msgs = await conn.recv()
        for msg_id, payload in msgs:
            if msg_id != 20 or len(payload) < 2 or payload[0] != ut_metadata_id:
                continue
            sub = payload[1:]
            try:
                d, end = decode_one(sub, 0)
            except Exception:
                continue
            if d.get(b"msg_type") != 1:
                continue
            idx = d.get(b"piece")
            if idx is not None and idx in range(n_pieces) and pieces[idx] is None:
                piece_data = sub[end:]
                if idx is not None:
                    pieces[idx] = piece_data
                    received += 1
        await asyncio.sleep(0.02)

    if received != n_pieces:
        raise RuntimeError("Incomplete metadata")
    return b"".join(pieces)
