#!/usr/bin/python3
import argparse
import requests

# Import the lists from the release_tree module
from release_tree.dev_release import dev_release
from release_tree.long_term import long_term
from release_tree.stable_branch import stable_branch
from release_tree.testing_release import testing_release


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
            arch_selection()
        else:
            return user_arch
    except ValueError as e:
        print("[!] Please enter a valid number")
        arch_selection()


def branch_selection():
    branches = {1: "Long-term release tree", 2: "Stable release tree", 3: "Testing release tree", 4: "Development release tree"}
    for key, value in branches.items():
        print(key, value)
    user_branch = input("[+] Select your branch: ")
    try:
        user_branch = int(user_branch)
        if user_branch not in branches:
            print("[!] Please enter a valid number")
            branch_selection()
        else:
            return user_branch
    except ValueError as e:
        print("[!] Please enter a valid number")
        branch_selection()


def get_version(branch_selection):
    print("[+] Type the version you want")
    if branch_selection == 1:
        print(', '.join(long_term))
        user_version = input(">>> ")
        if user_version not in long_term:
            return False
        else:
            return user_version
    elif branch_selection == 2:
        print(', '.join(stable_branch))
        user_version = input(">>> ")
        if user_version not in stable_branch:
            return False
        else:
            return user_version
    elif branch_selection == 3:
        print(', '.join(testing_release))
        user_version = input(">>> ")
        if user_version not in testing_release:
            return False
        else:
            return user_version
    else:
        print(', '.join(dev_release))
        user_version = input(">>> ")
        if user_version not in dev_release:
            return False
        else:
            return user_version


def get_all(branch):
    # long term branch 
    if branch == 1:
        for arch in range(1,9):
            for i in long_term:
                get_npk(arch, branch, i)
    elif branch == 2:
        for arch in range(1,9):
            for i in stable_branch:
                get_npk(arch, branch, i)
    elif branch == 3:
        for arch in range(1,9):
            for i in testing_release:
                get_npk(arch, branch, i)
    else:
        for arch in range(1,9):
            for i in dev_release:
                get_npk(arch, branch, i)


def get_npk(arch, branch, version):
    # example target
    # https://download.mikrotik.com/routeros/6.30.1/routeros-mipsbe-6.30.1.npk
    # testing release tree
    # https://download.mikrotik.com/routeros/7.16rc4/routeros-7.16rc4-arm.npk
    arch_mapper = {1: "arm", 2: "arm64", 3: "mipsbe", 4: "mmips", 5: "smips", 6: "tile", 7: "ppc", 8: "x86"}
    
    arch_normalized = arch_mapper.get(arch)

    if branch == 3:
        if arch_normalized == "x86":
            base_url = f"https://download.mikrotik.com/routeros/{version}/routeros-{version}-{arch_normalized}.npk"
        else:
            base_url = f"https://download.mikrotik.com/routeros/{version}/routeros-{version}-{arch_normalized}.npk"
    else:

        if arch_normalized != "x86":
            base_url = f"https://download.mikrotik.com/routeros/{version}/routeros-{arch_normalized}-{version}.npk"
        else:
            base_url = f"https://download.mikrotik.com/routeros/{version}/routeros-{version}.npk"
   
    print("[+] Target url:")
    print(base_url)
    req = requests.get(base_url)
    print(f"[+] Status Code: {req.status_code}")
    if req.status_code == 404:
        return
    dst_file = base_url.split("/")[-1]

    with open(dst_file, mode="wb") as file:
        file.write(req.content)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group()

    # Add the arguments to the group
    group.add_argument("-a", "--all", help="Download all .npk files from a specific branch", action="store_true", dest="all")
    group.add_argument("-s", "--single", help="Download single .npk file from a branch", action="store_true", dest="single")

    # Parse the arguments
    args = parser.parse_args()

    # Example usage of parsed arguments
    if args.all:
        user_branch = branch_selection()
        get_all(user_branch)
    elif args.single:
        print(f"Downloading single .npk file from {args.single}")

        user_arch = arch_selection()
        user_branch = branch_selection()
        user_version = False
    
        while user_version == False:
            user_version = get_version(user_branch)
    
        # debugging checks 
        # print(user_arch, user_branch, user_version)
        get_npk(user_arch, user_branch, user_version)
