import argparse
import itertools
import pdb

from binascii import hexlify, unhexlify

from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, NoReadersException

from apdu_utils.responses import prune_responses
from apdu_utils.file_enum import find_files_by_id, find_files_by_path, find_files_by_name, find_files_by_wordlist
from apdu_utils.cla_ins_enum import cla_enum, ins_enum, known_ins_values
from apdu_utils.data_enum import read_records, get_data

parser = argparse.ArgumentParser(description='Wubblegum: Smart card enumerator')
parser.add_argument('-r', '--reader', type=int, default=0,
                    help='reader to select when more than one is attached to the system')
parser.add_argument('--show-readers', action='store_true',
                    help='show available smart card readers')

parser.add_argument('-e', '--enumerate', action='extend', nargs="+", default=[],
                    help='which items to enumerate: c for CLA values (applications), '
                         'fi for files by ID, fp for files by path, fn for files by name, '
                         'i for INS values (commands), d for card data (records, binary, '
                         'data)')

parser.add_argument('-c', '--cla', action='extend', nargs="+", type=str,
                    help='a list of CLA values, in hex, to use. '
                         'this option can be used multiple times')
parser.add_argument('--full-cla-enum', action='store_true', default=False,
                    help='use this option to brute force through ISO7816 standard-violating '
                         'CLA values. if not enabled, only CLA values 0x00 and 0x80-0xff will be '
                         'enumerated.')

parser.add_argument('-f', '--files', action='extend', nargs="+", default=[],
                    help='a list of files to select instead of brute-force enumerating.')
parser.add_argument('-t', '--filetype', choices=['id', 'path', 'name'], default='name',
                    help='how to select file names on the inserted smart card (default '
                         'by name).')
parser.add_argument('-p', '--filename-prefix', default=None,
                    help='a prefix, hex encoded, that should be used when enumerating '
                         'files by name.')
parser.add_argument('-l', '--filename-brute-length', type=int, default=1,
                    help='the number of bytes to guess when enumerating files by name.')
parser.add_argument('-w', '--wordlist', type=str, default=None,
                    help='a wordlist of hex-encoded filenames to use when enumerating '
                         'files by name.')

parser.add_argument('--throttle', default=0,
                    help='how long to wait inbetween each command, in milliseconds. '
                         'use this if your smart card is throwing so many errors '
                         'that it exceeds the failure threshold.')
parser.add_argument('--max-fail', type=int, default=5,
                    help='the maximum number of times to retry some command before '
                         'giving up.')

parser.add_argument('-i', '--ins', action='extend', nargs="+", default=False,
                    help='a list of INS values, in hex, to use when dumping data')
parser.add_argument('--no-ins-blocklist', action='store_true',
                    help='Wubblegum will not try INS values commonly used for commands that '
                         'delete data or terminate the functionality of the card. if you want '
                         'to try these values anyway, use this option.')
parser.add_argument('--ins-auto-prune', action='store_true',
                    help='use this option to prune any INS values that produce the standard '
                         'code for incorrect INS value and do not prompt the user to prune '
                         'manually.')

parser.add_argument('-v', '--verbose', action='store_true',
                    help='')

args = parser.parse_args()

# --- SETUP ---
if args.show_readers:
    print("\nAvailable smart card readers:")
    for (num, reader_name) in enumerate(readers()):
        print(f"[{num}]: {reader_name}")
    exit()

# sanity check file enum options
if sum(['fi' in args.enumerate, 'fp' in args.enumerate, 'fn' in args.enumerate]) > 1:
    print("\nPlease specify only one of (fi, fp, fn) in -e/--enumerate.")

# TODO: check ATR/historical bytes for clues on
# TODO: check EF.DIR

connection = None
try:
    connection = readers()[args.reader].createConnection()
    connection.connect()
except NoReadersException:
    print("No smart card reader found. Check that your reader is connected.")
    exit()
except NoCardException:
    print("No smart card inserted. If you have multiple smart card readers, you may "
          "select a specific reader with the -r switch.")
    exit()

card = {}  # TODO: convert card structure to OO
cla_list = [int(cla, 16) for cla in args.cla] if args.cla else []

# TODO: add support for simultaneous CLA / INS brute force

