# Chainify

**Chainify** is a solution for generating pairwise genome alignment chain plots using UCSC's Genome Browser in a Box (GBiB). This tool can be used to create ready-to-plot alignments for specific genes or gene lists.

## Usage

To use Chainify, just make:

```
git clone https://github.com/alejandrogzi/chainify.git
# to download necessary binaries
cd modules
./dependencies.py
# or just run with required arguments (automates binary installation)
./chainify.py
```

## Input files:
Chainify is a tool that automates the converting process of a genome aligment chain in a graphic format recognized by the UCSC Genome Browser. It utilizes the Genome Browser in a Box - a small virtualized version of UCSC Genome Browser that runs locally - making it easier for people that does not have the possibility to host their files in a server/cloud/etc. The input files needed to run chainify are:

```
usage: chainify.py [-h] -c CHAIN -s SIZES -g GENE [-sf SHARED_FOLDER]

  -h, --help            show this help message and exit
  -c CHAIN, --chain CHAIN
                        Chain file. *.chain or *.chain.gz are accepted
  -s SIZES, --sizes SIZES
                        Chromosome sizes file. Should have two columns: chromosome and size
  -g GENE, --gene GENE  Gene name(s) (comma-separated)
  -sf SHARED_FOLDER, --shared_folder SHARED_FOLDER
                        Shared folder name used by the VM
```

where:

1. The chain file should have a '.chain' extension and could (or not) be .gz compressed.

`zcat example.chain.gz`

```
chain 2755244274 chrX 154259566 + 112383 154241906 chrX 127069619 + 28712 126971188 1
29      1       0
61      3       0
78      22      0
8       42      0
43      0       1
```

2. The chromosome sizes file could be in any text format (.txt, .tsv, ...), including the .2bit output format name '.chrom.sizes'. Regarding any of the extensions, your file must have the word '.chrom.' in the name.

`cat example.chrom.sizes`

3. This file should have only two columns: chromosome-name \t size; where the first column has the chromosome names and the second one the chromosome lengths (in bp).

```
chr1    123313939
chr2    86187811
chr3    92870237
chr4    89007665
chr5    89573405
```
4. Gene names can be specified directly as an argument by just typing them as comma-separated values (if working with multiple genes).

   **Note that when I talk about 'gene names' I refer to Ensembl IDs (e.g. ENST00000373688.209092) only.** As chainify is a tool that facilitates the processing of alignment chains, gene names must be accompanied by their chain projection (joined by '.'), just like the example. Chainify uses the chain ID to look through the '.chain' file and find the desired chain to convert.

### Example:

`./chainify.py -c ${chain} -s ${chrom_sizes} -g ${gene}`

Chainify assumes that GBiB running locally has '~/Documents' as the shared folder and will direct the output constructor using that shared folder as a part of the path. During the GBiB installation process you can choose any folder of your convenience. The path to that folder should be specified with -sf. 

`./chainify.py -c ${chain} -s ${chrom_sizes} -g ${gene} -sf ~/Downloads`

## Output:

This chainifier saves the results as a .txt file named "out" located within `~/chainify/temp/modules`. The output file stores the track type, urls directing to the chain linked converted files and optionally a name, description provided by the user.

`track type=bigChain bidDataUrl=/path/to/bigChain.bb linkDataUrl= /path/to/bigChain.link.bb description="An example" name="Test chain"`

As GBiB allows the usage of local files, only open the localhost to Genome Browser and paste the information provided by chainify! 

## License

This project is licensed under the [MIT License](LICENSE).
