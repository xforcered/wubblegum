import pdb
from time import sleep
from smartcard.Exceptions import CardConnectionException, NoCardException

ins_blocklist = [
    0x04,  # deactivate file/invalidate
    0x0c,  # erase record
    0x0e,  # erase binary
    0x0f,  # erase binary
    0x16,  # card block, vsdc
    0x1e,  # application block
    0xc4,  # delete applets
    0xe4,  # delete file
    0xe6,  # terminate df
    0xe8,  # terminate ef
    0xee,  # write lock
    0xfe,  # terminate card usage
    0x6c, 0x6d, 0x92, 0x93  # sim card
]

known_ins_values = {
    0x04: 'ISO7816-4: Deactivate File',
    0x0c: 'ISO7816-4: Erase Record(s)',
    0x0d: 'SAGEM SCT U34: Verify Transport Code',
    0x0e: 'ISO7816-4: Erase Binary',
    0x0f: 'ISO7816-4: Erase Binary',
    0x10: 'ISO7816-4: Perform SCQL Operation',
    0x12: 'ISO7816-4: Perform Transaction Operation',
    0x14: 'ISO7816-4: Perform User Operation',
    0x16: 'VSDC: Card Block / Freeze Access Conditions',
    0x18: 'VSDC: Application Unblock',
    0x1e: 'VSDC: Application Block',
    0x20: 'ISO7816-4: Verify',
    0x21: 'ISO7816-4: Verify',
    0x22: 'ISO7816-4: Manage Security Environment',
    0x24: 'ISO7816-4: Change Reference Data / EMV: PIN change / unblock',
    0x26: 'ISO7816-4: Disable Verification Requirement',
    0x28: 'ISO7816-4: Enable Verification Requirement',
    0x2a: 'ISO7816-4: Perform Security Operation',
    0x2c: 'ISO7816-4: Reset Retry Counter',
    0x2e: '3GPP TS 11.11: Write Code Status',
    0x30: '3GPP TS 51.011: Decrease',
    0x32: '3GPP TS 11.11: Increase',
    0x34: 'EN 726-3: Decrease Stamped',
    0x36: 'EN 726-3: Increase Stamped',
    0x39: 'Javacard: Authenticate User',
    0x44: 'ISO7816-4: Activate File',
    0x46: 'ISO7816-4: Generate Asymmetric Key Pair',
    0x50: 'GlobalPlatform: Initialize Update',
    0x52: 'EN 1546-3: Credit IEP',
    0x54: 'EN 1546-3: Debit IEP',
    0x56: 'EN 1546-3: Convert IEP Currency',
    0x58: 'EN 1546-3: Update IEP Parameter',
    0x5a: 'EN 1546-3: Get Previous IEP Signature',
    0x70: 'ISO7816-4: Manage Channel / EN 1546-3: Initialize PSAM',
    0x72: 'EN 1546-3: CREDIT PSAM, Pay from IEP to the PSAM',
    0x74: 'EN 1546-3: PSAM Complete',
    0x76: 'EN 1546-3: Initialize PSAM',
    0x78: 'GlobalPlatform: End R-MAC Session / EN 1546-3: Execute PSAM online booking of an amount',
    0x7a: 'GlobalPlatform: Begin R-MAC Session / EN 1546-3: End PSAM online booking of an amount',
    0x7c: 'EN 1546-3: INITIALIZE PSAM for Offline Collection',
    0x7e: 'EN 1546-3: End PSAM offline booking of an amount',
    0x82: 'ISO7816-4: External (/ Mutual) Authenticate',
    0x84: 'ISO7816-4: Get Challenge',
    0x86: 'ISO7816-4: General Authenticate',
    0x87: 'ISO7816-4: General Authenticate',
    0x88: 'ISO7816-4: Internal Authenticate',
    0xa0: 'ISO7816-4: Search Binary',
    0xa1: 'ISO7816-4: Search Binary',
    0xa2: 'ISO7816-4: Search Record',
    0xa4: 'ISO7816-4: Select File/Application',
    0xa8: 'VSDC: Get Processing Options',
    0xac: 'EN 726-3: Close application',
    0xae: 'EMV Book 3: Generate Application Cryptogram / EN 726-3: Execute file',
    0xb0: 'ISO7816-4: Read Binary',
    0xb1: 'ISO7816-4: Read Binary',
    0xb2: 'ISO7816-4: Read Record(s)',
    0xb3: 'ISO7816-4: Read Record(s)',
    0xb4: 'Javacard: Component Data, EN 726-3: Read Binary Stamped',
    0xb6: 'EN 726-3: Read Record Stamped',
    0xb8: 'Javacard: Create Applet',
    0xba: 'Javacard: CAP End',
    0xbc: 'Javacard: Component End',
    0xbe: 'GEMPLUS GemClub-MEMO: Read',
    0xc0: 'ISO7816-4: Get Response',
    0xc2: 'ISO7816-4: Envelope',
    0xc3: 'ISO7816-4: Envelope',
    0xc4: 'Javacard: Delete Applets',
    0xca: 'ISO7816-4: Get Data',
    0xcb: 'ISO7816-4: Get Data',
    0xd0: 'ISO7816-4: Write Binary',
    0xd1: 'ISO7816-4: Write Binary',
    0xd2: 'ISO7816-4: Write Record',
    0xd4: 'EN 726-3: Extend file',
    0xd6: 'ISO7816-4: Update Binary',
    0xd7: 'ISO7816-4: Update Binary',
    0xd8: 'GlobalPlatform: Put Key / EMV: Set Card Status',
    0xda: 'ISO7816-4: Put Data',
    0xdb: 'ISO7816-4: Put Data',
    0xdc: 'ISO7816-4: Update Record',
    0xdd: 'ISO7816-4: Update Record',
    0xde: 'GEMPLUS GemClub-MEMO: Update / 3GPP TS 11.11: Load AoC(SICAP)',
    0xe0: 'ISO7816-4: Create File',
    0xe2: 'ISO7816-4: Append Record',
    0xe4: 'ISO7816-4: Delete File',
    0xe6: 'ISO7816-4: Terminate DF',
    0xe8: 'ISO7816-4: Terminate EF',
    0xea: '3GPP TS 11.11: Create Binary',
    0xee: 'VSDC: Write Lock',
    0xf0: 'GlobalPlatform: Set Status',
    0xf2: 'GlobalPlatform: Get Status',
    0xf8: 'SAGEM SCT U34 8.1.1: Dir',
    0xfa: '3GPP TS 11.11: Sleep',
    0xfb: 'SAGEM SCT U34 8.1.1: Dir',
    0xfc: 'SAGEM SCT U34 8.1.3: Read Info',
    0xfe: 'ISO7816-4: Terminate Card Usage'
}


