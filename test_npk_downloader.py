import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import npk_downloader as downloader


class FilenameTests(unittest.TestCase):
    def test_v7_architecture_follows_version(self):
        self.assertEqual(
            downloader.filename_for_version("7.16.1", "arm"),
            "routeros-7.16.1-arm.npk",
        )

    def test_v7_x86_has_no_architecture_suffix(self):
        self.assertEqual(
            downloader.filename_for_version("7.16rc4", "x86"),
            "routeros-7.16rc4.npk",
        )

    def test_v6_prerelease_uses_legacy_order(self):
        self.assertEqual(
            downloader.filename_for_version("6.49rc2", "mipsbe"),
            "routeros-mipsbe-6.49rc2.npk",
        )

    def test_v6_ppc_is_called_powerpc(self):
        self.assertEqual(
            downloader.filename_for_version("6.49.18", "ppc"),
            "routeros-powerpc-6.49.18.npk",
        )

    def test_v6_x86_keeps_architecture(self):
        self.assertEqual(
            downloader.filename_for_version("6.16", "x86"),
            "routeros-x86-6.16.npk",
        )

    def test_package_identity_accepts_both_filename_orders(self):
        expected = ("7.1rc1", "arm")
        self.assertEqual(
            downloader.package_identity("routeros-7.1rc1-arm.npk"), expected
        )
        self.assertEqual(
            downloader.package_identity("routeros-arm-7.1rc1.npk"), expected
        )

    def test_package_identity_normalizes_powerpc(self):
        self.assertEqual(
            downloader.package_identity("routeros-powerpc-6.49.18.npk"),
            ("6.49.18", "ppc"),
        )


class ChangelogTests(unittest.TestCase):
    def test_official_changelog_versions_are_deduplicated_and_validated(self):
        response = Mock()
        response.text = """
            <div data-changelog-version="7.2"></div>
            <div data-changelog-version="7.2rc1"></div>
            <div data-changelog-version="7.2"></div>
            <div data-changelog-version="not-a-version"></div>
        """
        response.raise_for_status.return_value = None
        session = Mock()
        session.get.return_value = response

        versions = downloader.fetch_official_versions(5, session=session)

        self.assertEqual(versions, ["7.2", "7.2rc1", "6.32", "6.21"])
        session.get.assert_called_once_with(
            downloader.OFFICIAL_CHANGELOG_URL,
            params={"channelFilter": "", "versionFilter": ""},
            timeout=30,
        )


class ExistingArchiveTests(unittest.TestCase):
    def test_index_recurses_across_branch_directories(self):
        with TemporaryDirectory() as directory:
            package = Path(directory) / "stable" / "arm"
            package.mkdir(parents=True)
            existing_file = package / "routeros-arm-7.1rc1.npk"
            existing_file.touch()

            packages = downloader.index_existing_packages([directory])

            self.assertEqual(packages[("7.1rc1", "arm")], existing_file)

    def test_download_skips_semantically_equivalent_existing_file(self):
        session = Mock()
        existing = {
            ("7.1rc1", "arm"): Path("stable/arm/routeros-arm-7.1rc1.npk")
        }

        result = downloader.get_npk(
            1, 5, "7.1rc1", session=session, existing_packages=existing
        )

        self.assertTrue(result)
        session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
