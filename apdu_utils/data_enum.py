import pdb
from time import sleep
from smartcard.util import toBytes, toHexString
from smartcard.Exceptions import CardConnectionException, NoCardException
from uttlv import TLV

from .responses import get_readable_response


def read_records(conn, cla, file, file_select_method, max_fail=5, throttle_msec=0, verbose=False):
    cla = int(cla,16)
    file = toBytes(file)
    throttle_sec = throttle_msec/1000
    file_select_methods = {'id': 2, 'path': 8, 'name': 4}
    select_method_byte = file_select_methods[file_select_method]
    filename_len = len(file)

    for ef_id in range(1, 31):  # EF ids can be 1-30
        file_not_found = False
        for record in range(1, 255): # Records can be 1-254
            if verbose:
                print("\rChecking EFI %2x Record %2x                        " % (ef_id, record), end='', flush=True)
            fail_count = 0
            needs_reconnect = True
            if file_not_found:
                file_not_found = False
                break
            while True:
                try:
                    if needs_reconnect:
                        conn.reconnect()
                        conn.transmit([cla, 0xa4, select_method_byte, 0, filename_len] + list(file))
                        needs_reconnect = False
                    apdu = [cla, 0xb2, record, (ef_id << 3) + 4]
                    (resp, sw1, sw2) = conn.transmit(apdu)
                    sleep(throttle_sec)
                    if sw1 == 0x90:
                        print('\rRecord %02x EFI %02x produced empty response' % (record, ef_id))
                        record += 1
                        break
                    elif sw1 == 0x6c:
                        apdu = [cla, 0xb2, record, (ef_id << 3) + 4, sw2]
                        (resp, sw1, sw2) = conn.transmit(apdu)
                        print('\rEFI %02x Record %02x produced data:' % (ef_id, record))
                        print(resp)
                        break
                    elif (sw1, sw2) == (0x6a, 0x82):
                        file_not_found = True
                        break
                    elif (sw1, sw2) == (0x6a, 0x83): # record not found
                        break
                    elif (sw1, sw2) == (0x69, 0x85): # conditions not satisfied
                        print(f'\rEFI {ef_id:02x} Record {record:02x} present but denied under current conditions (unauthenticated?)')
                        break
                    else:
                        if verbose:
                            print(f"Unrecognized response code: {sw1:2x}, {sw2:2x}")
                        break
                except KeyboardInterrupt:
                    exit()
                except (CardConnectionException, NoCardException):
                    if fail_count >= max_fail:
                        print('\rFailed at EFI %02x Record %02x' % (ef_id, record), end='', flush=True)
                        break
                    else:
                        fail_count += 1
                        needs_reconnect = True
                        continue


def get_data(conn, cla, file, file_select_method, max_fail=5, throttle_msec=0, verbose=False):
    # try dumping first
    if type(cla) == str:
        cla = int(cla,16)
    file = toBytes(file)
    throttle_sec = throttle_msec/1000
    file_select_methods = {'id': 2, 'path': 8, 'name': 4}
    select_method_byte = file_select_methods[file_select_method]
    filename_len = len(file)

    fail_count = 0
    needs_reconnect = True
    while True:
        try:
            if needs_reconnect:
                conn.reconnect()
                conn.transmit([cla, 0xa4, select_method_byte, 0, filename_len] + list(file))
                needs_reconnect = False
            (resp, sw1, sw2) = conn.transmit([0, 0xca, 0, 0])
            sleep(throttle_sec)
            if sw1 == 0x6c:
                (resp, sw1, sw2) = conn.transmit([0, 0xca, 0, 0, sw2])
                return resp
            else:
                return None
        except KeyboardInterrupt:
            exit()
        except (CardConnectionException, NoCardException):
            if fail_count >= max_fail:
                print(f'Failed while attempting GET DATA command on file {toHexString(file, 1)}', end='', flush=True)
                return None
            else:
                fail_count += 1
                needs_reconnect = True
                continue
