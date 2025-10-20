import argparse, json
from binascii import hexlify

from smartcard.System import readers
from smartcard.ATR import ATR
from smartcard.util import toBytes, toHexString
from smartcard.Exceptions import NoCardException, NoReadersException, CardConnectionException

from apdu_utils.responses import get_readable_response
from apdu_utils.card_class import CardClass

from ishell.console import Console
from ishell.command import Command

from apdu_utils.tlv_parser import parse_tlv

import pdb #debug

def send_apdu_raw(apdu, max_tries = 5):
    while max_tries:
        try:
            resp, s1, s2 = conn.transmit(apdu)
            print(f"{hex(s1)},{hex(s2)}: {get_readable_response(s1,s2)}")
            if resp:
                print(f'debug: {parse_tlv(resp, nested=1)}')
            return (resp, s1, s2)
        except CardConnectionException:
            print("Card was disconnected. Attempting to reconnect...")
        except NoCardException:
            print("No card detected, please re-insert card and try again.")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting...")
            exit(0)
        conn.reconnect()
        max_tries -= 1

def send_apdu_hex(hex_apdu):
    return send_apdu_raw(toBytes(hex_apdu))

parser = argparse.ArgumentParser(description='Wubblegum APDU Console')
parser.add_argument('-r', '--reader', type=int, default=0,
                    help='reader to select when more than one is attached to the system')
parser.add_argument('--show-readers', action='store_true',
                    help='show available smart card readers')
parser.add_argument('-s', '--card-state-file', default=None,
                    help='A saved card state to load')

args = parser.parse_args()

if args.show_readers:
    print("\nAvailable smart card readers:")
    for (num, reader_name) in enumerate(readers()):
        print(f"[{num}]: {reader_name}")
    exit()

card_state = CardClass(args.card_state_file)
current_file = None
current_cla = 0x00

try:
    conn = readers()[args.reader].createConnection()
    conn.connect()
    print(f"Connected to smart card reader {readers()[args.reader]}")
except (NoCardException, NoReadersException):
    print(f"Could not connect to specified reader. Try --show-readers")
    exit()



console = Console(prompt="Wubblegum console", prompt_delim=">")

class ExitCommand(Command):
    def run(self, line):
        print("Thanks for using Wubblegum! Exiting...")
        exit(0)

class StatusCommand(Command):
    def run(self, line):
        print(f"Current CLA: {toHexString([current_cla])}")
        if current_file is not None:
            print(f"Selected File: {current_file}")
        print()
        print(f"Card map\n=====\n{card_state!s}")

class ResetCommand(Command):
    def run(self, line):
        print("Resetting...")
        conn.reconnect()
        atr = ATR(conn.getATR())
        historical_bytes = atr.getHistoricalBytes()
        global card_state, current_file, current_cla
        card_state = CardClass(args.card_state_file)
        card_state.parse_historical_bytes(historical_bytes)
        current_file = None
        current_cla = 0x00
        
class LoadCommand(Command):
    def run(self, line):
        line = line.split()
        if len(line) != 2:
            print("Please provide a filename to load a card state from. (ex. load bankcard.wgum)")
            return
        global card_state
        card_state.load(line[1])

class SaveCommand(Command):
    def run(self,line):
        line = line.split()
        if len(line) != 2:
            print("Please provide a filename to save the card state to. (ex. save bankcard.wgum)")
            return
        global card_state
        card_state.save(line[1])

class APDUCommand(Command):
    def run(self, line):
        try:
            send_apdu_hex(line[5:])
        except TypeError:
            print("Could not parse provided APDU. Please check your input and try again.")
            return
            

class ClaCommand(Command):
    def run(self,line):
        line = line.split()
        if len(line) != 2:
            print("Wrong number of arguments: 1 expected (ex. CLA ff)")
            return
        try:
            new_cla = int(line[1], 16)
            if not 0 <= new_cla <= 255:
                print("New CLA must be a hex number between 00 and FF")
                return
            else:
                print("Testing new CLA...")
                (_, s1, s2) = send_apdu_raw([new_cla, 0xa4, 0x00, 0x00])
                if (s1, s2) == (0x6e, 0x00):
                    use_bad_cla = input('This CLA does not appear to be supported. Continue anyway? (y/n) ')[0].lower()=='y'
                    if not use_bad_cla:
                        print("Aborting.")
                        return
                global current_cla
                current_cla = new_cla
                global card_state
                card_state.add_cla(new_cla)
                return
        except ValueError:
            print("Invalid CLA, specify a one-byte CLA in hex digits (ex. cla 3f)")
            return

