"""Derive Roblox's suggestion words from the prefix profile, with no word list as input.

Reads the JSON written by profile_all.py (counts of each prefix per 10 million account IDs).
A prefix is kept when, in every era from account 110 million to 200 million, its count is at
least THRESHOLD above its own baseline. The baseline is the higher of its mean count in
accounts 40-90 million and its mean count in accounts 300-400 million.

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


def excess(profile):
    baseline = max(mean(profile, BEFORE_ERAS), mean(profile, AFTER_ERAS))
    return min(profile.get(str(era), 0) for era in SURGE_ERAS) - baseline


def load_scores(profile_path):
    """Return {prefix: score} for every prefix the rule considers."""
    with open(profile_path, encoding="utf-8") as handle:
        profiles = json.load(handle)["profiles"]
    return {prefix: excess(profile) for prefix, profile in profiles.items()
            if prefix.isalpha() and prefix[0].isupper() and not prefix.isupper()}


if __name__ == "__main__":
    profile_path, out_path = sys.argv[1:3]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else THRESHOLD
    words = sorted(prefix for prefix, score in load_scores(profile_path).items() if score >= threshold)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(words) + "\n")
    print(len(words), "words at threshold", threshold)
