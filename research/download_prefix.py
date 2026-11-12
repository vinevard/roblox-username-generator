"""Download the first N bytes of the archive.org file 'rbx-users-6b.7z' with parallel range requests.

Usage: python -I download_prefix.py <output file> <total bytes wanted>
Resumes from the current size of the output file.
"""
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://ia600909.us.archive.org/22/items/rbx-users-6b.7z/rbx-users-6b.7z"
CHUNK = 16 * 1024 * 1024
WORKERS = 8

out_path, wanted = sys.argv[1], int(sys.argv[2])


def fetch(start):
    end = min(start + CHUNK, wanted) - 1
    for attempt in range(30):
        try:
            request = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}", "User-Agent": "research-script"})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
            if len(data) == end - start + 1:
                return data
        except Exception as error:
            last = error
        time.sleep(min(60, 2 + attempt * 3))
    raise RuntimeError(f"chunk at {start} failed")


done = os.path.getsize(out_path) if os.path.exists(out_path) else 0
done -= done % CHUNK
began, began_at = time.time(), done
with open(out_path, "r+b" if done else "wb") as out, ThreadPoolExecutor(WORKERS) as pool:
    out.truncate(done)
    out.seek(done)
    starts = range(done, wanted, CHUNK)
    for index, data in enumerate(pool.map(fetch, starts)):
        out.write(data)
        out.flush()
        done += len(data)
        if index % 8 == 0:
            rate = (done - began_at) / (time.time() - began) / 1e6
            print(f"{done / 1e9:.2f} GB of {wanted / 1e9:.1f} GB, {rate:.2f} MB/s", flush=True)
print("finished", done, flush=True)
