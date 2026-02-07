# pybittorrent

A BitTorrent client in Python with HTTP/UDP trackers, peer wire protocol, multi-peer parallel downloads, rarest-first piece selection, endgame mode, DHT, magnet links (ut_metadata), PEX, and seeding.

## Features

- **Trackers**: HTTP/HTTPS and UDP announce (BEP 3)
- **Peer wire protocol**: Handshake, choke/unchoke, BITFIELD, REQUEST/PIECE, upload (seeding)
- **Piece selection**: Rarest-first; endgame mode when few pieces remain
- **DHT**: Minimal node (BEP 5) for peer discovery; bootstrap and `get_peers`
- **Magnet links**: Parse `urn:btih:`; fetch metadata via ut_metadata (BEP 9), then download
- **PEX**: Peer Exchange (BEP 11); discovered peers are added to the worker pool
- **Extensions**: Reserved bit (BEP 10); extended handshake, ut_metadata, PEX
- **Seed mode**: TCP server that handshakes and serves REQUESTs for a completed file

## Layout

```
core/           torrent, bencode, messages, piece, piece_manager, peer_connection, magnet
trackers/       http_tracker, udp_tracker, router
dht/            krpc, node, routing
extensions/     handshake, pex, metadata (ut_metadata fetch)
engine/         timeouts, seeder, worker, downloader
cli.py          download <torrent|magnet> | seed <torrent>
main.py         entry for example.torrent
```

## Requirements

- Python 3.8+
- No extra dependencies (stdlib only)

## Usage

```bash
python main.py

# CLI
python cli.py download file.torrent -o output.bin
python cli.py download "magnet:?xt=urn:btih:..." -o output.bin
python cli.py download file.torrent -j 30 --no-dht -p 6881
python cli.py seed file.torrent -o /path/to/downloaded/file -p 6881
```

Inspired by :

https://markuseliasson.se/article/bittorrent-in-python/


---
