"""Convert between account IDs and creation dates, using account-dates.csv.

Account IDs are handed out in order, so a table of a few hundred accounts and their creation
times is enough to date any account by interpolating between its two nearest neighbours.
"""
import bisect
import csv
import os
from datetime import datetime, timezone

TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "account-dates.csv")

with open(TABLE, newline="", encoding="utf-8") as handle:
    rows = sorted((int(row["account_id"]), datetime.fromisoformat(row["created_utc"].replace("Z", "+00:00")).timestamp())
                  for row in csv.DictReader(handle))
ACCOUNTS = [account for account, _ in rows]
SECONDS = [seconds for _, seconds in rows]


def interpolate(value, known, wanted):
    position = bisect.bisect_left(known, value)
    position = min(max(position, 1), len(known) - 1)
    low, high = known[position - 1], known[position]
    share = (value - low) / (high - low)
    return wanted[position - 1] + share * (wanted[position] - wanted[position - 1])


def account_to_time(account_id):
    return datetime.fromtimestamp(interpolate(account_id, ACCOUNTS, SECONDS), timezone.utc)


def time_to_account(moment):
    return interpolate(moment.timestamp(), SECONDS, ACCOUNTS)
