#!/usr/bin/python3
import argparse
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

from release_tree.dev_release import dev_release
from release_tree.long_term import long_term
from release_tree.stable_branch import stable_branch
from release_tree.testing_release import testing_release

DOWNLOAD_BASE_DIR = "downloads"
OFFICIAL_CHANGELOG_URL = "https://mikrotik.com/download/changelogs"
DOWNLOAD_ROOT_URL = "https://download.mikrotik.com/routeros/"

BRANCH_DIRS = {
    1: "long_term",
    2: "stable",
    3: "testing",
    4: "development",
    5: "all",
}

BRANCH_NAMES = {
    1: "Long-term release tree",
    2: "Stable release tree",
    3: "Testing release tree",
    4: "Development release tree",
    5: "All historical releases",
}

# Values are the RouterOS v7 architecture names. RouterOS v6 and older called
# ppc "powerpc"; filename_for_version() handles that server-side alias.
ARCHITECTURES = {
    1: "arm",
    2: "arm64",
    3: "mipsbe",
    4: "mmips",
    5: "smips",
    6: "tile",
    7: "ppc",
    8: "x86",
    9: "mipsle",
}

OFFICIAL_CHANNEL_FILTERS = {
    1: "longTerm",
    2: "stable",
    3: "testing",
    4: "development",
    5: "",
}

# These stable packages are present on download.mikrotik.com but omitted from
# MikroTik's historical changelog page. They were verified against the archive
# using the same URL convention as the downloader.
ARCHIVE_ONLY_VERSIONS = {
    2: ["6.32", "6.21"],
    5: ["6.32", "6.21"],
}

VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:beta\d+|rc\d+)?$")
CHANGELOG_VERSION_RE = re.compile(r'data-changelog-version="([^"]+)"')


def unique(items):
    """Return items in their original order with duplicates removed."""
    return list(dict.fromkeys(items))


def parse_changelog(changelog_path="changelog.txt"):
    """Parse the repository's offline changelog snapshot."""
    versions = {
        "development": [],
        "stable": [],
        "testing": [],
        "long_term": [],
    }

    try:
        with open(changelog_path, "r", encoding="utf-8") as changelog_file:
            lines = changelog_file.read().splitlines()
    except FileNotFoundError:
        print(f"[!] Changelog file not found: {changelog_path}")
        return versions

    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue

        version = lines[i].strip()
        i += 1
        release_types = []

        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", line):
                i += 1
                break
            release_types.append(line)
            i += 1

        for release_type in release_types:
            key = {
                "Long-term": "long_term",
                "Development": "development",
                "Testing": "testing",
                "Stable": "stable",
            }.get(release_type)
            if key and version not in versions[key]:
                versions[key].append(version)

    return versions


def fetch_official_versions(branch, session=requests, timeout=30):
    """Read version identifiers from MikroTik's official historical changelog."""
    params = {
        "channelFilter": OFFICIAL_CHANNEL_FILTERS[branch],
        "versionFilter": "",
    }
    response = session.get(OFFICIAL_CHANGELOG_URL, params=params, timeout=timeout)
    response.raise_for_status()

    versions = unique(CHANGELOG_VERSION_RE.findall(response.text))
    versions = [version for version in versions if VERSION_RE.fullmatch(version)]
    if not versions:
        raise ValueError("the official changelog response contained no versions")
    return unique(versions + ARCHIVE_ONLY_VERSIONS.get(branch, []))


def offline_versions(branch, use_static=False, changelog_path="changelog.txt"):
    """Return versions from one of the repository's offline snapshots."""
    if use_static:
        by_branch = {
            1: long_term,
            2: stable_branch,
            3: testing_release,
            4: dev_release,
        }
    else:
        parsed = parse_changelog(changelog_path)
        by_branch = {
            1: parsed["long_term"],
            2: parsed["stable"],
            3: parsed["testing"],
            4: parsed["development"],
        }

    if branch == 5:
        return unique(
            version
            for branch_number in (1, 2, 3, 4)
            for version in by_branch[branch_number]
        )
    return list(by_branch.get(branch, []))


def get_versions_for_branch(
    branch,
    use_official=True,
    use_static=False,
    changelog_path="changelog.txt",
    session=requests,
):
    """Get versions online, falling back to the selected offline snapshot."""
    if use_official:
        try:
            return fetch_official_versions(branch, session=session)
        except (requests.RequestException, ValueError) as error:
            print(f"[!] Could not read the official changelog: {error}")
            print("[!] Falling back to the local changelog snapshot")

    return offline_versions(branch, use_static, changelog_path)


def arch_selection():
    for key, value in ARCHITECTURES.items():
        print(key, value)
    try:
        user_arch = int(input("[+] Select your arch: "))
    except ValueError:
        user_arch = 0
    if user_arch not in ARCHITECTURES:
        print("[!] Please enter a valid number")
        return arch_selection()
    return user_arch


def branch_selection():
    for key, value in BRANCH_NAMES.items():
        print(key, value)
    try:
        user_branch = int(input("[+] Select your branch: "))
    except ValueError:
        user_branch = 0
    if user_branch not in BRANCH_NAMES:
        print("[!] Please enter a valid number")
        return branch_selection()
    return user_branch


def get_version(branch, **version_options):
    versions = get_versions_for_branch(branch, **version_options)
    print("[+] Type the version you want")
    print(", ".join(versions))
    user_version = input(">>> ").strip()
    return user_version if user_version in versions else False


