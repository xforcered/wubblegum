import itertools
import pdb
from time import sleep
from binascii import hexlify, unhexlify
from smartcard.util import toHexString
from smartcard.Exceptions import CardConnectionException, NoCardException
from ...apdu_utils.responses import get_readable_response

def secret_id_enum(conn, cla, throttle_msec=0):
    throttle_sec = throttle_msec / 1000



def verify_brute(conn, cla, secret_iter, throttle_msec=0, secret_id=0, verbose=False):
    throttle_sec = throttle_msec / 1000
    file_list = []
    for i in secret_iter:
        for j in range(256):
            apdu = [cla, 0x20, 0, secret_id]
            try_counter = 0
            if verbose:
                print("\rTrying %2x%2x" % (i, j), end='', flush=True)
            while True:
                resp = sw1 = sw2 = None
                try:
                    sleep(throttle_sec)
                    (resp, sw1, sw2) = conn.transmit(apdu)
                    break
                except (CardConnectionException, NoCardException):
                    conn.reconnect()
                    try_counter += 1
                    if try_counter >= max_fail:
                        print(f"Exceeded max failure count for fileid {hex(i)} {hex(j)}")
                        break
                    continue
                except KeyboardInterrupt:
                    print("Caught keyboard interrupt. Exiting...")
                    exit()
            if sw1 in [0x61, 0x90]:
                if verbose:
                    print('\r%2x%2x produced response: %s' % (i, j, resp))
                    print(get_readable_response(sw1, sw2))
                file_list.append((i, j))
    return file_list


def find_files_by_path(conn, cla, path=None, throttle_msec=0, max_fail=5, verbose=False):
    if path is None:
        path = []
    throttle_sec = throttle_msec / 1000
    file_list = []
    path_len = len(path) + 2
    for i in range(256):
        for j in range(256):
            if verbose:
                print("\rTrying %2x%2x" % (i, j), end='', flush=True)
            apdu = [cla, 0xa4, 8, 0, path_len] + path + [i, j]
            try_counter = 0
            while True:
                resp = sw1 = sw2 = None
                try:
                    sleep(throttle_sec)
                    (resp, sw1, sw2) = conn.transmit(apdu)
                    break
                except (CardConnectionException, NoCardException):
                    conn.reconnect()
                    try_counter += 1
                    if try_counter >= max_fail:
                        print(f"Exceeded max failure count for filepath {hexlify(bytes(path + [i, j]))}")
                        break
                    continue
                except KeyboardInterrupt:
                    print("Caught keyboard interrupt. Exiting...")
                    exit()
            if sw1 in [0x61, 0x90]:
                if verbose:
                    print(f'{hex(i)[2:]}{hex(j)[2:]} produced response: {resp}')
                    print(get_readable_response(sw1, sw2))
                file_list.append(tuple(path + [i, j]))
                file_list += find_files_by_path(conn, cla, path + [i, j], throttle_msec, max_fail, verbose)
    return file_list


def find_files_by_name(conn, cla, prefix=None, brute_length=1, throttle_msec=0,
                       max_fail=5, verbose=False, tarpit_threshold=100):
    if prefix is None:
        prefix = []
    elif len(prefix) >= 16:
        return []
    throttle_sec = throttle_msec / 1000
    file_list = []
    filename_len = len(prefix) + brute_length
    for filename in itertools.combinations_with_replacement(range(256), brute_length):
        apdu = [cla, 0xa4, 4, 0, filename_len] + prefix + list(filename)
        try_counter = needs_reconnect = 0
        if verbose:
            print(f"\rTrying {toHexString(list(prefix))}{toHexString(list(filename))}", end='', flush=True)
        # check filename
        while True:
            resp = sw1 = sw2 = None
            try:
                if needs_reconnect:
                    conn.reconnect()
                    needs_reconnect = 0
                sleep(throttle_sec)
                (resp, sw1, sw2) = conn.transmit(apdu)
                break
            except (CardConnectionException, NoCardException):
                needs_reconnect = 1
                try_counter += 1
                if try_counter >= max_fail:
                    print(f"Exceeded max failure count for filename {hexlify(bytes(prefix + list(filename)))}")
                    break
                continue
            except KeyboardInterrupt:
                print("Caught keyboard interrupt. Exiting...")
                exit()
        if sw1 in [0x90, 0x61]:
            file_list.append(prefix + list(filename))
    if verbose:
        print()
    if len(file_list) >= tarpit_threshold ** brute_length:
        # some cards return positive results for any file starting with certain prefixes
        return []
    longer_filenames = []
    for identified_file in file_list:
        longer_filenames += find_files_by_name(conn, cla, identified_file,
                                               brute_length=1, throttle_msec=throttle_msec,
                                               max_fail=max_fail, verbose=verbose)
    file_list += longer_filenames
    if verbose and file_list:
        print(f"\nFound files:")
        for found_file in file_list:
            print(f"{toHexString(found_file)}")
    return file_list


def find_files_by_wordlist(conn, cla, wordlist='rid_list.txt', throttle_msec=0,
                           max_fail=5, verbose=False, tarpit_threshold=100):
    throttle_sec = throttle_msec / 1000
    file_list = []
    with open(wordlist, 'r') as wordlist_file:
        for filename in wordlist_file:
            filename = unhexlify(filename.rstrip())
            filename_len = len(filename)
            apdu = [cla, 0xa4, 4, 0, filename_len] + list(filename)
            try_counter = needs_reconnect = 0
            if verbose:
                print(f"\rTrying {toHexString(list(bytes(filename)))}             ", end='', flush=True)
            # check filename
            while True:
                resp = sw1 = sw2 = None
                try:
                    if needs_reconnect:
                        conn.reconnect()
                        needs_reconnect = 0
                    sleep(throttle_sec)
                    (resp, sw1, sw2) = conn.transmit(apdu)
                    break
                except (CardConnectionException, NoCardException):
                    needs_reconnect = 1
                    try_counter += 1
                    if try_counter >= max_fail:
                        print(f"Exceeded max failure count for filename {hexlify(bytes(list(filename)))}")
                        break
                    continue
                except KeyboardInterrupt:
                    print("Caught keyboard interrupt. Exiting...")
                    exit()
            if sw1 in [0x90, 0x61]:
                file_list.append(list(filename))
        if verbose and file_list:
            print(f"\nFound files:")
            for found_file in file_list:
                print(f"{toHexString(found_file)}")
    return file_list
