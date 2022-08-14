import pdb
from time import sleep
from smartcard.util import toBytes
from smartcard.Exceptions import CardConnectionException, NoCardException
from uttlv import TLV

from .responses import get_readable_response


def read_records(conn, cla, file, file_select_method, max_fail=5, throttle_msec=0, verbose=False):
    throttle_sec = throttle_msec/1000
    file_select_methods = {'id': 2, 'path': 8, 'name': 4}
    select_method_byte = file_select_methods[file_select_method]
    filename_len = len(file)

    for ef_id in range(1, 31):  # EF ids can be 1-30
        file_not_found = False
        for record in range(256):
            if verbose:
                print("\rChecking EFI %2x Record %2x" % (ef_id, record), end='', flush=True)
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
                    # print('DEBUG: Record %2x EFI %2x produced response: %x %x %s' % (record, ef_id, sw1, sw2, resp))
                    # print('DEBUG: ' + get_readable_response(sw1, sw2))
                    if sw1 == 0x90:
                        print('\rRecord %2x EFI %2x produced empty response' % (record, ef_id))
                    elif sw1 == 0x6c:
                        apdu = [cla, 0xb2, record, (ef_id << 3) + 4, sw2]
                        (resp, sw1, sw2) = conn.transmit(apdu)
                        tlv_parser = TLV(list(range(256)))
                        tlv_parser.parse_array(resp)
                        print('\rEFI %2x Record %2x produced data:' % (ef_id, record))
                        print(tlv_parser.tree())
                    elif (sw1, sw2) == (0x6a, 0x82):
                        file_not_found = True
                    break
                except KeyboardInterrupt:
                    exit()
                except (CardConnectionException, NoCardException):
                    if fail_count >= max_fail:
                        print('\rFailed at EFI %2x Record %2x' % (ef_id, record))
                        break
                    else:
                        fail_count += 1
                        needs_reconnect = True
                        continue


def get_data(conn, cla, file, file_select_method, max_fail=5, throttle_msec=0, verbose=False):
    # try dumping first
    throttle_sec = throttle_msec/1000
    file_select_methods = {'id': 2, 'path': 8, 'name': 4}
    select_method_byte = file_select_methods[file_select_method]
    filename_len = len(file)

    for p2 in range(256):
        if verbose:
            print("\rChecking Tag %2x" % p2, end='', flush=True)
        fail_count = 0
        needs_reconnect = True
        while True:
            try:
                if needs_reconnect:
                    conn.reconnect()
                    conn.transmit([cla, 0xa4, select_method_byte, 0, filename_len] + list(file))
                    needs_reconnect = False
                (resp, sw1, sw2) = conn.transmit([0, 0xca, 0, p2])
                sleep(throttle_sec)
                # print('DEBUG: Tag %2x produced response: %x %x %s' % (p2, sw1, sw2, resp))
                # print('DEBUG: ' + get_readable_response(sw1, sw2))
                if sw1 == 0x6c:
                    (resp, sw1, sw2) = conn.transmit([0, 0xca, 0, p2, sw2])
                    tlv_parser = TLV(list(range(256)))
                    tlv_parser.parse_array(resp)
                    print('\rTag %2x produced data:' % p2)
                    print(tlv_parser.tree())
                break
            except KeyboardInterrupt:
                exit()
            except (CardConnectionException, NoCardException):
                if fail_count >= max_fail:
                    print('\rFailed while requesting tag %2x' % p2)
                    break
                else:
                    fail_count += 1
                    needs_reconnect = True
                    continue
