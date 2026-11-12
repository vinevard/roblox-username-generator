"""Collect example usernames for chosen prefixes and fine-grained list-word counts.

Usage: python examples_and_fine_bins.py <archive prefix file> <base names file> <paste word list> <output json>
"""
import json
import re
import sys

from analyze import lines_from

path, base_path, paste_path, out_path = sys.argv[1:5]

EXAMPLE_PREFIXES = [b"Mckinney", b"Williams", b"Rodriguez", b"Rooobux", b"Robbux", b"Highgirl", b"Misslips",
                    b"Njchick", b"Xchick", b"Earthgurl", b"Unaccountable", b"Animated", b"BRR", b"TTV"]
EXAMPLES_FROM = {b"Mckinney": 260_000_000, b"Williams": 400_000_000, b"Rodriguez": 400_000_000,
                 b"BRR": 260_000_000, b"TTV": 260_000_000, b"Animated": 120_000_000}
EXAMPLES_EACH = 25
FINE_RANGES = [(80_000_000, 125_000_000), (200_000_000, 300_000_000)]
FINE_BIN = 1_000_000

with open(base_path, "rb") as handle:
    base = set(handle.read().split(b"\n"))
paste = {word.encode() for word in open(paste_path, encoding="utf-8").read().split()}
lengths = sorted({len(word) for word in paste})
finder = re.compile(rb"^(\d+):((?:" + b"|".join(EXAMPLE_PREFIXES) + rb")[^\n]*)$", re.M)

examples = {prefix.decode(): [] for prefix in EXAMPLE_PREFIXES}
fine = {}
fine_all = {}
for block in lines_from(path):
    for match in finder.finditer(block):
        user_id, name = int(match.group(1)), match.group(2)
        for prefix in EXAMPLE_PREFIXES:
            if name.startswith(prefix):
                bucket = examples[prefix.decode()]
                if user_id >= EXAMPLES_FROM.get(prefix, 0) and len(bucket) < EXAMPLES_EACH:
                    bucket.append([user_id, name.decode("utf-8", "replace")])
                break
    first_id = int(block[:block.find(b":")])
    last_line = block[block.rfind(b"\n", 0, len(block) - 1) + 1:]
    last_id = int(last_line[:last_line.find(b":")])
    if not any(first_id < end and last_id >= start for start, end in FINE_RANGES):
        continue
    for line in block.split(b"\n"):
        split = line.find(b":")
        if split < 0:
            continue
        name = line[split + 1:]
        first = name[:1]
        if first < b"A" or first > b"Z":
            continue
        user_id = int(line[:split])
        size = len(name)
        for length in lengths:
            if size - length < 4:
                break
            if name[:length] in paste:
                bin_index = user_id // FINE_BIN
                fine_all[bin_index] = fine_all.get(bin_index, 0) + 1
                if name[length:].lower() in base:
                    fine[bin_index] = fine.get(bin_index, 0) + 1

with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"examples": examples, "fine_base": fine, "fine_all": fine_all, "fine_bin": FINE_BIN}, handle)
print("done")
