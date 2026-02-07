from urllib.parse import urlparse

from .http_tracker import HTTPTracker
from .udp_tracker import UDPTracker


async def get_peers(torrent, peer_id, port=6881):
    scheme = urlparse(torrent.announce).scheme
    if scheme == "udp":
        tracker = UDPTracker(torrent.announce, torrent.info_hash, peer_id, port)
        return await tracker.get_peers()
    if scheme in ("http", "https"):
        tracker = HTTPTracker(torrent, peer_id, port)
        return await tracker.get_peers()
    raise RuntimeError("Unsupported tracker protocol")
