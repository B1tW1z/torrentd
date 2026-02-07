import asyncio
import os
import struct
import socket
from urllib.parse import urlparse


class UDPTracker:
    def __init__(self, announce_url, info_hash, peer_id, port=6881):
        self.url = urlparse(announce_url)
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.port = port
        self.transaction_id = os.urandom(4)

    async def get_peers(self):
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)

        port = self.url.port or (80 if self.url.scheme == "udp" else 6969)
        tracker_addr = (self.url.hostname, port)

        connect_req = struct.pack(
            "!Q I I",
            0x41727101980,
            0,
            int.from_bytes(self.transaction_id, "big")
        )
        await loop.sock_sendto(sock, connect_req, tracker_addr)
        data, _ = await loop.sock_recvfrom(sock, 2048)

        action, txn_id, conn_id = struct.unpack("!I I Q", data)
        if action != 0 or txn_id != int.from_bytes(self.transaction_id, "big"):
            sock.close()
            raise RuntimeError("Invalid connect response")

        transaction_id = int.from_bytes(os.urandom(4), "big")
        announce_req = struct.pack(
            "!Q I I 20s 20s Q Q Q I I I I H",
            conn_id, 1, transaction_id,
            self.info_hash, self.peer_id,
            0, 0, 0, 0, 0, 0, -1 & 0xFFFFFFFF, self.port
        )
        await loop.sock_sendto(sock, announce_req, tracker_addr)
        data, _ = await loop.sock_recvfrom(sock, 4096)
        sock.close()

        action, txn_id, interval, leechers, seeders = struct.unpack("!I I I I I", data[:20])
        if action != 1 or txn_id != transaction_id:
            raise RuntimeError("Invalid announce response")

        peers_bin = data[20:]
        peers = []
        for i in range(0, len(peers_bin), 6):
            ip = socket.inet_ntoa(peers_bin[i:i+4])
            port = struct.unpack("!H", peers_bin[i+4:i+6])[0]
            peers.append((ip, port))
        return peers
