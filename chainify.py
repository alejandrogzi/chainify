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
BINARIES = os.path.join(LOCATION, MODULES, BIN)
TEMP_DIR = os.path.join(LOCATION, MODULES, TEMP)
GITHUB = "https://github.com/alejandrogzi/chainify.git"
RESULTS = os.path.join(LOCATION,"results")
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
GENE = "gene"
GENOME = "genome"
CHROMOSOME = "chromosome"

VBOX = "VBoxManage"
VERSION = "--version"
VBOX_ARGS = "list vms"
UCSC_GBIB = "https://genome.ucsc.edu/goldenpath/help/gbib.html"
HTTPS_VBOX = "https://www.virtualbox.org/wiki/Downloads"
BIG_DATA_URL = "bigDataUrl="
LINK_DATA_URL = "linkDataUrl="
TRACK_TYPE = "track type=bigChain"
LOCALHOST = "http://127.0.0.1:1234/folders"
SHARED_FOLDER = "Documents" #Assuming its Documents



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
                print(f"{len(gene_list)} genes provided.")
                print(f"Genes provided: {gene_list}")
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



    def get_chain_coordinates(self, args, chain_id):
            """Looks for a chain_id in the chain file and return its metadata and coordinates"""
            if self.__check_chain_file(args) == COMPRESSED:
                grep = "zgrep"
                cat = "zcat"
            else:
                grep = "grep"
                cat = "cat"

            awk_metadata = f'$NF == "{chain_id}" {{print $0}}'
            metadata = self.run_cmd(f'{grep} -w "{chain_id}" {args.chain} | awk \'{awk_metadata}\'').strip()
            chain_metadata =''.join([k for k in metadata.split("\n") if k.startswith("chain")])
            
            print(f"Looking for chain {chain_id}...")

            #awk_inner = f'$NF == "{" ".join(chain_metadata.split(" ")[:4])}" {{print $1, $2, $3}}'
            #awk_rs = self.run_cmd(f'{grep} -w "{" ".join(chain_metadata.split(" ")[:4])}" {args.chain} | awk \'{awk_inner}\'').strip()
            cmd = f'{cat} {args.chain} | awk \'/^{" ".join(chain_metadata.split(" ")[:4])}/{{extract=1; next}} /^chain/{{extract=0}} extract\''
            chain_coordinates = self.run_cmd(cmd)

            return (chain_metadata, chain_coordinates)



    def _make_chain_from_gene(self, args):
        """Make chain file from gene."""
        if args.gene:
            if self.__check_args(args) != MULTIPLE:
                f = open(os.path.join(TEMP_DIR, f"{args.gene}.temp.chain"), "w")
                chain_id = args.gene.split(".")[1]
                k,v = self.get_chain_coordinates(args, chain_id)
                f.write(k + "\n" + v)
                print("Gene chain file created successfully.")

            else:
                m = open(os.path.join(TEMP_DIR, "genes.temp.chain"), "w")
                genes = args.gene.split(",")
                for gn in genes:
                    chain_id = gn.split(".")[1]
                    k,v = self.get_chain_coordinates(args, chain_id)
                    m.write(k + "\n" + v.rstrip() + "\n")
                print("Gene chain file created successfully.")
                    
            return SUCCESS



    def hg_load_chain(self, args):
        """Make bigChain file from chain file."""
        print("making bigChain file from the main chain file...")
        if args.mode == GENE:
            if self.__check_args(args) != MULTIPLE:
                file = os.path.join(TEMP_DIR, f"{args.gene}.temp.chain")
            else:
                file = os.path.join(TEMP_DIR, "genes.temp.chain")
        else:
            if self.__check_chain_file(args) == COMPRESSED:
                cmd = f"zcat {args.chain} > {os.path.join(TEMP_DIR, str(args.chain).split('.gz')[0])}"
                self.run_cmd(cmd)
                file = os.path.join(TEMP_DIR, str(args.chain).split('.gz')[0])
            else:
                file = args.chain

        if args.mode != GENE:
            query_chain = open(file, "r")
            chr_file = self.make_chromosome_chain(args, query_chain)
            cmd = f"{HG_LOAD_CHAIN} {LOAD_CHAIN_ARGS} {LOAD_CHAIN_GENOME} {LOAD_CHAIN_FORMAT} {chr_file}"

        rs = self.run_cmd(cmd)

        chain = open("chain.tab", "r")
        big_chain = open("chain.bigChain", "w")
        
        for line in chain:
            line = re.sub(r'\.000000', "", line).strip().split()
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
        rs = subprocess.Popen(cmd, shell=True)
        rs.wait()

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
        cmd = f"{BED_TO_BIGBED} {BIG_BED_TYPE_FOUR} -as={BIG_LINK} -tab {os.path.join(TEMP_DIR,BIG_LINK_OUTPUT)} {args.sizes} {os.path.join(TEMP_DIR,BIG_CHAIN_OUTPUT)}"
        rs = subprocess.Popen(cmd, shell=True)
        rs.wait()
        print("bigBedLink file created successfully.")

        return



    def mode(self, args):
        """Check whether the mode is specified or is gene or genome."""
        if not args.mode:
            return GENE
        else:
            if args.mode not in [GENE, GENOME, CHROMOSOME]:
                self.die("Mode not recognized. Please use gene or genome.")
            elif args.mode == GENOME:
                return GENOME
            elif args.mode == CHROMOSOME:
                return CHROMOSOME
            else:
                return GENE



    def make_chromosome_chain(self, args, file):
        """ Make chain file for a given chromosome """  
        if args.chromosome:
            print(f"Extracting alignments from {args.chromosome}...")
            name = args.chromosome
        else:
            print(f"Filtering negative chain scores from {args.chain}...")
            name = f"{args.chain.split('.chain')[0]}_noneg"
        chain_dict = {}
        current_chain = None
        chr_chain = open(f"{TEMP_DIR}/{name}.chain", "w")

        for line in file:
            if line.startswith("chain"):
                current_chain = line.strip()
                if int(current_chain.split(" ")[1]) > 0:
                    chain_dict[current_chain] = []
                else:
                    current_chain = None
            else:
                if current_chain:
                    chain_dict[current_chain].append(line.strip())

    
        for k,v in chain_dict.items():
            if args.chromosome:
                if k.split(" ")[2] == args.chromosome:
                    chr_chain.write(k + "\n" + "\n".join(v) + "\n")
            else:
                chr_chain.write(k + "\n" + "\n".join(v) + "\n")

        chr_chain.close()
        #name = os.path.join(TEMP_DIR, chr_chain.name)
        return chr_chain.name



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



    def clean_up(self, args):
        """ Deletes all intermediate files """
        if not args.clean:
            shutil.rmtree(TEMP_DIR)
            print("Cleaning all temp files...")
            return SUCCESS
        else:
            return None



    def make_link(self, args):
            """ Builds the input link to Genome Browser """
            if not os.path.isdir(RESULTS):
                os.makedirs(RESULTS, exist_ok=True)

            f = open(os.path.join(RESULTS, OUT), "w")
            if not args.shared_folder:
                sf = "_".join(["sf", SHARED_FOLDER])
                path = "/".join([LOCALHOST, sf])
            else:
                sf = "_".join(["sf", args.shared_folder])
                path = "/".join([LOCALHOST, SHARED_FOLDER])
            
            link = f"{TRACK_TYPE} {BIG_DATA_URL}{os.path.join(path, BIG_BED_OUTPUT)} {LINK_DATA_URL}{os.path.join(path, BIG_CHAIN_OUTPUT)}"   

            if args.name:
                name = f" name={args.name}"
                link += name

            if args.description:
                desc = f" description={args.description}"
                link += desc

            f.write(link)
            return SUCCESS



    def run(self, args):
        f = open(os.path.join(TEMP_DIR, OUT), "w")
        if self.mode(args) == GENE:
            if self._make_chain_from_gene(args) == SUCCESS:
                if self.hg_load_chain(args):
                    self.bed_to_bigbed(args)
                    self._check_gbib()
        else:
            self.hg_load_chain(args)
            self.bed_to_bigbed(args)
            self._check_gbib()


        self.make_link(args)
        shutil.move(os.path.join(TEMP_DIR, BIG_BED_OUTPUT), os.path.join(os.path.expanduser('~'), SHARED_FOLDER))
        shutil.move(os.path.join(TEMP_DIR, BIG_CHAIN_OUTPUT), os.path.join(os.path.expanduser('~'), SHARED_FOLDER))
        self.clean_up(args)

        print("### Chainify finished successfully. ###")
        print(f"Results are available at: {os.path.join(RESULTS, OUT)}")



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
        required=False,
        type=str
        )
    app.add_argument(
        "-sf",
        "--shared_folder",
        help="Shared folder name used by the VM",
        required=False,
        type=str
    )
    app.add_argument(
        "-cl",
        "--clean",
        help="Clean all the temp files from path",
        default=False,
        required=False,
        type=str
    )
    app.add_argument(
        "-n",
        "--name",
        help="Name of the track",
        required=False,
        type=str
    )
    app.add_argument(
        "-d",
        "--description",
        help="Description of the track",
        required=False,
        type=str
    )
    app.add_argument(
        "-m",
        "--mode",
        help="Chanify mode: gene or whole genome",
        required=False,
        type=str
    )
    app.add_argument(
        "-chr",
        "--chromosome",
        help="Chromosome name",
        required=False,
        type=str
    )

    if len(sys.argv) < 2:
        app.print_help()
        sys.exit(0)

    args = app.parse_args()

    if args.mode == CHROMOSOME and not args.chromosome:
        error_msg = ("Chromosome not provided. Please provide a chromosome.")
        sys.exit(error_msg)

    return args



def main():
    args = parse_args()
    chainify = Chain(args)
    chainify.run(args)


if __name__ == "__main__":
    main()