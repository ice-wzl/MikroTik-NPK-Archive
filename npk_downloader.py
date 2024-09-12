#!/usr/bin/python3
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



if __name__ == '__main__':

    user_arch = arch_selection()
    user_branch = branch_selection()
    user_version = False
    
    while user_version == False:
        user_version = get_version(user_branch)
    
    # debugging checks 
    print(user_arch, user_branch, user_version)
