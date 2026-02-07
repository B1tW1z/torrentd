import struct

# Message IDs
CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8

# Extension (BEP 10)
EXTENDED = 20


def build_message(msg_id=None, payload=b""):
    if msg_id is None:
        return struct.pack("!I", 0)
    length = 1 + len(payload)
    return struct.pack("!I B", length, msg_id) + payload


def interested():
    return build_message(INTERESTED)


def request(index, begin, length):
    payload = struct.pack("!III", index, begin, length)
    return build_message(REQUEST, payload)


def parse_messages(buffer):
    messages = []
    offset = 0

    while len(buffer) - offset >= 4:
        length = struct.unpack("!I", buffer[offset:offset + 4])[0]

        if length == 0:
            messages.append((None, None))
            offset += 4
            continue

        if len(buffer) - offset < 4 + length:
            break

        msg_id = buffer[offset + 4]
        payload = buffer[offset + 5: offset + 4 + length]
        messages.append((msg_id, payload))
        offset += 4 + length

    return messages, buffer[offset:]
