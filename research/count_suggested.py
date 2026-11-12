"""Count suggested names by account ID across the whole life of the feature.

A suggested name here is a username that starts with one of the suggestion words and ends
with one of the early usernames written by analyze.py. The output holds:

- counts per BIN accounts, for accounts below LAST_ACCOUNT
- counts per FINE_BIN accounts between FINE_FROM and FINE_TO, around the start
- the usernames found between NAMES_FROM and NAMES_TO, so the first run can be read directly

Usage: python research/count_suggested.py <archive prefix file> <base names file> <word list> <output json>
"""
import json
import sys

from analyze import lines_from

path, base_path, words_path, out_path = sys.argv[1:5]

BIN = 5_000
LAST_ACCOUNT = 480_000_000
FINE_BIN = 100
FINE_FROM = 3_000_000
FINE_TO = 8_000_000
NAMES_FROM = 5_330_000
NAMES_TO = 5_340_000

with open(base_path, "rb") as handle:
    base = set(handle.read().split(b"\n"))
with open(words_path, encoding="utf-8") as handle:
    words = {word.encode() for word in handle.read().split()}
lengths = sorted({len(word) for word in words})

counts = {}
fine_counts = {}
names = []
done = False
for block_number, block in enumerate(lines_from(path)):
    for line in block.split(b"\n"):
        split = line.find(b":")
        if split < 0:
            continue
        name = line[split + 1:]
        first = name[:1]
        if first < b"A" or first > b"Z":
            continue
        user_id = int(line[:split])
        if user_id >= LAST_ACCOUNT:
            done = True
            break
        size = len(name)
        for length in lengths:
            if size - length < 4:
                break
            if name[:length] in words and name[length:].lower() in base:
                counts[user_id // BIN] = counts.get(user_id // BIN, 0) + 1
                if FINE_FROM <= user_id < FINE_TO:
                    fine_counts[user_id // FINE_BIN] = fine_counts.get(user_id // FINE_BIN, 0) + 1
                if NAMES_FROM <= user_id < NAMES_TO:
                    names.append([user_id, name.decode()])
                break
    if done:
        break
    if block_number % 100 == 99:
        print(f"block {block_number + 1}", flush=True)

with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"bin": BIN, "last_account": LAST_ACCOUNT, "counts": counts,
               "fine_bin": FINE_BIN, "fine_from": FINE_FROM, "fine_to": FINE_TO, "fine_counts": fine_counts,
               "names": names}, handle)
print(sum(counts.values()), "suggested-looking names below account", LAST_ACCOUNT)
