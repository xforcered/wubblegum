# wubblegum

Wubblegum is a smart card reconnaissance tool that works at the APDU level, without the need to understand and follow the higher level specification a card may follow such as EMV or GlobalPlatform.

WARNING: Wubblegum is still experimental and will need much wider testing on a variety of smart cards. If you do encounter any issues not addressed by the README, it would be very helpful to the future of this project to make an issue on GitHub. It may damage or brick your smart card, or make disparaging comments about your dog's face. 

## Installation
To install wubblegum, clone this repo and install the dependencies.

### Pre-requisites
wubblegum depends on uttlv and pyscard. You will also need Python3.6 or later.

To install these dependencies:
```sh
python3 -m pip install uttlv
python3 -m pip install pyscard
```

## Usage
wubblegum is a command line tool. To understand the usage of wubblegum and its options, run `python3 ./wubblegum.py --help` or read on.

### Selecting a card reader
You should check using `--show-readers` to see if there is more than one card reader recognized on your system. Some devices like Yubikeys are recognized as card readers. If you need to select a reader that isn't the first in the list (index 0) you can use `-r x` where x is the index of the reader you wish to use, as listed by `--show-readers`.

### Enumerating a card
The main option you'll want to use is `--enumerate`. It takes several options at once, separated by spaces. These options are:
```
Enumerate...
c - Application class (CLA) values
fi - Files by two-byte identifier
fp - Files by path
fn - Files by filename
i - Instruction (INS) values
d - Data
```

### CLA enumeration
Smart cards have different sets of commands they support based on the CLA value. The error messages returned can vary greatly from card to card, so Wubblegum asks the user to manually prune responses, grouping responses by the particular response code returned.

In general, if a card returns an error indicating that the CLA / application class is invalid, those responses should be deleted before continuing. Other responses that usually should be pruned include a response that the logical channel being selected is not supported. Often, there are far more unusable CLA values than usable ones, so it's often productive to delete the most common responses. Getting the right values may take some trial and error.

If you want to manually specify CLA values, you can do so with the `-c` option. It supports multiple CLAs, specified as space-separated hex values, like so:

`-c 00 80 ff`

### File enumeration options
Once you have valid CLA values, most cards will require you select a file before most commands will be enabled, and selection of different files will often enable different sets of commands. Different smart cards will require different methods of file selection.

#### DF name
Several options are available for DF name enumeration. If you would like to brute force names by wordlist, you can specify one using the `-w` or `--wordlist` switch. A wordlist should be a newline separated file of hex encoded filenames. A file of publicly known registered identifiers, `rid_list.txt`, is included with this tool.

Many cards will support selection by partial file name. Some of them require a minimum length for partial file names. You can provide a hex-encoded prefix for all candidate filenames with `-p` or `--filename-prefix`. You can also choose how many bytes are used in brute force attempts (since many cards will expect a minimum number of bytes) using `-l` or `--filename-brute-length`. By default, no prefix will be used, and only one byte filenames will be attempted, though Wubblegum will also attempt to enumerate full filenames one byte at a time upon any successful filename guess.

#### File ID
To brute force by file identifier, use `--enumerate fi`.

#### File Path
To brute force by path, use `--enumerate fp`.

#### Manually specifying files
If you would like to manually specify files, you can use `--files` to provide hex encoded file names or identifiers, and use `--filetype` followed by one of the following options (default is by name):
```
id - File Identifier
path - File Path
name - File Name
```

### INS Enumeration
To enumerate INS values, use `--enumerate i`. By default, Wubblegum will use a blocklist to prevent running commands that may delete files, delete data, or render the card non-operational. If you really want to try these INS values anyway, use `--no-ins-blocklist`.

Sometimes there will be many combinations of discovered CLA values and files, making the process of manually pruning INS probe responses a tedious task. To assume that the correct error code will be returned for any unsupported INS value and automatically prune only those responses, use `--ins-auto-prune`.


### Data enumeration
To enumerate valid record identifiers / EF identifiers / tags and use them to extract data from the card when a file is found to support data-reading commands, use `--enumerate d`.


### Example
To enumerate CLA, Files by name using the included RID wordlist, INS with autoprune, and card data from the first card reader in verbose mode:
`python3 ./wubblegum.py --enumerate c fn i d --wordlist rid_list.txt --ins-auto-prune -v`
