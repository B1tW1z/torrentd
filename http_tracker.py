import aiohttp
from urllib.parse import urlencode
from bencode import decode

class Tracker:
    def __init__(self, torrent, peer_id, port=6881):
        self.torrent = torrent
        self.peer_id = peer_id
        self.port = port

    async def get_peers(self):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': self.port,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent.length,
            'compact': 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.torrent.announce, params=params) as resp:
                data = await resp.read()

        response = decode(data)
        peers_bin = response[b'peers']

        peers = []
        for i in range(0, len(peers_bin), 6):
            ip = '.'.join(map(str, peers_bin[i:i+4]))
            port = int.from_bytes(peers_bin[i+4:i+6], 'big')
            peers.append((ip, port))

        return peers
