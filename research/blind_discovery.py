"""Blind prefix discovery: find suggestion words without using any word list.

For every username Prefix+Rest where Rest (lower-cased) is one of the early usernames
written by analyze.py (about the first 2.57 million accounts), tally the prefix separately for accounts before and after
the point where suggestions appear. Genuine suggestion words are nearly absent before
and frequent after; ordinary popular words appear in both.

Usage: python -I blind_discovery.py <archive prefix file> <base names file> <output json> <pre_end> <post_start> <post_end>
"""
import json
import sys

from analyze import lines_from

path, base_path, out_path = sys.argv[1:4]
pre_end, post_start, post_end = (int(value) for value in sys.argv[4:7])
FINE_BIN = 250_000

with open(base_path, "rb") as handle:
    base = set(handle.read().split(b"\n"))

counts = {}
fine = {}
done = False
for block in lines_from(path):
    for line in block.split(b"\n"):
        split = line.find(b":")
        if split < 0:
            continue
        name = line[split + 1:]
        first = name[:1]
        if first < b"A" or first > b"Z":
            continue
        user_id = int(line[:split])
        if user_id >= post_end:
            done = True
            break
        if pre_end <= user_id < post_start:
            phase = None
        else:
            phase = 0 if user_id < pre_end else 1
        size = len(name)
        for length in range(3, 14):
            if size - length < 4:
                break
            prefix = name[:length]
            if prefix.isalpha() and name[length:].lower() in base:
                bin_key = (prefix, user_id // FINE_BIN)
                fine[bin_key] = fine.get(bin_key, 0) + 1
                if phase is not None:
                    pair = counts.get(prefix)
                    if pair is None:
                        pair = counts[prefix] = [0, 0]
                    pair[phase] += 1
    if done:
        break

kept = {prefix.decode(): pair for prefix, pair in counts.items() if pair[1] >= 15}
fine_kept = {}
for (prefix, bin_index), count in fine.items():
    word = prefix.decode()
    if word in kept:
        fine_kept.setdefault(word, {})[bin_index] = count
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"pre_end": pre_end, "post_start": post_start, "post_end": post_end, "fine_bin": FINE_BIN, "counts": kept, "fine": fine_kept}, handle)
print(len(counts), "prefixes seen,", len(kept), "kept")
