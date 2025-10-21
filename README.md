# wubblegum

Wubblegum is a smart card reconnaissance tool that works at the APDU level, without the need to understand and follow the higher level specification a card may follow such as EMV or GlobalPlatform.

WARNING: Wubblegum is still experimental and will need much wider testing on a variety of smart cards. If you do encounter any issues not addressed by the README, it would be very helpful to the future of this project to make an issue on GitHub. It may damage or brick your smart card, or make disparaging comments about your dog's face. 

## Installation
To install wubblegum, clone this repo and install the dependencies.

### Pre-requisites
wubblegum depends on `pyscard` for low level smartcard functionality and `ishell` for the interactive shell provided by the APDU console. You will also need Python3.6 or later.

To install these dependencies:
```sh
pip install -r requirements.txt
```

## Card reader support
wubblegum's card reader support is provided by `pyscard`, which should work with a card reader that states it is PCSC or CCID compatible.

## Suggested card readers

### Budget
For those who want to start hacking smart cards with as little money spent as possible, the UTHAI X02 USB SIM Smart Card Reader is confirmed to work with wubblegum and can be found on AliExpress for as little as $1USD.
https://www.aliexpress.us/item/2255799890621602.html

### Support and accountability
If you have technical issues with a $1USD card reader, it's likely you are completely on your own. There are also questions of whether $1 readers from AliExpress can be trusted not to be preloaded with malware, given this has actually been an attack vector in the past. Here's some more options confirmed to work from the well known company HID:

#### Contact-only reader
If you only want or need to read contact cards:
HID Omnikey 3021
https://www.officesupply.com/technology/peripherals-memory/memory-adapters/memory-readers/omnikey-3021-reader/p961615.html?request_type=mlt

#### Contactless & contact reader
If you would like to have a reader capable of reading both contact and high frequency contactless cards (which are more likely to be interesting and not just spit out a hard coded ID number):
HID Omnikey 5422
https://www.officesupply.com/dual-interface-contact-contactless-smart-card-reader/p1242160.html

#### SIM to IC card adapter
If you have SIM cards you'd like to read, this allows you to insert them into a card reader that accepts a wallet-sized smart card:
XCRFID SIM to IC Card adapter
https://www.amazon.com/Pinboard-Adapter-Converter-ISO7816-XCRFID/dp/B0748C839G/

## Smart card structure
Smart cards are organized according to a filesystem that differs a little bit from the way most filesystems work. In addition to being able to contain data:
* They are hierarchical, but do not necessarily have a root node that is above all other nodes hierarchically. If there is such a node, it is known as the MF, or Master File.
* Every file can also be like a directory, that is, each file can have child nodes, and those children can have children, and so on.
* Every file can also be an application: after selecting a given file, certain commands may be enabled or disabled, or may begin to work differently.

Commands are issued to a smart card by the terminal (aka "card reader") to which it is connected. These commands take the form of an APDU (application protocol data unit).

An APDU looks like this:

```
+---+---+--+--+--+------+--+
|CLA|INS|P1|P2|Lc| Data |Le|
+---+---+--+--+--+------+--+
| 00| A4|04|00|03|414243|--|
+---+---+--+--+--+------+--+
```

The fields are as follows:
* CLA - application CLAss id, one byte specifying what type of instruction is being issued
* INS - INStruction id, one byte to specify which command to execute
* P1 & P2 - Parameter 1 & 2, one byte each, used to specify how to execute the command / options for the command
* Lc - Length of Command data, one byte, can be omitted if no 
* Data - the Data provided for processing by the command, if any
* Le - Length Expected, one byte indicating the length of data the terminal is expected to return in its response

In the above case, CLA is 00, indicating that the commands being issued are standard inter-industry commands. INS A4 indicates the SELECT FILE command. P1 == 04, when using the SELECT FILE command, indicates that selection is being done by DF name. P2 == 00, with SELECT FILE, indicates that the first file matching the data provided should be selected if more than one match is found. The file name provided is three bytes long, so Lc is 03 and the three bytes of Data follow. Le is omitted.

Lc, Data, and Le may be omitted if not necessary for the command being issued. For instance, in the example above, there is no specific length of response data expected, so no Le is provided. An example of an APDU where Le is provided but Lc & Data are not is as follows:

```
+---+---+--+--+--+------+--+
|CLA|INS|P1|P2|Lc| Data |Le|
+---+---+--+--+--+------+--+
|-00|-84|00|00|--|------|08|
+---+---+--+--+--+------+--+
```


## Usage
wubblegum is a command line tool. To understand the usage of wubblegum and its options, run `python3 ./wubblegum.py --help` or read on.
If you want to issue commands (including raw APDUs in hex format) to a card interactively, run `python3 ./apdu_console.py`.

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

### Card state
Wubblegum and the APDU console can keep track of what has been discovered during card enumeration. use `-s` or `--state-file` to specify a file to load and save card data to. This can be useful for various reasons, such as if you want to enumerate a card with wubblegum and then interact with it using the APDU console while keeping track of the structure of the target card.

Any option that requires prior enumeration of the card (e.g. INS enumeration needs valid CLA values) can be satisfied by a card state that contains the needed card data.

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
To enumerate CLA, Files by name using the included RID wordlist, INS with autoprune, and card data from the first card reader in verbose mode, saving to `card1.state`:
`python3 ./wubblegum.py --enumerate c fn i d --wordlist rid_list.txt --ins-auto-prune -v -s card1.state`
