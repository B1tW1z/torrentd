"""
Minimal DHT routing: store nodes and find closest to a target.
Full Kademlia would use k-buckets; here we keep a simple list for bootstrap/peer discovery.
"""
import hashlib


def distance(a: bytes, b: bytes) -> bytes:
    """XOR distance between two 20-byte node IDs."""
    return bytes(x ^ y for x, y in zip(a, b))


def id_for_peer(ip: str, port: int) -> bytes:
    """Stable node ID from address (for routing table)."""
    return hashlib.sha1(f"{ip}:{port}".encode()).digest()
