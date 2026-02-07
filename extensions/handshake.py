"""
Extension protocol (BEP 10): reserved bits and extended handshake.
"""
import struct

# Reserved byte index 5, bit 0x10 = extension protocol
def reserved_with_extensions():
    reserved = bytearray(8)
    reserved[5] |= 0x10
    return bytes(reserved)

def build_handshake(info_hash, peer_id, use_extensions=True):
    pstr = b"BitTorrent protocol"
    reserved = reserved_with_extensions() if use_extensions else b"\x00" * 8
    return (
        struct.pack("!B", len(pstr))
        + pstr
        + reserved
        + info_hash
        + peer_id
    )
