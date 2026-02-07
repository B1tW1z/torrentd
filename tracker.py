from urllib.parse import urlparse
from udp_tracker import UDPTracker
from http_tracker import Tracker as HTTPTracker  # rename your old tracker.py logic

class Tracker:
    def __init__(self, torrent, peer_id):
        self.torrent = torrent
        self.peer_id = peer_id

    async def get_peers(self):
        scheme = urlparse(self.torrent.announce).scheme

        if scheme == "udp":
            tracker = UDPTracker(
                self.torrent.announce,
                self.torrent.info_hash,
                self.peer_id
            )
            return await tracker.get_peers()

        elif scheme in ("http", "https"):
            tracker = HTTPTracker(self.torrent, self.peer_id)
            return await tracker.get_peers()

        else:
            raise RuntimeError("Unsupported tracker protocol")
