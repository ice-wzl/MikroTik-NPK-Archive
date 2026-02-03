#!/usr/bin/python3
import argparse
import os
import re
import requests
from pathlib import Path

# Import the lists from the release_tree module
from release_tree.dev_release import dev_release
from release_tree.long_term import long_term
from release_tree.stable_branch import stable_branch
from release_tree.testing_release import testing_release

# Base directory for downloads
DOWNLOAD_BASE_DIR = "downloads"

# Branch name mapping for directory structure
BRANCH_DIRS = {
    1: "long_term",
    2: "stable",
    3: "testing",
    4: "development"
}


def parse_changelog(changelog_path="changelog.txt"):
    """
    Parse the changelog.txt file and return categorized version lists.
    
    Format of changelog.txt:
    version_number
    release_type (Development, Stable, Testing, Long-term) - can be multiple lines
    date (YYYY-MM-DD)
    empty line
    """
    versions = {
        "development": [],
        "stable": [],
        "testing": [],
        "long_term": []
    }
    
    try:
        with open(changelog_path, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f"[!] Changelog file not found: {changelog_path}")
        return versions
    
    # Split by double newlines to get entries
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        # Skip empty lines
        if not lines[i].strip():
            i += 1
            continue
        
        # First non-empty line is the version
        version = lines[i].strip()
        i += 1
        
        # Collect release types until we hit a date or empty line
        release_types = []
        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            # Check if it's a date (YYYY-MM-DD format)
            if re.match(r'^\d{4}-\d{2}-\d{2}$', line):
                i += 1
                break
            release_types.append(line)
            i += 1
        
        # Categorize the version based on release types
        for release_type in release_types:
            if release_type == "Long-term":
                if version not in versions["long_term"]:
                    versions["long_term"].append(version)
            elif release_type == "Development":
                if version not in versions["development"]:
                    versions["development"].append(version)
            elif release_type == "Testing":
                if version not in versions["testing"]:
                    versions["testing"].append(version)
            elif release_type == "Stable":
                # Only add to stable if not already in long_term
                if version not in versions["long_term"] and version not in versions["stable"]:
                    versions["stable"].append(version)
    
    return versions


def get_versions_for_branch(branch, use_changelog=True, changelog_path="changelog.txt"):
    """
    Get version list for a specific branch.
    If use_changelog is True, parse changelog.txt dynamically.
    Otherwise, use the static lists from release_tree module.
    """
    if use_changelog:
        versions = parse_changelog(changelog_path)
        branch_map = {
            1: versions["long_term"],
            2: versions["stable"],
            3: versions["testing"],
            4: versions["development"]
        }
        return branch_map.get(branch, [])
    else:
        branch_map = {
            1: long_term,
            2: stable_branch,
            3: testing_release,
            4: dev_release
        }
        return branch_map.get(branch, [])


def arch_selection():
    # x86 does not specify arch designation in download url 
    arch = {1: "arm", 2: "arm64", 3: "mipsbe", 4: "mmips", 5: "smips", 6: "tile", 7: "ppc", 8: "x86"}

    for key, value in arch.items():
        print(key, value)
    user_arch = input("[+] Select your arch: ")
    try:
        user_arch = int(user_arch)
        if user_arch not in arch:
            print("[!] Please enter a valid number")
            return arch_selection()
        else:
            return user_arch
    except ValueError as e:
        print("[!] Please enter a valid number")
        return arch_selection()


def branch_selection():
    branches = {1: "Long-term release tree", 2: "Stable release tree", 3: "Testing release tree", 4: "Development release tree"}
    for key, value in branches.items():
        print(key, value)
    user_branch = input("[+] Select your branch: ")
    try:
        user_branch = int(user_branch)
        if user_branch not in branches:
            print("[!] Please enter a valid number")
            return branch_selection()
        else:
            return user_branch
    except ValueError as e:
        print("[!] Please enter a valid number")
        return branch_selection()


def get_version(branch_selection, use_changelog=True):
    """Get version selection from user."""
    versions = get_versions_for_branch(branch_selection, use_changelog)
    
    print("[+] Type the version you want")
    print(', '.join(versions))
    user_version = input(">>> ")
    
    if user_version not in versions:
        return False
    else:
        return user_version


