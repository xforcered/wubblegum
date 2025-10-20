import argparse
import itertools
import pdb

from binascii import hexlify, unhexlify

from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.ATR import ATR
from smartcard.Exceptions import NoCardException, NoReadersException

from apdu_utils.responses import prune_responses
from apdu_utils.file_enum import find_files_by_id, find_files_by_path, find_files_by_name, find_files_by_wordlist
from apdu_utils.cla_ins_enum import cla_enum, ins_enum, cla_ins_enum
from apdu_utils.data_enum import read_records, get_data
from apdu_utils.card_class import CardClass
from apdu_utils.historical_bytes import parse_historical_bytes

parser = argparse.ArgumentParser(description='Wubblegum: Smart card enumerator')
parser.add_argument('-r', '--reader', type=int, default=0,
                    help='reader to select when more than one is attached to the system')
parser.add_argument('--show-readers', action='store_true',
                    help='show available smart card readers')

parser.add_argument('-e', '--enumerate', action='extend', nargs="+", default=[],
                    help='which items to enumerate: c for CLA values (applications), '
                         'fi for files by ID, fp for files by path, fn for files by name, '
                         'i for INS values (commands), d for card data (records, binary, '
                         'data), ci for combined CLA and INS brute force')

parser.add_argument('-c', '--cla', action='extend', nargs="+", type=str, default=[],
                    help='a list of CLA values, in hex, to use. '
                         'this option can be used multiple times')
parser.add_argument('--cla-auto-prune', action='store_true', default=False,
                    help='this option will attempt to automatically identify valid CLA values'
                         'based on response codes without prompting the user.')

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

parser.add_argument('-i', '--ins', action='extend', nargs="+", default=[],
                    help='a list of INS values, in hex, to use when dumping data')
parser.add_argument('--no-ins-blocklist', action='store_true',
                    help='Wubblegum will not try INS values commonly used for commands that '
                         'delete data or terminate the functionality of the card. if you want '
                         'to try these values anyway, use this option.')
parser.add_argument('--ins-auto-prune', action='store_true',
                    help='use this option to prune any INS values that produce the standard '
                         'code for incorrect INS value and do not prompt the user to prune '
                         'manually.')

parser.add_argument('--dump', action='store_true',
                    help='Equivalent to -e c fn i d --ins-auto-prune --cla-auto-prune '
                    '--historical-bytes')

parser.add_argument('-s', '--state-file', default=None,
                    help='Provide a file path to load and save state to')

parser.add_argument('-v', '--verbose', action='store_true',
                    help='Give more detailed output')

parser.add_argument('-b', '--historical-bytes', action='store_true',
                    help='Attempt to parse the card-provided info about itself (aka historical bytes)')

args = parser.parse_args()

# --- SETUP ---
if args.show_readers:
    print("\nAvailable smart card readers:")
    for (num, reader_name) in enumerate(readers()):
        print(f"[{num}]: {reader_name}")
    exit()

if args.dump:
    args.enumerate = 'c fn i d'
    args.ins_auto_prune = True
    args.cla_auto_prune = True
    args.historical_bytes = True


# sanity check file enum options
if sum(['fi' in args.enumerate, 'fp' in args.enumerate, 'fn' in args.enumerate]) > 1:
    print("\nPlease specify only one of (fi, fp, fn) in -e/--enumerate.")

# sanity check file names
for file in args.files:
    try:
        unhexlify(file)
    except:
        print("Provided file names / identifiers are not valid hex encoded data")
        exit()

# sanity check ins list
for ins in args.ins:
    assert(0 <= int(cla,16) <= 255)

# sanity check cla list
for cla in args.cla:
    assert(0 <= int(cla,16) <= 255)

# TODO: check EF.DIR

connection = None
try:
    connection = readers()[args.reader].createConnection()
    connection.connect()
except IndexError:
    print("Invalid card reader number, please try --show-readers and choose one of\n"
          "the displayed options.")
    exit()
except NoReadersException:
    print("No smart card reader found. Check that your reader is connected.")
    exit()
except NoCardException:
    print("No smart card inserted. If you have multiple smart card readers, you may "
          "select a specific reader with the -r switch.")
    exit()
    
try:
    card_state = CardClass(args.state_file)
except FileNotFoundError:
    card_state = CardClass()
cla_list = [int(cla, 16) for cla in args.cla] if args.cla else [0] # assume existence of CLA 00

if args.historical_bytes:
    atr = ATR(connection.getATR())
    historical_bytes = atr.getHistoricalBytes()
    if historical_bytes is not None:
        print(toHexString(historical_bytes))
    parse_historical_bytes(historical_bytes, card_state)
    print()

