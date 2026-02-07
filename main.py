"""
Entry point: run download for example.torrent (or first .torrent in CWD).
Uses new package layout: core, trackers, engine, dht, extensions.
"""
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from core.torrent import Torrent
from trackers import get_peers
from engine.downloader import download


async def main():
    torrent_path = "example.torrent"
    if not os.path.isfile(torrent_path):
        print(f"Place a .torrent file (e.g. {torrent_path}) in the current directory.")
        return

    path, err = await download(
        torrent_path,
        download_path="download.bin",
        max_workers=20,
        use_dht=True,
    )
    if err:
        print(f"Tracker/error: {err}")
        return
    if path:
        print(f"Downloaded to {path}")
    else:
        print("Download incomplete.")


if __name__ == "__main__":
    asyncio.run(main())
