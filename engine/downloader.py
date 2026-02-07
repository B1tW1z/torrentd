"""
Orchestrate multi-peer download: tracker/DHT -> peers, PieceManager (rarest-first), workers.
Supports .torrent files and magnet links (DHT + ut_metadata).
"""
import asyncio
import os

from core.torrent import Torrent
from core.piece_manager import PieceManager
from trackers import get_peers
from .worker import run_worker, connect_peer


async def _run_download(torrent, peers, peer_id, download_path, max_workers, peer_queue=None):
    with open(download_path, "wb") as f:
        f.truncate(torrent.length)
    piece_manager = PieceManager(torrent, download_path)
    tasks = []
    for ip, p in peers[:max_workers]:
        tasks.append(asyncio.create_task(
            run_worker(ip, p, torrent, peer_id, piece_manager, download_path, peer_queue=peer_queue)
        ))

    if peer_queue:
        while not piece_manager.is_done():
            try:
                ip, p = await asyncio.wait_for(peer_queue.get(), timeout=0.5)
                tasks.append(asyncio.create_task(
                    run_worker(ip, p, torrent, peer_id, piece_manager, download_path, peer_queue=peer_queue)
                ))
            except asyncio.TimeoutError:
                pass
    await asyncio.gather(*tasks)
    return download_path if piece_manager.is_done() else None


async def download(
    torrent_path,
    download_path="download.bin",
    peer_id=None,
    port=6881,
    max_workers=20,
    use_dht=True,
    peer_queue=None,
):
    """Download from a .torrent file."""
    torrent = Torrent(torrent_path)
    peer_id = peer_id or (b"-PC0001-" + os.urandom(12))
    try:
        peers = await get_peers(torrent, peer_id, port)
    except Exception as e:
        return None, str(e)
    if use_dht:
        try:
            from dht.node import DHTNode
            dht = DHTNode(port=port + 1)
            dht_peers = await dht.get_peers(torrent.info_hash)
            dht.close()
            peers = list(dict.fromkeys(peers + dht_peers))
        except Exception:
            pass
    if not peers:
        return None, "No peers"
    if peer_queue is None:
        peer_queue = asyncio.Queue()
    result = await _run_download(torrent, peers, peer_id, download_path, max_workers, peer_queue)
    return result, None


async def download_magnet(
    magnet_uri,
    download_path="download.bin",
    peer_id=None,
    port=6881,
    max_workers=20,
):
    """Download from a magnet link: DHT get_peers + ut_metadata, then same pipeline."""
    from core.magnet import parse_magnet
    from core.bencode import decode
    from extensions.metadata import fetch_metadata

    info_hash = parse_magnet(magnet_uri)
    peer_id = peer_id or (b"-PC0001-" + os.urandom(12))

    from dht.node import DHTNode
    dht = DHTNode(port=port + 1)
    peers = await dht.get_peers(info_hash)
    dht.close()
    if not peers:
        return None, "No peers from DHT"

    # Minimal object for handshake (only info_hash needed)
    class MagnetHandshake:
        pass
    magnet_torrent = MagnetHandshake()
    magnet_torrent.info_hash = info_hash

    metadata_bin = None
    for ip, p in peers[:10]:
        conn, err = await connect_peer(ip, p, magnet_torrent, peer_id, download_path)
        if err is not None:
            continue
        try:
            metadata_bin = await asyncio.wait_for(fetch_metadata(conn), timeout=20)
            break
        except Exception:
            try:
                conn.writer.close()
                await conn.writer.wait_closed()
            except Exception:
                pass
            continue

    if metadata_bin is None:
        return None, "Could not fetch metadata from any peer"

    info = decode(metadata_bin)
    torrent = Torrent.from_metadata(info, info_hash)
    peer_queue = asyncio.Queue()
    result = await _run_download(torrent, peers, peer_id, download_path, max_workers, peer_queue)
    return result, None
