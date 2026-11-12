"""Look up when a grid of Roblox accounts was created, to turn account IDs into dates.

Uses Roblox's public users API, one account per request, about one request a second.
Writes account_id,created_utc rows. Rows already in the output file are kept, so the
script can be stopped and run again.

Usage: python research/account_dates.py <output csv>
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

out_path = sys.argv[1]

API = "https://users.roblox.com/v1/users/{}"
PAUSE_SECONDS = 1.1
GRID = [
    (100_000, 10_000_000, 100_000),
    (10_500_000, 60_000_000, 500_000),
    (62_000_000, 480_000_000, 2_000_000),
    (5_300_000, 5_380_000, 2_000),
]


def created(account_id):
    """Return the creation time of the account, trying the next few IDs if one is missing."""
    for candidate in range(account_id, account_id + 5):
        request = urllib.request.Request(API.format(candidate), headers={"User-Agent": "research-script"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return candidate, json.load(response)["created"]
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    break
                time.sleep(10 * (attempt + 1))
            except (urllib.error.URLError, TimeoutError):
                time.sleep(10 * (attempt + 1))
        time.sleep(PAUSE_SECONDS)
    return None


wanted = sorted({account_id for start, end, step in GRID for account_id in range(start, end + 1, step)})
known = {}
if os.path.exists(out_path):
    with open(out_path, newline="", encoding="utf-8") as handle:
        known = {int(row["account_id"]): row["created_utc"] for row in csv.DictReader(handle)}

for index, account_id in enumerate(wanted):
    if any(account_id <= have < account_id + 5 for have in known):
        continue
    found = created(account_id)
    if found:
        known[found[0]] = found[1]
    time.sleep(PAUSE_SECONDS)
    if index % 20 == 0:
        with open(out_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["account_id", "created_utc"])
            writer.writerows(sorted(known.items()))
        print(f"{len(known)} of about {len(wanted)}", flush=True)

with open(out_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["account_id", "created_utc"])
    writer.writerows(sorted(known.items()))
print("finished:", len(known), "accounts")
