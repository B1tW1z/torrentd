def decode(data):
    def _decode(i):
        if data[i:i+1] == b'i':
            i += 1
            end = data.index(b'e', i)
            return int(data[i:end]), end + 1

        if data[i:i+1] == b'l':
            i += 1
            lst = []
            while data[i:i+1] != b'e':
                val, i = _decode(i)
                lst.append(val)
            return lst, i + 1

        if data[i:i+1] == b'd':
            i += 1
            d = {}
            while data[i:i+1] != b'e':
                key, i = _decode(i)
                val, i = _decode(i)
                d[key] = val
            return d, i + 1

        # byte string
        colon = data.index(b':', i)
        length = int(data[i:colon])
        start = colon + 1
        end = start + length
        return data[start:end], end

    result, _ = _decode(0)
    return result


def encode(obj):
    if isinstance(obj, int):
        return b'i' + str(obj).encode() + b'e'

    if isinstance(obj, bytes):
        return str(len(obj)).encode() + b':' + obj

    if isinstance(obj, list):
        return b'l' + b''.join(encode(i) for i in obj) + b'e'

    if isinstance(obj, dict):
        out = b'd'
        for k in sorted(obj.keys()):
            out += encode(k) + encode(obj[k])
        return out + b'e'

    raise TypeError("Unsupported type")