def cla_enum(conn, file, file_select_method, full_enum=False, max_fail=5, throttle_msec=0):
    responses = {}
    fail_count = 0
    needs_reconnect = 0
    throttle_sec = throttle_msec / 1000
    file_select_methods = {'id': 0, 'path': 2, 'name': 4}
    p1 = file_select_methods[file_select_method]
    file_len = len(file)

    cla_list = [0]
    cla_list += range(0x1, 0x100) if full_enum else range(0x80, 0x100)
    cla_iter = iter(cla_list)

    cla = next(cla_iter)  # initialize loop
    while True:
        try:
            if needs_reconnect:
                conn.reconnect()
                needs_reconnect = 0
            sleep(throttle_sec)
            # SELECT the file we already know with the candidate CLA
            (resp, sw1, sw2) = conn.transmit([cla, 0xA4, p1, 0, file_len] + list(file)) 
            try:  # hacky but we need to check if we have recorded anything for this sw1/sw2 pair yet
                _ = responses[(sw1, sw2)]
            except KeyError:
                responses[(sw1, sw2)] = {}
            responses[(sw1, sw2)][cla] = resp
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting...")
            exit()
        except (CardConnectionException, NoCardException):
            needs_reconnect = 1
            if fail_count >= max_fail:
                print(f"Failed {max_fail} times with CLA {cla:02x}, moving on")
            else:
                fail_count += 1
                continue
        try:
            cla = next(cla_iter)
        except StopIteration:
            break
        fail_count = 0
    return responses


