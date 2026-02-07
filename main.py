import asyncio
import os
import sys
from torrent import Torrent

from tracker import Tracker
from downloader import download_single_piece

# Use SelectorEventLoop on Windows to avoid UDP sock_sendto WinError 10022
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    torrent = Torrent("example.torrent")
    peer_id = b"-PC0001-" + os.urandom(12)

    tracker = Tracker(torrent, peer_id)
    try:
        peers = await tracker.get_peers()
    except (OSError, RuntimeError) as e:
        print(f"Tracker error (check network and that the tracker in the .torrent is reachable): {e}")
        return

    if not peers:
        print("No peers returned by tracker.")
        return

    print("Peers:", peers[:5])

    open("download.bin", "wb").truncate(torrent.length)

    ip, port = peers[0]
    await download_single_piece(ip, port, torrent, peer_id, piece_index=0)

if __name__ == "__main__":
    asyncio.run(main())
