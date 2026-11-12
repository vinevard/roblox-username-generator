"""Profile username prefixes by account ID in the 'first 6 billion roblox users' dump.

Reads a (possibly partial) copy of rbx-users-6b.7z: one LZMA2 stream starting at byte 32,
16 MB dictionary, containing lines of "id:username".

Usage: python -I analyze.py <archive prefix file> <candidate words file> <output json> [max_id]

For every username that starts with a capitalised candidate word followed by at least
three more characters, counts (word, id band, kind) where kind is 1 when the remainder,
lower-cased, is an early username, else 0. Early usernames are read in whole blocks until
account BASE_LIMIT is passed, which in practice reaches about account 2.57 million.
Also tallies CamelCase names of the form WordWord[digits] by first and second word.
"""
import json
import lzma
import multiprocessing
import re
import sys
import time

BAND = 5_000_000
ERA = 50_000_000
BASE_LIMIT = 2_000_000
BLOCK_BYTES = 8 * 1024 * 1024
WORKERS = 5
CAMEL = re.compile(rb"([A-Z][a-z]{2,11})([A-Z][a-z]{2,11})(\d{0,4})")

candidates = set()
lengths = ()
base = set()


def lines_from(path):
    """Yield blocks of whole lines decompressed from the archive prefix."""
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "dict_size": 1 << 24}])
    pending = b""
    with open(path, "rb") as source:
        source.seek(32)
        while True:
            chunk = source.read(2 * 1024 * 1024)
            if not chunk:
                break
            try:
                pending += decoder.decompress(chunk)
            except (lzma.LZMAError, EOFError):
                break
            if len(pending) >= BLOCK_BYTES:
                cut = pending.rfind(b"\n") + 1
                yield pending[:cut]
                pending = pending[cut:]
    cut = pending.rfind(b"\n") + 1
    if cut:
        yield pending[:cut]


def build_base(path):
    names = set()
    for block in lines_from(path):
        last_id = 0
        for line in block.split(b"\n"):
            split = line.find(b":")
            if split < 0:
                continue
            last_id = int(line[:split])
            name = line[split + 1:].lower()
            if len(name) >= 4 and not name.isdigit():
                names.add(name)
        if last_id >= BASE_LIMIT:
            break
    return names


def init_worker(candidate_list, base_path):
    global candidates, lengths, base
    candidates = set(candidate_list)
    lengths = tuple(sorted({len(word) for word in candidates}))
    with open(base_path, "rb") as handle:
        base = set(handle.read().split(b"\n"))


def process(block):
    prefix_counts = {}
    camel_counts = {}
    band_totals = {}
    last_id = 0
    for line in block.split(b"\n"):
        split = line.find(b":")
        if split < 0:
            continue
        name = line[split + 1:]
        first = name[:1]
        if first < b"A" or first > b"Z":
            continue
        user_id = int(line[:split])
        last_id = user_id
        size = len(name)
        for length in lengths:
            if size - length < 3:
                break
            prefix = name[:length]
            if prefix in candidates:
                kind = 1 if name[length:].lower() in base else 0
                key = (prefix, user_id // BAND, kind)
                prefix_counts[key] = prefix_counts.get(key, 0) + 1
        match = CAMEL.fullmatch(name)
        if match:
            era = user_id // ERA
            digits = 1 if match.group(3) else 0
            for position in (1, 2):
                key = (match.group(position), position, digits, era)
                camel_counts[key] = camel_counts.get(key, 0) + 1
    lines = block.count(b"\n")
    band = last_id // BAND
    band_totals[band] = lines
    return prefix_counts, camel_counts, band_totals, last_id


def main():
    path, words_path, out_path = sys.argv[1:4]
    max_id = int(sys.argv[4]) if len(sys.argv) > 4 else None
    words = [line.strip().encode() for line in open(words_path, encoding="utf-8") if line.strip()]

    started = time.time()
    base_path = out_path + ".base"
    names = build_base(path)
    with open(base_path, "wb") as handle:
        handle.write(b"\n".join(names))
    print(f"base set: {len(names)} names in {time.time() - started:.0f}s", flush=True)
    del names

    prefix_counts, camel_counts, band_totals = {}, {}, {}
    last_id = 0
    with multiprocessing.Pool(WORKERS, init_worker, (words, base_path)) as pool:
        outstanding = []

        def collect(result):
            nonlocal last_id
            part_prefix, part_camel, part_bands, part_last = result.get()
            for key, count in part_prefix.items():
                prefix_counts[key] = prefix_counts.get(key, 0) + count
            for key, count in part_camel.items():
                camel_counts[key] = camel_counts.get(key, 0) + count
            for key, count in part_bands.items():
                band_totals[key] = band_totals.get(key, 0) + count
            last_id = max(last_id, part_last)

        for index, block in enumerate(lines_from(path)):
            outstanding.append(pool.apply_async(process, (block,)))
            if len(outstanding) >= WORKERS * 3:
                collect(outstanding.pop(0))
            if index % 200 == 199:
                # Drop CamelCase tokens seen only once or twice so the tally stays small.
                for key in [key for key, count in camel_counts.items() if count < 3]:
                    del camel_counts[key]
                print(f"block {index + 1}, up to id ~{last_id:,}, {time.time() - started:.0f}s", flush=True)
            if max_id and last_id >= max_id:
                break
        for result in outstanding:
            collect(result)

    camel_counts = {key: count for key, count in camel_counts.items() if count >= 20}
    output = {
        "band": BAND,
        "era": ERA,
        "last_id": last_id,
        "band_totals": {str(key): count for key, count in sorted(band_totals.items())},
        "prefix": [[key[0].decode(), key[1], key[2], count] for key, count in prefix_counts.items()],
        "camel": [[key[0].decode(), key[1], key[2], key[3], count] for key, count in camel_counts.items()],
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle)
    print(f"done: up to id {last_id:,}, {len(prefix_counts)} prefix keys, {len(camel_counts)} camel keys, {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