def filename_for_version(version, arch_name):
    """Build the combined RouterOS package name used by MikroTik's archive."""
    major = int(version.split(".", 1)[0])
    if major >= 7:
        if arch_name == "x86":
            return f"routeros-{version}.npk"
        return f"routeros-{version}-{arch_name}.npk"

    legacy_arch = "powerpc" if arch_name == "ppc" else arch_name
    return f"routeros-{legacy_arch}-{version}.npk"


def download_url(version, filename):
    return urljoin(DOWNLOAD_ROOT_URL, f"{version}/{filename}")


def package_identity(filename):
    """Return (version, architecture) for both old and new package names."""
    name = Path(filename).name.lower()
    if not name.startswith("routeros-") or not name.endswith(".npk"):
        return None

    parts = name[len("routeros-"):-len(".npk")].split("-")
    if len(parts) == 1 and VERSION_RE.fullmatch(parts[0]):
        return parts[0], "x86"
    if len(parts) != 2:
        return None

    first, second = parts
    if VERSION_RE.fullmatch(first):
        version, arch_name = first, second
    elif VERSION_RE.fullmatch(second):
        arch_name, version = first, second
    else:
        return None

    if arch_name == "powerpc":
        arch_name = "ppc"
    if arch_name not in ARCHITECTURES.values():
        return None
    return version, arch_name


def index_existing_packages(paths):
    """Index NPKs below one or more existing archive directories."""
    packages = {}
    for path in paths or []:
        root = Path(path).expanduser()
        if not root.exists():
            print(f"[!] Existing archive path not found: {root}")
            continue

        candidates = [root] if root.is_file() else root.rglob("*.npk")
        try:
            for package_path in candidates:
                identity = package_identity(package_path.name)
                if identity:
                    packages.setdefault(identity, package_path)
        except OSError as error:
            print(f"[!] Could not scan existing archive {root}: {error}")

    if paths:
        print(f"[+] Indexed {len(packages)} existing packages")
    return packages


def get_download_path(branch, arch_name, filename, create=False):
    branch_dir = BRANCH_DIRS.get(branch, "unknown")
    download_dir = Path(DOWNLOAD_BASE_DIR) / branch_dir / arch_name
    if create:
        download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir / filename


def get_all(branch, existing_packages=None, **version_options):
    versions = get_versions_for_branch(branch, **version_options)
    if not versions:
        print(f"[!] No versions found for branch {branch}")
        return

    print(f"[+] Found {len(versions)} versions to download")
    for arch in ARCHITECTURES:
        for version in versions:
            get_npk(
                arch,
                branch,
                version,
                existing_packages=existing_packages,
            )


def get_npk(arch, branch, version, session=requests, existing_packages=None):
    """Download one combined RouterOS NPK, streaming it to a partial file."""
    arch_name = ARCHITECTURES.get(arch)
    if arch_name is None:
        raise ValueError(f"Unknown architecture selection: {arch}")
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid RouterOS version: {version}")

    identity = (version.lower(), arch_name)
    if existing_packages is not None and identity in existing_packages:
        print(
            f"[=] Skipping {version}/{arch_name} - already exists at "
            f"{existing_packages[identity]}"
        )
        return True

    filename = filename_for_version(version, arch_name)
    url = download_url(version, filename)
    destination = get_download_path(branch, arch_name, filename)
    if destination.exists():
        print(f"[=] Skipping {filename} - already exists")
        return True

    print(f"[+] Downloading: {url}")
    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        with session.get(url, timeout=30, stream=True) as response:
            print(f"[+] Status Code: {response.status_code}")
            if response.status_code == 404:
                print(f"[!] Not found: {url}")
                return False
            response.raise_for_status()

            destination = get_download_path(branch, arch_name, filename, create=True)
            partial = destination.with_suffix(destination.suffix + ".part")
            with open(partial, "wb") as package_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        package_file.write(chunk)
            os.replace(partial, destination)
            if existing_packages is not None:
                existing_packages[identity] = destination
            print(f"[+] Saved to: {destination}")
            return True
    except requests.RequestException as error:
        print(f"[!] Download error: {error}")
        return False
    finally:
        if partial.exists():
            partial.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Download historical MikroTik RouterOS NPK files"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-a", "--all", action="store_true",
        help="Download all NPK files from a selected branch",
    )
    group.add_argument(
        "-s", "--single", action="store_true",
        help="Download one NPK file from a selected branch",
    )

    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--offline", action="store_true",
        help="Use changelog.txt instead of MikroTik's live historical changelog",
    )
    source.add_argument(
        "--static", action="store_true",
        help="Use the legacy release_tree Python lists",
    )
    parser.add_argument(
        "-c", "--changelog", default="changelog.txt",
        help="Offline changelog path (used with --offline or as an online fallback)",
    )
    parser.add_argument(
        "--existing-dir",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Recursively skip packages already present below PATH; may be "
            "specified more than once"
        ),
    )
    args = parser.parse_args()

    version_options = {
        "use_official": not args.offline and not args.static,
        "use_static": args.static,
        "changelog_path": args.changelog,
    }

    existing_packages = index_existing_packages(args.existing_dir)

    if args.all:
        get_all(
            branch_selection(),
            existing_packages=existing_packages,
            **version_options,
        )
        return

    user_arch = arch_selection()
    user_branch = branch_selection()
    user_version = False
    while user_version is False:
        user_version = get_version(user_branch, **version_options)
        if user_version is False:
            print("[!] Version is not present in the selected release tree")
    get_npk(
        user_arch,
        user_branch,
        user_version,
        existing_packages=existing_packages,
    )


if __name__ == "__main__":
    main()
