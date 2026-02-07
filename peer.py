import asyncio
import struct

class Peer:
    def __init__(self, ip, port, info_hash, peer_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id

    async def handshake(self):
        reader, writer = await asyncio.open_connection(self.ip, self.port)

        pstr = b"BitTorrent protocol"
        msg = (
            struct.pack("!B", len(pstr)) +
            pstr +
            b"\x00" * 8 +
            self.info_hash +
            self.peer_id
        )

        writer.write(msg)
        await writer.drain()

        response = await reader.readexactly(68)

        if response[28:48] != self.info_hash:
            writer.close()
            return False

        writer.close()
        return True
