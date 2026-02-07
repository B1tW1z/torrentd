"""
CLI: pybittorrent download <torrent|magnet> | seed <torrent> [options]
"""
import argparse
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main():
    parser = argparse.ArgumentParser(description="BitTorrent client (pybittorrent)")
    parser.add_argument("command", nargs="?", default="download", help="download | seed")
    parser.add_argument("target", nargs="?", help=".torrent file or magnet link")
    parser.add_argument("-o", "--output", default="download.bin", help="Output file (download) or path to file (seed)")
    parser.add_argument("-j", "--jobs", type=int, default=20, help="Max concurrent peers")
    parser.add_argument("--no-dht", action="store_true", help="Disable DHT peer discovery")
    parser.add_argument("-p", "--port", type=int, default=6881, help="Port for listen (seed) or announce")
    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        return 1

    target = args.target.strip()
    use_dht = not args.no_dht

    if args.command == "seed":
        if not os.path.isfile(target):
            print(f"Not a file: {target}", file=sys.stderr)
            return 1
        async def run_seed():
            from engine.seeder import run_seeder
            await run_seeder(target, args.output, port=args.port)
        try:
            asyncio.run(run_seed())
        except KeyboardInterrupt:
            pass
        return 0

    if args.command != "download":
        parser.print_help()
        return 1

    async def run_download():
        from engine.downloader import download, download_magnet
        if target.startswith("magnet:"):
            path, err = await download_magnet(
                target,
                download_path=args.output,
                max_workers=args.jobs,
                port=args.port,
            )
        else:
            if not os.path.isfile(target):
                print(f"Not a file: {target}", file=sys.stderr)
                return 1
            path, err = await download(
                target,
                download_path=args.output,
                max_workers=args.jobs,
                use_dht=use_dht,
                port=args.port,
            )
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        if path:
            print(f"Downloaded to {path}")
            return 0
        print("Download incomplete (no peers or interrupted).", file=sys.stderr)
        return 1

    return asyncio.run(run_download())


if __name__ == "__main__":
    sys.exit(main())
