"""Blind prefix profile over the whole downloaded range.

For every username Prefix+Rest where Prefix is alphabetic and starts with a capital and
Rest (lower-cased, at least four characters) is one of the early usernames written by
analyze.py (about the first 2.57 million accounts), counts (Prefix, id // ERA). No word list is used.
Also tallies CamelCase names WordWord[digits] by first and second word per CAMEL_ERA.

Usage: python profile_all.py <archive prefix file> <base names file> <output json> [max_id]
"""
import json
import multiprocessing
import os
import re
import sys
import time

from analyze import lines_from

ERA = 10_000_000
CAMEL_ERA = 50_000_000
WORKERS = 3
PRUNE_ABOVE = 3_000_000
CHECKPOINT_BLOCKS = 400
CAMEL = re.compile(rb"([A-Z][a-z]{2,11})([A-Z][a-z]{2,11})(\d{0,4})")

base = set()


def init_worker(base_path):
    global base
    with open(base_path, "rb") as handle:
        base = set(handle.read().split(b"\n"))


def process(block):
    prefix_counts = {}
    camel_counts = {}
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
        for length in range(3, 15):
            if size - length < 4:
                break
            prefix = name[:length]
            if not prefix.isalpha():
                break
            if name[length:].lower() in base:
                key = (prefix, user_id // ERA)
                prefix_counts[key] = prefix_counts.get(key, 0) + 1
        match = CAMEL.fullmatch(name)
        if match:
            era = user_id // CAMEL_ERA
            digits = 1 if match.group(3) else 0
            for position in (1, 2):
                key = (match.group(position), position, digits, era)
                camel_counts[key] = camel_counts.get(key, 0) + 1
    return prefix_counts, camel_counts, last_id, block.count(b"\n")


def main():
    path, base_path, out_path = sys.argv[1:4]
    max_id = int(sys.argv[4]) if len(sys.argv) > 4 else None
    started = time.time()
    profiles, camel_counts, era_totals = {}, {}, {}
    last_id = 0

    def collect(result):
        nonlocal last_id
        part_prefix, part_camel, part_last, lines = result.get()
        for (prefix, era), count in part_prefix.items():
            profile = profiles.get(prefix)
            if profile is None:
                profile = profiles[prefix] = {}
            profile[era] = profile.get(era, 0) + count
        for key, count in part_camel.items():
            camel_counts[key] = camel_counts.get(key, 0) + count
        era_totals[part_last // ERA] = era_totals.get(part_last // ERA, 0) + lines
        last_id = max(last_id, part_last)

    def save():
        output = {
            "era": ERA,
            "camel_era": CAMEL_ERA,
            "last_id": last_id,
            "era_totals": {str(key): count for key, count in sorted(era_totals.items())},
            "profiles": {prefix.decode(): {str(era): count for era, count in profile.items()}
                         for prefix, profile in profiles.items() if sum(profile.values()) >= 30},
            "camel": [[key[0].decode(), key[1], key[2], key[3], count] for key, count in camel_counts.items() if count >= 30],
        }
        with open(out_path + ".tmp", "w", encoding="utf-8") as handle:
            json.dump(output, handle)
        os.replace(out_path + ".tmp", out_path)
        return len(output["profiles"])

    with multiprocessing.Pool(WORKERS, init_worker, (base_path,)) as pool:
        outstanding = []
        for index, block in enumerate(lines_from(path)):
            outstanding.append(pool.apply_async(process, (block,)))
            if len(outstanding) >= WORKERS * 2:
                collect(outstanding.pop(0))
            if len(profiles) > PRUNE_ABOVE:
                for prefix in [prefix for prefix, profile in profiles.items() if sum(profile.values()) < 4]:
                    del profiles[prefix]
            if index % 200 == 199:
                for key in [key for key, count in camel_counts.items() if count < 3]:
                    del camel_counts[key]
                print(f"block {index + 1}, id ~{last_id:,}, {len(profiles):,} prefixes, {time.time() - started:.0f}s", flush=True)
            if index % CHECKPOINT_BLOCKS == CHECKPOINT_BLOCKS - 1:
                save()
            if max_id and last_id >= max_id:
                break
        for result in outstanding:
            collect(result)

    kept = save()
    print(f"done: id {last_id:,}, {kept:,} prefixes kept, {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
