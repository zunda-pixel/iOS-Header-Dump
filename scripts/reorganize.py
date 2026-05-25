#!/usr/bin/env python3
"""Reorganize flat headers/ into letter-bucketed structure.

Before: headers/UIKitCore/UIView.h
After:  headers/U/UIKitCore/UIView.h
"""

import shutil
import sys
from pathlib import Path


def get_bucket(fw_name: str) -> str:
    first = fw_name[0] if fw_name else "_"
    return first.upper() if first.isalpha() else "_"


def is_bucket_dir(name: str) -> bool:
    return len(name) == 1 and (name.isupper() or name == "_")


def reorganize(headers_dir: Path) -> None:
    fw_dirs = [
        d for d in sorted(headers_dir.iterdir())
        if d.is_dir() and not is_bucket_dir(d.name)
    ]
    if not fw_dirs:
        print("Already organized (no top-level framework dirs found).")
        return

    print(f"Reorganizing {len(fw_dirs)} frameworks into letter buckets...")
    buckets: dict[str, int] = {}
    for fw_dir in fw_dirs:
        bucket = get_bucket(fw_dir.name)
        dest_bucket = headers_dir / bucket
        dest_bucket.mkdir(exist_ok=True)
        shutil.move(str(fw_dir), str(dest_bucket / fw_dir.name))
        buckets[bucket] = buckets.get(bucket, 0) + 1

    for b in sorted(buckets):
        print(f"  {b}/  ({buckets[b]} frameworks)")
    print(f"Done. {len(fw_dirs)} frameworks → {len(buckets)} buckets.")


if __name__ == "__main__":
    headers_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("headers")
    reorganize(headers_dir.resolve())
