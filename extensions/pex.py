"""
Peer Exchange (PEX, BEP 11): parse PEX payloads from extension messages.
"""
import struct

PEX_ID = 1


def parse_pex(payload: dict) -> list:
    """
    payload is the decoded extended message payload (dict).
    Returns list of (ip, port) from 'added' (and optionally 'added.f' for flags).
    """
    added = payload.get(b"added", b"")
    peers = []
    for i in range(0, len(added), 6):
        if i + 6 > len(added):
            break
        ip = ".".join(map(str, added[i:i+4]))
        port = struct.unpack("!H", added[i+4:i+6])[0]
        peers.append((ip, port))
    return peers
