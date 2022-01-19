# ncbi_single_use_genome
Download a NCBI genome, process it with your own code, then trash it 

This script is instrumental to analyze as many NCBI genomes as you want, without having to allocate the storage space for them.
In a single run ncbi_single_use_genome will download a genome, process it according to options, then trash it

Requirements:
-------------
  - datasets and dataformat by NCBI (see https://www.ncbi.nlm.nih.gov/datasets/); version tested: 12.24.0
  - easyterm (see https://easyterm.readthedocs.io/)

Help message / usage:
---------------------
(run 'ncbi_single_use_genome.py -h' to inspect at any time)

This program downloads one specific NCBI assembly, executes certains operations, then cleans up data

### Input/Output:
-a     genome NCBI accession
-o     folder to download to

### Actions:
-c     bash command template
-cf    bash command template read from this file
-p     python command template
-pf    python command template read from this file

In all templates above, these placeholders can be used:
{accession}   genome NCBI accession, e.g. GCA_000209535.1
{genomefile}  path to genome fasta file
{taxid}       taxonomy id
{species}     species name, e.g. "Drosophila melanogaster"
{mspecies}    masked species, e.g. "Drosophila_melanogaster"

### Other options:
-k      keep files instead of cleaning them up at the end
-w      max workers for downloads at once
-sh     open shells for bash commands. Required for complex commands
        (e.g. sequential commands, or using redirections)

-print_opt   print currently active options
-h | --help  print this help and exit
