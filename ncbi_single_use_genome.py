#! /usr/bin/env -S python3 -u
import os, shutil, sys, glob, traceback
from easyterm import * 

help_msg="""This program downloads one specific NCBI assembly, executes certains operations, then cleans up data

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
-h | --help  print this help and exit"""

command_line_synonyms={'t':'temp'}
def_opt= {'a':'',
          'o':'./',
          'c':'',
          'cf':'',
          'p':'',
          'pf':'',
          'k':False,
          'sh':False,
          'w':1,
          'temp':'/tmp/'}

temp_folder=None

##### start main program function
def main(args={}):
  """We're encapsulating nearly the whole program in a function which is executed when 
  the script is directly executed. This provides the alternative of being able 
  to run the same thing as module: importing this 'main' function and running it with 
  a 'args' dictionary containing options and arguments, equivalent to opt
  """
  
  ### loading options
  if not args:
    opt=command_line_options(def_opt, help_msg, synonyms=command_line_synonyms)
  else:   
    opt=args

  # if not opt['cf'] and not opt['c']:
  #   raise NoTracebackError("ERROR you must define a template command with -c or -cf")
  if opt['c'] or opt['cf']:                         
    bash_template_command=(opt['c']
                           if opt['c'] else
                           '\n'.join([x.strip() for x in open(opt['cf'])]))
  if opt['p'] or opt['pf']:
    py_template_command=(opt['p']
                         if opt['p'] else
                         '\n'.join([x.strip() for x in open(opt['pf'])]))    
    
  if not opt['o']:
    raise NoTracebackError("ERROR you must provide an output folder with -o")
  outfolder=opt['o'].rstrip('/')
  if not os.path.exists(outfolder):
    os.makedirs(outfolder)
  
  if not opt['a']:
    raise NoTracebackError("ERROR you must provide an accession with -a")
  accession=opt['a']

  datadir=f'{outfolder}/dataset.{accession}'
  zipfile=datadir+'.zip'

  write('*** Options accepted: ', how='green')
  write(opt)
  write('')
  
  write('*** Download metadata (dehydrated)', how='green')
  ## download dehydrated
  cmd_download_dehydra = f"""\
datasets download genome accession {accession} \
--reference --dehydrated \
--exclude-genomic-cds --exclude-gff3 --exclude-protein --exclude-rna \
--filename {zipfile} """
  run_cmd(cmd_download_dehydra,
          stdout=None, stderr=None) # messages printed to screen

  write('*** Reformatting metadata', how='green')  
  ## get some metadata
  cmd_format_tsv = f"""
dataformat tsv genome \
--package {zipfile} \
--fields tax-id,organism-name"""
  x = run_cmd(cmd_format_tsv).stdout 
  taxid, species = x.split('\n')[1].split('\t')
  mspecies=mask_chars(species)
  write(f'accession: {accession}')
  write(f'taxid:     {taxid}')
  write(f'species:   {species}')
  write(f'mspecies:  {mspecies}')  

  write('*** Unzipping metadata, removing zipfile', how='green')    
  ## prep for download: unzip
  cmd_unzip_dehydra=f"unzip -o -d {datadir} {zipfile}"
  run_cmd(cmd_unzip_dehydra,
          stdout=None, stderr=None) # messages printed to screen
  write(f'removing {zipfile}')
  os.remove(zipfile)
  
  write('')
  write('*** Downloading genome data', how='green')    
  ## download / hydrate
  progressbar=''  if sys.stdout.isatty() else ' --no-progressbar '
  cmd_download_hydra=f"""
datasets rehydrate \
--directory {datadir} \
--match "/{accession}/" \
--max-workers {opt['w']} \
{progressbar} """
  run_cmd(cmd_download_hydra,
          stdout=None, stderr=None) # messages printed to screen

  write('')
  write('*** Compacting chromosomes into a single fasta', how='green')
  fasta_regexp=f'{datadir}/ncbi_dataset/data/{accession}/*fna'
  genomefile=  f'{datadir}/ncbi_dataset/data/{accession}/{accession}.fasta'
  index=0
  with open(genomefile, 'wb') as wfd:
    for index, chromfile in enumerate(glob.iglob(fasta_regexp)):
      service(chromfile)
      with open(chromfile,'rb') as fd:
        shutil.copyfileobj(fd, wfd)  
  # cmd_compact_fasta=f'cat {fasta_regexp} > {genomefile}'
  # run_cmd(cmd_compact_fasta)
  write(f'Concatenating {index+1} chromosomes or contigs \n to genomefile: {genomefile}')
  
  write('*** Removing chromosomes fasta files', how='green')
  for chromfile in glob.iglob(fasta_regexp):
    os.remove(chromfile)

  if not any( [opt[k] for k in ['c', 'p', 'cf', 'pf']] ):
    write('')
    write('*** <No commands to be executed>', how='green')
  try:
    if opt['c'] or opt['cf']:
      write('')    
      write('*** Running bash command', how='green')
      #template='{genomefile} {species} {mspecies}'
      bash_cmd=bash_template_command.format(**locals())
      write(bash_cmd)
      run_cmd(bash_cmd,
              shell=opt['sh'],
              stdout=None, stderr=None) # messages printed to screen, if not redicted

    if opt['p'] or opt['pf']:
      write('')    
      write('*** Running python command', how='green')
      py_cmd=py_template_command.format(**locals()) 
      write(py_cmd)
      exec(py_cmd)
      
  except Exception:
    write('')
    write('*** an ERROR occured !', how='red') 
    traceback.print_exc()    

  if not opt['k']:
    write('')
    write('*** Cleaning up all data', how='green')
    write(f'removing {datadir}')
    shutil.rmtree(datadir)    
  else:
    write('')
    write('*** Leaving data in place', how='green')
    write(f'check {datadir}')
    

  
  # creating a temporary folder with random name inside the -temp argument
  # temp_folder=random_folder(opt['temp'])
  # write(f'Using temporary folder={temp_folder}')
  
  ### insert your code here



##### end main program function

### function executed when program execution is over:
def close_program():
  pass
  # if temp_folder is not None and os.path.isdir(temp_folder):
  #   # deleting temporary folder
  #   shutil.rmtree(temp_folder)

if __name__ == "__main__":
  try:
    main()
    close_program()  
  except Exception as e:
    close_program()
    raise e from None
