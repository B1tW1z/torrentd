# pybittorrent

A BitTorrent client in Python with HTTP/UDP trackers, peer wire protocol, multi-peer parallel downloads, rarest-first piece selection, endgame mode, DHT, magnet links (ut_metadata), PEX, and seeding.

## Features

### Implemented

- [x] **Trackers**: HTTP/HTTPS and UDP announce (BEP 3)
- [x] **Peer wire protocol**: Handshake, choke/unchoke, BITFIELD, REQUEST/PIECE, upload (seeding)
- [x] **Piece selection**: Rarest-first; endgame mode when few pieces remain
- [x] **DHT**: Minimal node (BEP 5) for peer discovery; bootstrap and `get_peers`
- [x] **Magnet links**: Parse `urn:btih:`; fetch metadata via ut_metadata (BEP 9), then download
- [x] **PEX**: Peer Exchange (BEP 11); discovered peers are added to the worker pool
- [x] **Extensions**: Reserved bit (BEP 10); extended handshake, ut_metadata, PEX
- [x] **Seed mode**: TCP server that handshakes and serves REQUESTs for a completed file
- [x] **Timeouts**: Handshake and block request timeouts to avoid deadlocks

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



### Todo Features

- [ ] **Resume / save progress** – Persist completed piece indices; on restart load and only request missing pieces
- [ ] **Progress display** – Show % done and download speed (e.g. `45% | 2.1 MB/s`) in the CLI
- [ ] **Multi-file torrents** – Support `info[b"files"]`: create directories and map pieces to multiple files
- [ ] **Private flag** – If `info.get(b"private") == 1`, disable DHT and PEX
- [ ] **Graceful shutdown** – On Ctrl+C, save completed pieces for resume and close connections cleanly
- [ ] **DHT node persistence** – Save good DHT nodes to a file and bootstrap from them on next run



Inspired by: [BitTorrent in Python](https://markuseliasson.se/article/bittorrent-in-python/)


--- 
