#!/usr/bin/env python3
"""Generate firmware.json by scanning a downloaded firmware tree."""

import argparse
import json
import os
from pathlib import Path


def build_entries(downloads_dir):
    """Return index entries for branch/architecture/*.npk files."""
    root = Path(downloads_dir).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"Downloads directory not found: {root}")

    entries = []
    for package_path in root.rglob("*.npk"):
        relative = package_path.relative_to(root)
        if len(relative.parts) != 3:
            continue

        branch, arch, name = relative.parts
        url_path = "/" + relative.as_posix()
        entries.append(
            {
                "path": url_path,
                "branch": branch,
                "arch": arch,
                "name": name,
            }
        )

    entries.sort(key=lambda entry: (
        entry["branch"],
        entry["arch"],
        entry["name"].lower(),
    ))
    return entries


def write_index(entries, output_path):
    """Atomically replace the JSON index after it is fully written."""
    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")

    try:
        with open(temporary, "w", encoding="utf-8") as index_file:
            json.dump(entries, index_file, indent=2)
            index_file.write("\n")
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Build firmware.json from a MikroTik NPK archive tree"
    )
    parser.add_argument(
        "--downloads-dir",
        default="downloads",
        metavar="PATH",
        help="Archive root containing branch/architecture/*.npk files",
    )
    parser.add_argument(
        "--output",
        default="firmware.json",
        metavar="PATH",
        help="Destination JSON file",
    )
    args = parser.parse_args()

    try:
        entries = build_entries(args.downloads_dir)
        write_index(entries, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")

    print(f"Indexed {len(entries)} packages from {Path(args.downloads_dir)}")
    print(f"Wrote {Path(args.output)}")


if __name__ == "__main__":
    main()
