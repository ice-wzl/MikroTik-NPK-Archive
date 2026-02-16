#!/usr/bin/env python3
"""Generate firmware.json from out.txt. Run when out.txt is updated."""
import json
import re

def main():
    entries = []
    with open("out.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.endswith(".npk"):
                continue
            # ./branch/arch/filename.npk
            path = line.lstrip("./")
            parts = path.split("/")
            if len(parts) != 3:
                continue
            branch, arch, name = parts
            entries.append({
                "path": "/" + path,
                "branch": branch,
                "arch": arch,
                "name": name,
            })

    with open("firmware.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=0)

if __name__ == "__main__":
    main()
