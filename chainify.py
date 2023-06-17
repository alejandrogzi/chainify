#!/usr/bin/env python3



import os
import sys
import subprocess
import shutil
from datetime import datetime as dt
import gzip
import re
import argparse
import modules.dependencies as dp



__author__ = "Alejandro Gonzales-Irribarren"
__email__ = "jose.gonzalesdezavala1@unmsm.edu.pe"



CHROM_SIZES_COLS = 2
LOCATION = os.path.dirname(__file__)
TEMP = "temp"
BIN = "bin"
MODULES = "modules"
BINARIES = os.path.join(LOCATION, BIN)
TEMP_DIR = os.path.join(LOCATION, MODULES, TEMP)
GITHUB = "https://github.com/alejandrogzi/chainify.git"
OUT = "out.txt"

BED_TO_BIGBED = os.path.join(BINARIES,"bedToBigBed")
HG_LOAD_CHAIN = os.path.join(BINARIES, "hgLoadChain")
BIG_CHAIN = os.path.join(BINARIES,"bigChain.as")
BIG_LINK = os.path.join(BINARIES,"bigLink.as")
LINK_TAB = os.path.join(TEMP_DIR, "link.tab")

LOAD_CHAIN_ARGS = "-noBin -test"
LOAD_CHAIN_GENOME = "hg38"
LOAD_CHAIN_FORMAT = "bigChain"

BIG_BED_TYPE_SIX  = "-type=bed6+6"
BIG_BED_TYPE_FOUR = "-type=bed4+1"
BIG_BED_OUTPUT = "bigChain.bb"
BIG_LINK_OUTPUT = "bigChain.bigLink"
BIG_CHAIN_OUTPUT = "bigChain.link.bb"

SINGLE = "single"
MULTIPLE = "multiple"
UNCOMPRESSED = "uncompressed"
COMPRESSED = "compressed"
SUCCESS = "success"
FAILURE = "failure"

VBOX = "VBoxManage"
VERSION = "--version"
VBOX_ARGS = "list vms"
UCSC_GBIB = "https://genome.ucsc.edu/goldenpath/help/gbib.html"
HTTPS_VBOX = "https://www.virtualbox.org/wiki/Downloads"
BIG_DATA_URL = "bigDataUrl="
LINK_DATA_URL = "linkDataUrl="
TRACK_TYPE = "track type=bigChain"
LOCALHOST = "http://127.0.0.1:1234/folders"
SHARED_FOLDER = "sf_Documents" #Assuming its Documents