# --- ENUMERATE FILES ---
file_list = [""]
card_state.add_file("", "name")
file_select_method = args.filetype
if 'fi' in args.enumerate:
    print("\nBeginning file enumeration by id...")
    file_select_method = 'id'
    for cla in cla_list:
        file_list = find_files_by_id(connection, cla, args.throttle, verbose=args.verbose)
        for file in file_list:
            card_state.add_file(toHexString(list(file),1), 'id')
elif 'fp' in args.enumerate:
    print("\nBeginning file enumeration by path...")
    file_select_method = 'path'
    for cla in cla_list:
        file_list = find_files_by_path(connection, cla, [], args.throttle, verbose=args.verbose)
        for file in file_list:
            card_state.add_file(toHexString(list(file),1), 'path')
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
            card_state.add_file(toHexString(list(file),1), 'name')
elif args.files:
    file_select_method = args.filetype
    for file in args.files:
        card_state.add_file(file, file_select_method)

card_state.save(args.state_file)

# --- ENUMERATE CLA & INS VALUES SIMULTANEOUSLY ---
if 'ci' in args.enumerate:
    print("\n Beginning combined CLA & INS enumeration...")
    for file in file_list:
        cla_ins_responses = cla_ins_enum(connection, file, file_select_method,
                                         not args.no_ins_blocklist, args.max_fail,
                                         args.throttle, args.verbose)
        
        cla_ins_responses = prune_responses(cla_ins_responses)
        cla_ins_list = list(itertools.chain.from_iterable(cla_ins_responses.values()))
        for (cla, ins) in cla_ins_list:
            try:
                card_state.add_cla(file, cla)
                card_state.add_ins(file, cla, ins)
            except:
                #debug
                pdb.set_trace()
    print("\nCLA & INS combined enumeration complete.")


# --- ENUMERATE CLA VALUES ---
if 'c' in args.enumerate and not 'ci' in args.enumerate:
    print("\nBeginning CLA enumeration...")
    for file in file_list:
        cla_responses = cla_enum(connection, file, file_select_method, throttle_msec=args.throttle)
        if args.cla_auto_prune:
            negative_responses = [(0x68, 0x81), (0x68, 0x82), (0x6e, 0x00)]
            for negative_response in negative_responses:
                if negative_response in cla_responses:
                    cla_responses.pop(negative_response)
        else:
            cla_responses = prune_responses(cla_responses)
        for cla in list(itertools.chain.from_iterable(cla_responses.values())):
            card_state.add_cla(file, f'{cla:02x}')
    print("CLA enumeration complete.")


card_state.save(args.state_file)


# --- ENUMERATE INS VALUES ---
if 'i' in args.enumerate and not 'ci' in args.enumerate:
    ins_list = []

    if not file_select_method:
        file_select_method = 'name'

    file_list = card_state.get_file_list()
    if not file_list:
        print(f"No known files, skipping INS enumeration.")
    for file in file_list:
        for cla in card_state.get_cla_list(file):
            print(f"\nBeginning INS enumeration for File {file} CLA {cla}")
            ins_responses = ins_enum(connection, toBytes(file), file_select_method, int(cla,16), not args.no_ins_blocklist,
                                     args.max_fail, args.throttle, verbose=args.verbose)

            if args.ins_auto_prune:
                negative_responses = [(0x6d, 0x00)]
                for negative_response in negative_responses:
                    if negative_response in ins_responses:
                        ins_responses.pop(negative_response)
            else:
                ins_responses = prune_responses(ins_responses)  # TODO: make pruning occur after all brute forcing
            ins_list = list(itertools.chain.from_iterable(ins_responses.values()))
            for ins in ins_list:
                card_state.add_ins(file, cla, f'{ins:02x}')

card_state.save(args.state_file)

print(card_state)

# --- READ DATA / RECORDS / BINARY ---
# TODO: Read binary from files supporting
if 'd' in args.enumerate:
    for file in card_state.get_file_list():
        for cla in card_state.get_cla_list(file):
            file_select_method = card_state.get_file_type(file)
            ins_list = card_state.get_ins_list(file, cla)
            if 'CA' in ins_list:  # INS 0xCA == GET DATA
                print(f"\nEnumerating data for {file}")
                file_data = get_data(connection, cla, file, file_select_method, max_fail=args.max_fail,
                         throttle_msec=args.throttle, verbose=args.verbose)
                if file_data != None:
                    card_state.set_file_data(cla, file, file_data)
            #TODO: return data instaed of printing and put data in card state
            if 'B2' in ins_list:  # INS 0xB2 == READ RECORD(S)
                print(f"\nEnumerating records for {file}")
                read_records(connection, cla, file, file_select_method, max_fail=args.max_fail,
                             throttle_msec=args.throttle, verbose=args.verbose)

