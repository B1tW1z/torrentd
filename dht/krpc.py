"""
KRPC: bencoded UDP messages for DHT (BEP 5).
"""
import os
from core.bencode import encode, decode


def make_query(q: bytes, a: dict, node_id: bytes) -> bytes:
    """Build a query message: y=q, q=method, a=args (id added automatically)."""
    return encode({
        b"t": os.urandom(2),
        b"y": b"q",
        b"q": q,
        b"a": {**a, b"id": node_id}
    })


def make_response(tid: bytes, r: dict) -> bytes:
    """Build a response message: y=r, r=dict."""
    return encode({
        b"t": tid,
        b"y": b"r",
        b"r": r
    })


def decode_krpc(data: bytes) -> dict:
    """Decode one KRPC message. Returns dict with y, t, and q/r/a as applicable."""
    return decode(data)
