"""
Minimal DHT node: bootstrap and listen for get_peers/find_node responses.
Enough to resolve peers from magnet links when combined with tracker flow.
"""
import asyncio
import os
import socket

from core.bencode import decode
from .krpc import make_query, decode_krpc

BOOTSTRAP_NODES = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
]


class DHTNode:
    def __init__(self, node_id=None, port=6881):
        self.node_id = node_id or os.urandom(20)
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(("", port))
        self._peers = []
        self._running = False

    async def bootstrap(self):
        """Send find_node to bootstrap nodes to join the DHT."""
        loop = asyncio.get_running_loop()
        for host, port in BOOTSTRAP_NODES:
            try:
                msg = make_query(b"find_node", {b"target": self.node_id}, self.node_id)
                await loop.sock_sendto(self.sock, msg, (host, port))
            except Exception:
                pass

    async def get_peers(self, info_hash: bytes, timeout=5.0):
        """
        Ask bootstrap nodes for peers for info_hash. Returns list of (ip, port).
        Minimal implementation: no full routing table; just fire get_peers at bootstrap nodes.
        """
        loop = asyncio.get_running_loop()
        msg = make_query(b"get_peers", {b"info_hash": info_hash}, self.node_id)
        self._peers = []
        for host, port in BOOTSTRAP_NODES:
            try:
                await loop.sock_sendto(self.sock, msg, (host, port))
            except Exception:
                pass

        deadline = loop.time() + timeout
        while loop.time() < deadline and len(self._peers) < 50:
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self.sock, 4096),
                    timeout=min(1.0, deadline - loop.time())
                )
            except asyncio.TimeoutError:
                continue
            try:
                m = decode_krpc(data)
                if m.get(b"y") == b"r" and b"r" in m:
                    r = m[b"r"]
                    if b"values" in r:
                        for v in r[b"values"]:
                            if isinstance(v, bytes) and len(v) >= 6:
                                ip = ".".join(map(str, v[:4]))
                                port = int.from_bytes(v[4:6], "big")
                                self._peers.append((ip, port))
            except Exception:
                pass
        return list(dict.fromkeys(self._peers))

    async def listen(self, callback=None):
        """Run receive loop; callback(msg, addr) if provided."""
        loop = asyncio.get_running_loop()
        self._running = True
        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(self.sock, 4096)
                msg = decode_krpc(data)
                if callback:
                    callback(msg, addr)
            except Exception:
                pass

    def close(self):
        self._running = False
        try:
            self.sock.close()
        except Exception:
            pass
