"""Count suggested names in small bins around the start of the feature.

A suggested name here is a username that starts with one of the suggestion words and ends
with one of the early usernames written by analyze.py. Counts are per BIN accounts for
accounts below LAST_ACCOUNT. The usernames found between NAMES_FROM and NAMES_TO are
listed too, so the first run of suggested names can be read directly.

Usage: python research/launch_detail.py <archive prefix file> <base names file> <word list> <output json>
"""
import json
import sys

from analyze import lines_from

path, base_path, words_path, out_path = sys.argv[1:5]

BIN = 5_000
LAST_ACCOUNT = 8_000_000
NAMES_FROM = 5_330_000
NAMES_TO = 5_340_000

with open(base_path, "rb") as handle:
    base = set(handle.read().split(b"\n"))
with open(words_path, encoding="utf-8") as handle:
    words = {word.encode() for word in handle.read().split()}
lengths = sorted({len(word) for word in words})

counts = {}
names = []
done = False
for block in lines_from(path):
    for line in block.split(b"\n"):
        split = line.find(b":")
        if split < 0:
            continue
        user_id = int(line[:split])
        if user_id >= LAST_ACCOUNT:
            done = True
            break
        name = line[split + 1:]
        first = name[:1]
        if first < b"A" or first > b"Z":
            continue
        size = len(name)
        for length in lengths:
            if size - length < 4:
                break
            if name[:length] in words and name[length:].lower() in base:
                counts[user_id // BIN] = counts.get(user_id // BIN, 0) + 1
                if NAMES_FROM <= user_id < NAMES_TO:
                    names.append([user_id, name.decode()])
                break
    if done:
        break

with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"bin": BIN, "last_account": LAST_ACCOUNT, "counts": counts, "names": names}, handle)
print(sum(counts.values()), "suggested-looking names below account", LAST_ACCOUNT)
