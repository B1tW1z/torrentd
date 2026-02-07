"""
Parse magnet links (BEP 9). For DHT-only magnets, info_hash comes from xt=urn:btih:<hex or b32>.
"""
import base64
import re


def parse_magnet(uri: str) -> bytes:
    """
    Extract info_hash from magnet URI.
    xt can be urn:btih:<40-char hex> or urn:btih:<32-char base32>.
    Returns 20-byte info_hash.
    """
    params = {}
    for part in uri.replace("?", "&").split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.lower()] = v

    xt = params.get("xt", "")
    if not xt.startswith("urn:btih:"):
        raise ValueError("Missing or invalid xt=urn:btih:... in magnet link")
    digest = xt[9:].strip()

    if len(digest) == 40 and re.match(r"^[0-9a-fA-F]{40}$", digest):
        return bytes.fromhex(digest)
    if len(digest) == 32:
        try:
            return base64.b32decode(digest.upper())
        except Exception:
            pass
    raise ValueError("Could not decode btih value (need 40 hex or 32 base32 chars)")
