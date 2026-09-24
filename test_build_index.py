import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import build_index


class BuildIndexTests(unittest.TestCase):
    def test_scans_branch_architecture_tree_and_sorts_entries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "downloads"
            first = root / "stable" / "arm" / "routeros-arm-6.49.npk"
            second = root / "long_term" / "arm64" / "routeros-7.23.7-arm64.npk"
            ignored = root / "unexpected" / "too" / "deep" / "ignored.npk"
            for package in (first, second, ignored):
                package.parent.mkdir(parents=True, exist_ok=True)
                package.touch()

            entries = build_index.build_entries(root)

            self.assertEqual(
                entries,
                [
                    {
                        "path": "/long_term/arm64/routeros-7.23.7-arm64.npk",
                        "branch": "long_term",
                        "arch": "arm64",
                        "name": "routeros-7.23.7-arm64.npk",
                    },
                    {
                        "path": "/stable/arm/routeros-arm-6.49.npk",
                        "branch": "stable",
                        "arch": "arm",
                        "name": "routeros-arm-6.49.npk",
                    },
                ],
            )

    def test_writes_valid_json(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "web" / "firmware.json"
            entries = [{"path": "/stable/x86/routeros-6.49.npk"}]

            build_index.write_index(entries, output)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), entries)
            self.assertFalse(Path(str(output) + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
