import asyncio
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.bencode import decode


class HTTPTracker:
    def __init__(self, torrent, peer_id, port=6881):
        self.torrent = torrent
        self.peer_id = peer_id
        self.port = port

    def _get_peers_sync(self):
        q = (
            f"info_hash={quote(self.torrent.info_hash, safe='')}"
            f"&peer_id={quote(self.peer_id, safe='')}"
            f"&port={self.port}&uploaded=0&downloaded=0&left={self.torrent.length}&compact=1"
        )
        url = self.torrent.announce + ('&' if '?' in self.torrent.announce else '?') + q
        req = Request(url, headers={"User-Agent": "PythonTorrent/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = resp.read()
        response = decode(data)
        peers_bin = response[b'peers']
        peers = []
        for i in range(0, len(peers_bin), 6):
            ip = '.'.join(map(str, peers_bin[i:i+4]))
            port = int.from_bytes(peers_bin[i+4:i+6], 'big')
            peers.append((ip, port))
        return peers

    async def get_peers(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_peers_sync)
