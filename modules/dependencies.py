#!/usr/bin/env python3



import os
import sys
import subprocess
import shutil
from datetime import datetime as dt



__author__ = "Alejandro Gonzales-Irribarren"
__email__ = "jose.gonzalesdezavala1@unmsm.edu.pe"



LOCATION = os.path.join(os.path.dirname(__file__), "bin")
HGDOWNLOAD = "http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/"
GOLDENPATH = "https://genome.ucsc.edu/goldenPath/help/examples/"
SUCCESS = "SUCCESS"
FAILED = "FAILED"



class Binary:
    BED_TO_BIGBED = "bedToBigBed"
    HG_LOAD_CHAIN = "hgLoadChain"
    BIG_CHAIN = "bigChain.as"
    BIG_LINK = "bigLink.as"



def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(path, mode)
    print(f"Changed {path} permissions to executable.")



def _is_already_installed(binary_name):
    """Check whether package is already installed."""
    dir = shutil.which(binary_name)
    if dir:
        print(f"{binary_name} is already installed at {dir}")
        return True
    else:
        return False



def download_binary(binary_name):
    file = f"{LOCATION}/{binary_name}"

    if os.path.isfile(file):
        print(f"{binary_name} is already installed.")
        return True
    
    print(f"Downloading binaries to {LOCATION}...")
    link = f"{HGDOWNLOAD}/{binary_name}"

    cmd = subprocess.run(["wget", "-P", LOCATION, link])

    if cmd.returncode == 0:
        print(f"{binary_name} downloaded successfully.")
        make_executable(file)
        return True
    else:
        print(f"Failed to download {binary_name}, command: {cmd}")
        return False
    


def download_chain_template(template_name):
    file = f"{LOCATION}/{template_name}"

    if os.path.isfile(file):
        print(f"{template_name} is already installed.")
        return True
    
    print(f"Downloading binaries to {LOCATION}...")
    link = f"{GOLDENPATH}/{template_name}"

    cmd = subprocess.run(["wget", "-P", LOCATION, link])

    if cmd.returncode == 0:
        print(f"{template_name} downloaded successfully.")
        make_executable(file)
        return True
    else:
        print(f"Failed to download {template_name}, command: {cmd}")
        return False



def get_bedtobigbed():
    if not _is_already_installed(Binary.BED_TO_BIGBED):
        status = download_binary(Binary.BED_TO_BIGBED)
        return SUCCESS if status else FAILED
    else:
        return SUCCESS



def get_hgloadchain():
    if not _is_already_installed(Binary.HG_LOAD_CHAIN):
        status = download_binary(Binary.HG_LOAD_CHAIN)
        return SUCCESS if status else FAILED
    else:
        return SUCCESS
    


def get_bigchain():
    if not _is_already_installed(Binary.BIG_CHAIN):
        status = download_chain_template(Binary.BIG_CHAIN)
        return SUCCESS if status else FAILED
    else:
        return SUCCESS
    


def get_biglink():
    if not _is_already_installed(Binary.BIG_LINK):
        status = download_chain_template(Binary.BIG_LINK)
        return SUCCESS if status else FAILED
    else:
        return SUCCESS



def check_stats(stats):
    if all(x == SUCCESS for x in stats.values()):
        print("### All dependencies are installed ###")
        return

    for k, v in stats.items():
        if v == SUCCESS:
            continue
        elif v == FAILED:
            print(f"# Error! Could not install {k}: {v}")
            print("This is a necessary requirement, please try")
            print("to acquire the respective binary manually")
    
    if any(x == FAILED for x in stats.values()):
        print("\n### Error! Could not install some binaries (see above)")
    return



def main():

    os.mkdir(LOCATION) if not os.path.exists(LOCATION) else None

    bedtobidbed_status = get_bedtobigbed()
    hgloadchain_status = get_hgloadchain()
    biglink_status = get_biglink()
    bigchain_status = get_bigchain()


    stats = {
        Binary.BED_TO_BIGBED: bedtobidbed_status,
        Binary.HG_LOAD_CHAIN: hgloadchain_status,
        Binary.BIG_CHAIN: bigchain_status,
        Binary.BIG_LINK: biglink_status
    }

    check_stats(stats)

    return True


if __name__ == "__main__":
    main() 