class SelectNameCommand(Command):
    def run(self, line):
        global current_file
        global card_state
        line = line.split()
        if len(line) != 3:
            print("Wrong number of arguments for select, 2 expected. (ex. select name a0000006)")
            return
        filename = toBytes(line[2])
        apdu = [current_cla, 0xa4, 0x04, 0x00, len(filename)] + filename
        (resp, s1, s2) = send_apdu_raw(apdu)
        if s1 == 0x90: # successful command
            current_file = line[2]
            card_state.add_file(current_cla, line[2], "name")
        elif s1 == 0x61: # success, plus additional response
            (resp, s1, s2) = send_apdu_raw([current_cla, 0xc0, 0x00, 0x00, s2])
            if resp[0] == 0x6f: # FCI
                resp = resp[2:]
            tlv_parser = TLV()
            tlv_parser.parse_array(resp)
            try:
                df_name = hexlify(tlv_parser[0x84]).decode() # DF name entry
                current_file = df_name
                card_state.add_file(current_cla, df_name, "name")
            except IndexError:
                pass
            print(f"{hex(s1)},{hex(s2)}: {get_readable_response(s1,s2)}")
            print(f"{toHexString(resp)}")
        elif (s1, s2) == (0x6a, 0x86):
            print("This card may not support file selection by file name.")

class SelectIdCommand(Command): # TODO: support selection of child files
    def run(self, line):
        line = line.split()
        if len(line) != 3:
            print("Wrong number of arguments for select, 2 expected. (ex. select id 2f01)")
            return
        file_id = toBytes(line[2])
        id_len = len(file_id)
        if id_len != 2:
            print("Could not parse ID. (ex. select id 2f01)")
            return
        apdu = [current_cla, 0xa4, 0x00, 0x00, id_len] + file_id
        (_, s1, s2) = send_apdu_raw(apdu)
        if s1 == 0x90: # successful command
            global current_file
            current_file = line[2]
        elif (s1, s2) == (0x6a, 0x86):
            print("This card may not support file selection by file ID.")
 
class SelectPathCommand(Command):
    def run(self, line):
        line = line.split()
        if len(line) != 3:
            print("Wrong number of arguments for select, 2 expected. (ex. select path 3f000001)")
            return
        file_path = toBytes(line[2])
        path_len = len(file_path)
        if not (path_len % 2 == 0) and (path_len >= 2):
            print("File paths should be expressed as hex sequences that are a "
                  "multiple of four hex digits in length. (ex. select path 3f000001)")
        apdu = [current_cla, 0xa4, 0x08, 0x00, path_len] + file_path
        (_, s1, s2) = send_apdu_raw(apdu)
        if s1 == 0x90: # successful command
            global current_file
            current_file = line[2]
            global card_state
            card_state.add_file(line[2],)
        elif (s1, s2) == (0x6a, 0x86):
            print("This card may not support file selection by file path.")

class SelectMfCommand(Command):
    def run(self,line):
        apdu = [current_cla, 0xa4, 0x00, 0x00]
        (_, s1, s2) = send_apdu_raw(apdu)
        if s1 == 0x90: # successful command
            current_file = line[2]
        elif (s1, s2) == (0x6a, 0x86):
            print("This card may not support MF file selection.")

class GetDataCommand(Command):
    def run(self,line):
        line = line.split()
        num_args = len(line) - 1
        if num_args == 0:
            apdu = [current_cla, 0xca, 0x00, 0x00]
        elif num_args == 1:
            file_id = toBytes(line[1])
            if len(file_id) == 2:
                apdu = [current_cla, 0xcb] + file_id
            else:
                print("File identifier must be two bytes expressed in hex digits. (ex. getdata 0001)")
                return
        else:
            print("Wrong number of arguments. getdata supports 0 or 1 arguments.")
            return
        (_, sw1, sw2) = send_apdu_raw(apdu)
        if sw1 == 0x6c:
            (resp, sw1, sw2) = conn.transmit([0, 0xca, 0, 0, sw2])
            return resp
        else:
            return None