# --- ENUMERATE CLA VALUES ---
if 'c' in args.enumerate:
    print("\nBeginning CLA enumeration...")
    cla_responses = cla_enum(connection, args.full_cla_enum, throttle_msec=args.throttle)
    print("CLA enumeration complete.")
    cla_responses = prune_responses(cla_responses)
    cla_list = list(itertools.chain.from_iterable(cla_responses.values()))

for cla in cla_list:
    card[cla] = {}

# --- ENUMERATE FILES ---
file_list = []
file_select_method = None
if 'fi' in args.enumerate:
    print("\nBeginning file enumeration by id...")
    file_select_method = 'id'
    for cla in cla_list:
        file_list = find_files_by_id(connection, cla, args.throttle, verbose=args.verbose)
        for file in file_list:
            card[cla][file] = {}
elif 'fp' in args.enumerate:
    print("\nBeginning file enumeration by path...")
    file_select_method = 'path'
    for cla in cla_list:
        file_list = find_files_by_path(connection, cla, [], args.throttle, verbose=args.verbose)
        for file in file_list:
            card[cla][file] = {}
elif 'fn' in args.enumerate:
    print("\nBeginning file enumeration by DF name...")
    file_select_method = 'name'
    prefix = list(unhexlify(args.filename_prefix)) if args.filename_prefix else []  # convert to int array
    for cla in cla_list:
        if args.wordlist:
            file_list = find_files_by_wordlist(connection, cla, wordlist=args.wordlist,
                                               throttle_msec=args.throttle, verbose=args.verbose)
        else:
            file_list = find_files_by_name(connection, cla, prefix=prefix, brute_length=args.filename_brute_length,
                                           throttle_msec=args.throttle, verbose=args.verbose)
        for file in file_list:
            card[cla][bytes(file)] = {}
elif args.files:
    file_select_method = args.filetype
    for cla in cla_list:
        for file in args.files:
            card[cla][unhexlify(file)] = {}
else:
    print("No file enumeration requested and no file identifiers provided. Can't continue.\n"
          "Use --files to specify files to use, or enumerate files with -e <fi/fp/fn>.")
    parser.print_help()
    exit()

# --- ENUMERATE INS VALUES ---
if 'i' in args.enumerate:
    ins_list = []

    if not file_select_method:
        file_select_method = 'name'

    for cla in card:
        for file in card[cla]:

            print(f"\nBeginning INS enumeration for CLA {hex(cla)[2:]} File {toHexString(list(file))}")
            ins_responses = ins_enum(connection, cla, list(file), file_select_method, not args.no_ins_blocklist,
                                     args.max_fail, args.throttle, verbose=args.verbose)

            if args.ins_auto_prune:
                try:
                    ins_responses.pop((0x6d, 0x00))
                except KeyError:
                    pass
            else:
                ins_responses = prune_responses(ins_responses)  # TODO: make pruning occur after all brute forcing
            ins_list = list(itertools.chain.from_iterable(ins_responses.values()))
            for ins in ins_list:
                card[cla][file][ins] = {}

# --- DISPLAY CARD STRUCTURE ---
print()
for cla in card:
    print(f"CLA {hex(cla)[2:]}:")
    for file in card[cla]:
        print(f"- File {toHexString(list(file))}:")
        for ins in card[cla][file]:
            description = ''
            if ins in known_ins_values:
                description = ' - ' + known_ins_values[ins]
            print(f"--- INS {hex(ins)[2:]}{description}")

# --- READ DATA / RECORDS / BINARY ---
# TODO: Read binary from files supporting
if 'd' in args.enumerate:
    for cla in card:
        for file in card[cla]:
            if 0xca in card[cla][file]:  # INS 0xCA == GET DATA
                print(f"\nEnumerating data for {toHexString(list(file))}")
                get_data(connection, cla, file, file_select_method, max_fail=args.max_fail,
                         throttle_msec=args.throttle, verbose=args.verbose)
            if 0xb2 in card[cla][file]:  # INS 0xB2 == READ RECORD(S)
                print(f"\nEnumerating records for {toHexString(list(file))}")
                read_records(connection, cla, file, file_select_method, max_fail=args.max_fail,
                             throttle_msec=args.throttle, verbose=args.verbose)