def get_download_path(branch, arch_name, filename):
    """
    Get the full path for downloading a file.
    Creates directory structure: downloads/<branch>/<arch>/filename
    """
    branch_dir = BRANCH_DIRS.get(branch, "unknown")
    download_dir = Path(DOWNLOAD_BASE_DIR) / branch_dir / arch_name
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir / filename


def file_exists(branch, arch_name, filename):
    """Check if the NPK file already exists."""
    file_path = get_download_path(branch, arch_name, filename)
    return file_path.exists()


def get_all(branch, use_changelog=True):
    """Download all NPK files for a specific branch."""
    versions = get_versions_for_branch(branch, use_changelog)
    
    if not versions:
        print(f"[!] No versions found for branch {branch}")
        return
    
    print(f"[+] Found {len(versions)} versions to download")
    
    for arch in range(1, 9):
        for version in versions:
            get_npk(arch, branch, version)


def get_npk(arch, branch, version):
    """
    Download a single NPK file.
    Skips download if file already exists.
    """
    # example target
    # https://download.mikrotik.com/routeros/6.30.1/routeros-mipsbe-6.30.1.npk
    # testing release tree
    # https://download.mikrotik.com/routeros/7.16rc4/routeros-7.16rc4-arm.npk
    arch_mapper = {1: "arm", 2: "arm64", 3: "mipsbe", 4: "mmips", 5: "smips", 6: "tile", 7: "ppc", 8: "x86"}
    
    arch_normalized = arch_mapper.get(arch)
    
    # Determine URL format based on version pattern
    # RC and beta versions use: routeros-{version}-{arch}.npk
    # Stable versions use: routeros-{arch}-{version}.npk (except x86)
    is_prerelease = 'rc' in version.lower() or 'beta' in version.lower()
    
    if is_prerelease:
        if arch_normalized == "x86":
            filename = f"routeros-{version}-{arch_normalized}.npk"
        else:
            filename = f"routeros-{version}-{arch_normalized}.npk"
        base_url = f"https://download.mikrotik.com/routeros/{version}/{filename}"
    else:
        if arch_normalized != "x86":
            filename = f"routeros-{arch_normalized}-{version}.npk"
        else:
            filename = f"routeros-{version}.npk"
        base_url = f"https://download.mikrotik.com/routeros/{version}/{filename}"
    
    # Check if file already exists
    if file_exists(branch, arch_normalized, filename):
        print(f"[=] Skipping {filename} - already exists")
        return
    
    print(f"[+] Downloading: {base_url}")
    
    try:
        req = requests.get(base_url, timeout=30)
        print(f"[+] Status Code: {req.status_code}")
        
        if req.status_code == 404:
            print(f"[!] Not found: {base_url}")
            return
        
        if req.status_code != 200:
            print(f"[!] Error downloading: HTTP {req.status_code}")
            return
        
        # Get the full destination path
        dst_path = get_download_path(branch, arch_normalized, filename)
        
        with open(dst_path, mode="wb") as file:
            file.write(req.content)
        
        print(f"[+] Saved to: {dst_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"[!] Download error: {e}")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Download MikroTik RouterOS NPK files"
    )

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group()

    # Add the arguments to the group
    group.add_argument("-a", "--all", help="Download all .npk files from a specific branch", action="store_true", dest="all")
    group.add_argument("-s", "--single", help="Download single .npk file from a branch", action="store_true", dest="single")
    
    # Add optional argument to use static lists instead of changelog
    parser.add_argument("--static", help="Use static version lists instead of parsing changelog.txt", action="store_true", dest="static")
    
    # Add optional argument to specify changelog path
    parser.add_argument("-c", "--changelog", help="Path to changelog.txt file", default="changelog.txt", dest="changelog")

    # Parse the arguments
    args = parser.parse_args()
    
    use_changelog = not args.static

    # Example usage of parsed arguments
    if args.all:
        user_branch = branch_selection()
        get_all(user_branch, use_changelog)
    elif args.single:
        user_arch = arch_selection()
        user_branch = branch_selection()
        user_version = False
    
        while user_version == False:
            user_version = get_version(user_branch, use_changelog)
    
        # debugging checks 
        # print(user_arch, user_branch, user_version)
        get_npk(user_arch, user_branch, user_version)
    else:
        parser.print_help()