def ins_enum(conn, file, file_select_method, cla, use_blocklist=True, max_fail=5, throttle_msec=0, verbose=False):
    responses = {}
    fail_count = 0
    throttle_sec = throttle_msec / 1000
    file_select_methods = {'id': 0, 'path': 2, 'name': 4}
    p1 = file_select_methods[file_select_method]
    file_len = len(file)

    try:
        conn.reconnect()
        # reselect the file if not using implicit file selection
        if file != "":
            conn.transmit([cla, 0xa4, p1, 0, file_len] + list(file))
        needs_reconnect = 0
    except (CardConnectionException, NoCardException):
        fail_count += 1
        needs_reconnect = 1

    if use_blocklist:
        ins_iter = filter(lambda x: x not in ins_blocklist, range(0x100))
    else:
        ins_iter = range(0x100)

    ins = next(ins_iter)
    while True:
        try:
            if needs_reconnect:
                conn.reconnect()
                # reselect the file if not using implicit file selection
                if file != "":
                    conn.transmit([cla, 0xa4, p1, 0, file_len] + list(file))
                needs_reconnect = 0
            sleep(throttle_sec)
            (resp, sw1, sw2) = conn.transmit([cla, ins, 0, 0])
            try:  # hacky but we need to check if we have recorded anything for this sw1/sw2 pair yet
                _ = responses[(sw1, sw2)]
            except KeyError:
                responses[(sw1, sw2)] = {}
            responses[(sw1, sw2)][ins] = resp
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting...")
            exit()
        except (CardConnectionException, NoCardException):
            needs_reconnect = 1
            if fail_count >= max_fail:
                print(f"Failed {max_fail} times with INS {ins:02x}, moving on")
            else:
                fail_count += 1
                continue
        try:
            ins = next(ins_iter)
            if verbose:
                print(f"\rTrying INS {ins:02x}", end='', flush=True)
        except StopIteration:
            if verbose:
                print()
            break
    return responses


def cla_ins_enum(conn, file, file_select_method, use_blocklist=True, max_fail=5, throttle_msec=0, verbose=False):
    responses = {}
    fail_count = 0
    throttle_sec = throttle_msec / 1000
    file_select_methods = {'id': 0, 'path': 2, 'name': 4}
    p1 = file_select_methods[file_select_method]
    file_len = len(file)

    cla_iter = iter(range(0x100))
    cla = next(cla_iter)

    while True: # CLA loop
        if use_blocklist:
            ins_iter = filter(lambda x: x not in ins_blocklist, range(0x100))
        else:
            ins_iter = range(0x100)
        ins = next(ins_iter)
        while True: # INS loop
            try:
                sleep(throttle_sec)
                # reselect the known file unless it is implicit selection
                if file != "":
                    conn.transmit([0x00, 0xA4, p1, 0x00, file_len] + list(file))
                (resp, sw1, sw2) = conn.transmit([cla, ins, 0, 0])
                try:  # hacky but we need to check if we have recorded anything for this sw1/sw2 pair yet
                    _ = responses[(sw1, sw2)]
                except KeyError:
                    responses[(sw1, sw2)] = {}
                responses[(sw1, sw2)][(cla,ins)] = resp
            except KeyboardInterrupt:
                print("Caught keyboard interrupt, exiting...")
                exit()
            except (CardConnectionException, NoCardException):
                needs_reconnect = 1
                if fail_count >= max_fail:
                    print(f"Failed {max_fail} times with CLA {cla:02x} INS {ins:02x}, moving on")
                else:
                    fail_count += 1
                    continue
            except TypeError:
                pdb.set_trace()
            try:
                ins = next(ins_iter)
                if verbose:
                    print(f"\rTrying CLA {cla:02x} INS {ins:02x}", end='', flush=True)
            except StopIteration:
                break
        try:
            cla = next(cla_iter)
        except StopIteration:
            break
    return responses