class VerifyCheckCommand(Command):
    def run(self, line):
        line = line.split()
        if len(line) != 3:
            print("Please provide a verification slot number from 0-31 for card-wide PIN\n"
                  "or 128-159 for current file PIN (ex. verify check 1)")
            return
        slot = int(line[2])
        if (0 <= slot <= 31) or (128 <= slot <= 159):
            apdu = [current_cla, 0x20, 0x00] + [slot]
            send_apdu_raw(apdu)
        else:
            print("Slot number invalid. Please try a number between 0-31 for card-wide PIN\n"
                  "or 128-159 for current file PIN")
            return
        
        
        
class VerifyAttemptCommand(Command):
    def run(self, line):
        line = line.split()
        if len(line) != 4:
            print("Please provide a verification slot number from 0-31 for card-wide PIN\n"
                  "or 128-159 for current file PIN *and* a hex-encoded PIN to attempt verification\n"
                  "(ex. verify check 1 01020304) - Note: this will likely lower the number of remaining\n"
                  "verification attempts allowed")
            return
        slot = int(line[2])
        if (0 <= slot <= 31) or (128 <= slot <= 159):
            pin = toBytes(line[3])
            apdu = [current_cla, 0x20, 0x00, slot, len(pin)] + pin
            send_apdu_raw(apdu)
        else:
            print("Slot number invalid. Please try a number between 0-31 for card-wide PIN\n"
                  "or 128-159 for current file PIN")
            return
        
class RecordReadCommand(Command):
    def run(self, line):
        line = line.split()
        num_args = len(line) - 2
        if num_args == 1: # ex. record read 1
            short_ef_id = 0
        elif num_args == 2: # ex. record read 1 3
            short_ef_id = int(line[3])
            if not (1 <= short_ef_id <= 30):
                print("Short EF identifier must be a number from 1-30 if provided\n"
                      "(ex. record read 1 1)")
                return
        else:
            print("Please specify a record number from 0-255 and, if desired,\n"
                  "a short EF identifier from 1-30 (ex. record read 1 1)")
            return
        p2 = (short_ef_id << 3) + 4
        record = int(line[2])
        apdu = [current_cla, 0xb2, record, p2]
        (resp, s1, s2) = send_apdu_raw(apdu)
        if s1 == 0x6c:
            (resp, s1, s2) = send_apdu_raw([current_cla, 0xb2, record, p2, s2])
        # TODO: store record result in card
        print(toHexString(resp))


console.addChild(ExitCommand('exit', 'Exits the console'))
console.addChild(ResetCommand('reset', 'Resets the card and console'))
console.addChild(StatusCommand('status', 'Show status of smart card and console'))
console.addChild(LoadCommand('load', 'Load a card state from a file (ex. load bankcard.wgum)'))
console.addChild(SaveCommand('save', 'Save the current card state to a file (ex. save bankcard.wgum)'))
console.addChild(APDUCommand('apdu', 'Specify an APDU to issue to the card'))

console.addChild(ClaCommand('cla', 'Set the active class (CLA) to use (ex. cla ff)'))
select_cmd = console.addChild(Command('select', 'Select a file from the card by name, path, or id, or select the MF'))
select_cmd.addChild(SelectNameCommand('name','Select a file from the card by file name (ex. select name a0000006)'))
select_cmd.addChild(SelectIdCommand('id', 'Select a file from the card by ID (ex. select id 0001)'))
select_cmd.addChild(SelectPathCommand('path', 'Select a file from the card by path (ex. select path 2f01)'))
select_cmd.addChild(SelectMfCommand('mf', 'Select the MF (root file) of the card (ie. select mf)'))

console.addChild(GetDataCommand('getdata', help='Retrieve data associated to current file or specified file ID (ex. getdata -or- getdata 0001)'))

