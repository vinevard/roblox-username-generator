"""Derive Roblox's suggestion words from the prefix profile, with no word list as input.

Reads the JSON written by profile_all.py (counts of each prefix per 10 million account IDs).
For each prefix it works out three numbers, all per 10 million accounts:

- usual: the higher of its mean count in accounts 40-90 million and in accounts 300-400 million
- lowest: its smallest count in accounts 110-200 million, which were created in 2016
- extra: lowest minus usual

A prefix is kept when extra is at least THRESHOLD.

Usage: python research/derive_list.py <profile json> <output word list> [threshold]
"""
import json
import sys

SURGE_ERAS = range(11, 20)
BEFORE_ERAS = range(4, 9)
AFTER_ERAS = range(30, 40)
THRESHOLD = 250


def mean(profile, eras):
    return sum(profile.get(str(era), 0) for era in eras) / len(eras)


def measure(profile):
    """Return (usual, lowest, extra) for one prefix."""
    usual = max(mean(profile, BEFORE_ERAS), mean(profile, AFTER_ERAS))
    lowest = min(profile.get(str(era), 0) for era in SURGE_ERAS)
    return usual, lowest, lowest - usual


def load_measures(profile_path):
    """Return {prefix: (usual, lowest, extra)} for every prefix the rule considers."""
    with open(profile_path, encoding="utf-8") as handle:
        profiles = json.load(handle)["profiles"]
    return {prefix: measure(profile) for prefix, profile in profiles.items()
            if prefix.isalpha() and prefix[0].isupper() and not prefix.isupper()}


if __name__ == "__main__":
    profile_path, out_path = sys.argv[1:3]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else THRESHOLD
    words = sorted(prefix for prefix, (_, _, extra) in load_measures(profile_path).items() if extra >= threshold)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(words) + "\n")
    print(len(words), "words at threshold", threshold)