class Chain:
    """Chainify manager class."""
    def __init__(self, args):
        self.dependencies = self.__install_dependencies()
        if self.dependencies:
            self.die(
                "Dependencies could not be installed. "
                "Please check the error message or contact the developers at: {GITHUB}."
                    )
        else:
            self.__check_args(args)
            if self.__check_chrom_sizes(args) == SUCCESS:
                self.__get_temp_dir()
        
        print("\n")
        print("#### Chainify initiated successfully! ####")
        print("\n")        
        

    def die(self, msg, rc=1):
        """Print error message and exit."""
        print(msg)
        print(f"Program terminated with exit code {rc}.")
        sys.exit(rc)



    def __install_dependencies(self):
        """Install dependencies."""
        dp.main()



    def __get_temp_dir(self):
        """Create temp directory if it does not exist."""
        if not os.path.isdir(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)
            print(f"temp files are at {TEMP_DIR}.")
        else:
            print(f"{TEMP_DIR} already exists, sending temp files there...")



    def __check_args(self, args):
        """Check whether the arguments are correct."""
        print("#### Checking arguments... ####")
        if not os.path.isfile(args.chain):
            self.die(f"Chain file {args.chain} does not exist.")

        if not os.path.isfile(args.sizes):
            self.die(f"Chain file {args.sizes} does not exist.")

        if args.shared_folder:
            if not os.path.isdir(args.shared_folder):
                self.die(f"{args.shared_folder} does not exist.")

        if args.chain:
            chain_attributes = args.chain.split(".")
            if any(x == "chain" for x in chain_attributes):
                print("Chain file: OK")
        
        if args.sizes:
            chrom_sizes = args.sizes.split(".")
            if any(x == "chrom" for x in chrom_sizes):
                print("Chromosome sizes file: OK")

        if args.gene:
            gene_list = args.gene.split(",")
            if len(gene_list) > 1:
                print(f"{len(gene_list)} genes provided"
                    f"Genes provided: {gene_list}")
                return MULTIPLE
            elif len(gene_list) == 1:
                print(f"Gene provided: {gene_list}")
                return SINGLE
            else:
                self.die("No genes provided.")

        return 
    
    

    def __check_chain_file(self, args):
        """Check whether the chain file is compressed."""
        if args.chain:
            chain_attributes = args.chain.split(".")
            if any(x == "gz" for x in chain_attributes):
                print("Chain file is compressed")
                return COMPRESSED
            else:
                return UNCOMPRESSED
    


    def __check_chrom_sizes(self, args):
        """Check whether the chromosome sizes file is compressed."""
        if args.sizes:
            chrom_sizes = args.sizes.split(".")
            if any(x == "gz" for x in chrom_sizes):
                print("Chromosome sizes file is compressed")
                with gzip.open(args.sizes, "r") as sizes:
                    line = sizes.readline().strip().split("\t")
                    if len(line) == CHROM_SIZES_COLS and line[1].isdigit():
                        print("Chromosome sizes file is in the correct format")
                        return SUCCESS
                    else:
                        error_msg = ("Chromosome sizes file is not in the correct format"
                                    "The file should have two columns: chromosome and size"
                                    "Example: chr1 248956422")
                        self.die(error_msg)
            else:
                print("Checking chromosome sizes file...")
                with open(args.sizes, "r") as sizes:
                    line = sizes.readline().strip().split("\t")
                    if len(line) == CHROM_SIZES_COLS and line[1].isdigit():
                        print("Chromosome sizes file is in the correct format")
                        return SUCCESS
                    else:
                        error_msg = ("Chromosome sizes file is not in the correct format"
                                    "The file should have two columns: chromosome and size"
                                    "Example: chr1 248956422")
                        self.die(error_msg)



    def run_cmd(self, command):
        """Run command and return stdout."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout
            


    def _make_chain_from_gene(self, args):
        """Make chain file from gene."""
        if args.gene:
            if self.__check_args(args) != MULTIPLE:
                f = open(os.path.join(TEMP_DIR, f"{args.gene}.chain"), "w")
                chain_id = args.gene.split(".")[1]
                awk_inner = f'$NF == "{chain_id}" {{print $1, $2, $3}}'
                awk_metadata = f'$NF == "{chain_id}" {{print $0}}'
                chain_metadata = self.run_cmd(f'zgrep -w "{chain_id}" {args.chain} | awk \'{awk_metadata}\'').strip()
                print(f"Looking for chain {chain_id}...")

                if self.__check_chain_file(args) == COMPRESSED:
                    awk_rs = self.run_cmd(f'zgrep -w "{chain_id}" {args.chain} | awk \'{awk_inner}\'').strip()
                    cmd = f'zcat {args.chain} | awk \'/^{awk_rs}/{{extract=1; next}} /^chain/{{extract=0}} extract\''
                    chain_coordinates = self.run_cmd(cmd)
                else:
                    awk_rs = self.run_cmd(f'grep -w "{chain_id}" {args.chain} | awk \'{awk_inner}\'').strip()
                    cmd = f'cat {args.chain} | awk \'/^{awk_rs}/{{extract=1; next}} /^chain/{{extract=0}} extract\''
                    chain_coordinates = self.run_cmd(cmd)

                print("Creating new gene chain file...")
                f.write(chain_metadata + "\n" + chain_coordinates)
                print("Gene chain file created successfully.")

                return SUCCESS



    def hg_load_chain(self, args):
        """Make bigChain file from chain file."""
        print("making bigChain file from the main chain file...")
        file = os.path.join(TEMP_DIR, f"{args.gene}.chain")
        cmd = f"{HG_LOAD_CHAIN} {LOAD_CHAIN_ARGS} {LOAD_CHAIN_GENOME} {LOAD_CHAIN_FORMAT} {file}"
        rs = self.run_cmd(cmd)

        chain = open("chain.tab", "r")
        big_chain = open("chain.bigChain", "w")
        
        for line in chain:
            re.sub(r'\.000000', "", line)
            line = line.strip().split()
            new_line = [
                line[1], line[3], line[4], line[10], '1000',
                line[7], line[2], line[5], line[6], line[8], line[9], line[0]
            ]
            big_chain.write("\t".join(new_line) + "\n")

        shutil.move("chain.tab", TEMP_DIR)
        shutil.move("link.tab", TEMP_DIR)
        shutil.move("chain.bigChain", TEMP_DIR)

        print("bigChain file created successfully.")
        return SUCCESS



    def bed_to_bigbed(self, args):
        """Make bigBed and bigBedLink file from bigChain file."""
        print("making the bigBed file from the bigChain file...")
        cmd = f"{BED_TO_BIGBED} {BIG_BED_TYPE_SIX} -as={BIG_CHAIN} -tab {TEMP_DIR}/chain.bigChain {args.sizes} {TEMP_DIR}/{BIG_BED_OUTPUT}"
        rs = self.run_cmd(cmd)

        f = open(LINK_TAB, "r")
        o = open(BIG_LINK_OUTPUT, "w")
        link_list = []
        for line in f:
            fields = line.strip().split()
            link_list.append('\t'.join([fields[0], fields[1], fields[2], fields[4], fields[3]]))
        
        link_sorted = sorted(link_list, key=lambda x: (x.split('\t')[0], int(x.split('\t')[1])))
        o.write("\n".join(link_sorted))
        shutil.move(BIG_LINK_OUTPUT, TEMP_DIR)
        print("bigLink file created successfully.")

        print("making the bigBedLink file from the bigChain file...")
        cmd = f"{BED_TO_BIGBED} {BIG_BED_TYPE_FOUR} -as={BIG_LINK} -tab {TEMP_DIR}/chain.bigChain {args.sizes} {TEMP_DIR}/{BIG_CHAIN_OUTPUT}"
        rs = self.run_cmd(cmd)
        print("bigBedLink file created successfully.")

        return



    def _check_gbib(self):
        """Check whether GBiB is installed."""
        try: 
            subprocess.check_output([VBOX, VERSION])
            print("VirtualBox is installed")
            cmd = f"{VBOX} {VBOX_ARGS}"
            rs = self.run_cmd(cmd)
            if any(x == "browserbox" for x in rs.strip().split('"')):
                print("Genome Browser in a Box (GBiB) is installed")
                return SUCCESS
            else:
                print("Genome Browser in a Box (GBiB) is not installed. "
                    f"Please visit {UCSC_GBIB} for more information")
                return FAILURE
        except FileNotFoundError:
            print("VirtualBox is not installed. "
                f"Please visit {HTTPS_VBOX} for more information")
            return FAILURE
        
                
    def run(self, args):
        f = open(os.path.join(TEMP_DIR, OUT), "w")
        if self._make_chain_from_gene(args) == SUCCESS:
            if self.hg_load_chain(args):
                self.bed_to_bigbed(args)
                self._check_gbib()
                if args.shared_folder:
                    path = "/".join([LOCALHOST, SHARED_FOLDER])
                    link = f"{TRACK_TYPE} {BIG_DATA_URL}{os.path.join(path, BIG_BED_OUTPUT)} {LINK_DATA_URL} {os.path.join(path, BIG_CHAIN_OUTPUT)}"
                    f.write(link)
                    print("Chainify finished successfully."
                        f"Results are available at: {os.path.join(TEMP_DIR, OUT)}")
                else:
                    path = "/".join([LOCALHOST, SHARED_FOLDER])
                    link = f"{TRACK_TYPE} {BIG_DATA_URL}{os.path.join(path, BIG_BED_OUTPUT)} {LINK_DATA_URL} {os.path.join(path, BIG_CHAIN_OUTPUT)}"
                    f.write(link)
                    print("### Chainify finished successfully. ###")
                    print(f"Results are available at: {os.path.join(TEMP_DIR, OUT)}")



def parse_args():
    app = argparse.ArgumentParser()
    app.add_argument(
        "-c",
        "--chain", 
        help="Chain file"
        ". *.chain or *.chain.gz are accepted", 
        required=True,
        type=str
        )
    app.add_argument(
        "-s", 
        "--sizes", 
        help="Chromosome sizes file"
        ". Should have two columns: chromosome and size", 
        required=True,
        type=str
        )
    app.add_argument(
        "-g", 
        "--gene", 
        help="Gene name(s) (comma-separated)", 
        required=True,
        type=str
        )
    app.add_argument(
        "-sf",
        "--shared_folder",
        help="Shared folder name used by the VM",
        required=False,
        type=str
    )

    if len(sys.argv) < 2:
        app.print_help()
        sys.exit(0)
    args = app.parse_args()

    return args



def main():
    args = parse_args()
    chainify = Chain(args)
    chainify.run(args)


if __name__ == "__main__":
    main()