verify_cmd = console.addChild(Command('verify', 'Check for, or enter, a password or PIN'))
verify_cmd.addChild(VerifyCheckCommand('check', 'Check if a password slot is in use and how many tries'
                                       'remain (ex. verify check 1)'))
verify_cmd.addChild(VerifyAttemptCommand('attempt', 'Attempt to verify a password or PIN (ex. verify attempt 1 01020304)'))

record_cmd = console.addChild(Command('record', 'Search / read / write / erase records'))
record_cmd.addChild(RecordReadCommand('read', 'Read records (record read <record_id> [short_ef_id])'))

console.loop()

"""
while True:
    command = input("Wubblegum APDU console> ").strip().lower().split(' ')
    # command: exit
    if command[0] == "exit":
        print("Thanks for using Wubblegum! Exiting...")
        break
    # command: status
    elif command[0] == "status":
        print(f"CLA: {hex(current_cla)}")
        if current_file is not None:
            print(f"File: {current_file}")
        print(f"Card state: {card_state.to_json()}")
    # command: cla ...
    elif command[0] == "cla":
        if len(command) != 2:
            print("Wrong number of arguments: 1 expected (ex. CLA ff)")
            continue
        try:
            current_cla = int(command[1], 16)
            if current_cla > 256:
                raise ValueError
        except ValueError:
            print("Invalid CLA, specify a one-byte CLA in hex digits (ex. cla 3f)")
        continue
    # command: select ...
    elif command[0] == "select":
        # subcommand: select name ...
        if command[1] == "name":
            if len(command) != 3:
                print("Wrong number of arguments for select, 2 expected.")
                continue
            filename = toBytes(command[2])
            apdu = [current_cla, 0xa4, 0x04, 0x00, len(toBytes(command[2]))] + toBytes(command[2])
            (resp, s1, s2) = send_apdu_raw(apdu)
            pdb.set_trace()
            if s1 == 0x90: # successful command
                current_file = command[2]
            continue
        # subcommand: select id ...
        elif command[1] == "id":
            if len(command) != 3:
                print("Wrong number of arguments for select, 2 expected. (ex. select id 0001)")
                continue
            # send [CLA, a4, 02, 00, filename_len, filename]
            pass
        # subcommand: select path ...
        elif command[1] == "path":
            if len(command) != 3:
                print("Wrong number of arguments for select, 2 expected. (ex. select path 3f000001)")
                continue
            apdu = [current_cla, 0xa4, 0x08, 0x00, len(toBytes(command[2]))] + toBytes(command[2])
            send_apdu_raw(apdu)
            continue
        # subcommand: select mf
        elif command[1] == "mf":
            if len(command) != 2:
                print("select mf takes no arguments.")
                continue
            apdu = [current_cla, 0xa4, 0x00, 0x00]
            send_apdu_raw(apdu)
            continue
        else:
            print("Could not parse file selection method, try select [name|id|path|mf] (ex. select name a0000006)")
            continue
        
    # command: load
    # refresh from state
    elif command[0] == "load":
        if len(command) != 2:
            print("Wrong number of arguments for load, 1 expected.")
            continue
        card_state.load(command[1])
    # command: 
    elif command[0] == "save":
        if len(command) != 2:
            print("Wrong number of arguments for save, 1 expected.")
            continue
        card_state.save(command[1])
    # command: 
    elif command[0] == "verify":
        pass
    # command: 
    elif command[0] == "getdata":
        send_apdu_raw([current_cla,])
    # command: 
    elif command[0] == "help":
        print("Wubblegum APDU console commands:\n"
              "exit - exit the console\n"
              "load <state_file_name> - load a file with a card state\n"
              "save <state_file_name> - save the current card state to a file"
              "status - see the current status of the card and console\n"
              "cla <new_cla_value> - change the current CLA in use\n"
              "reset - reset the console and card\n"
              "select name <file_name> - select a file on the card by hex-encoded file name\n"
              "select id <file_id> - select a file on the card by hex-encoded two-byte identifier\n"
              "select path <file_path> - select a file on the card by hex-encoded file path\n"
              "verify <index> < - \n"
              "getdata - get data from current file")
    else:
        send_apdu_hex(''.join(command))

"""