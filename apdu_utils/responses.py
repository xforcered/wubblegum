def prune_responses(response_dict):
    while True:
        print("\nThe following responses were received:")
        for (index, code) in enumerate(response_dict):
            print(f"[{index}]: {hex(code[0])} {hex(code[1])} ({len(response_dict[code])} responses)")
            print(f"- {get_readable_response(code[0], code[1])}")
        user_choice = input("Enter i to inspect responses, d to delete a set of responses indicating "
                            "incorrect values, a to accept, or x to exit Wubblegum: ").rstrip()
        if user_choice == 'i':
            user_index = int(input("Please enter the index number for the responses you'd like to inspect: "))
            print(response_dict[list(response_dict)[user_index]])
        elif user_choice == 'd':
            user_index = int(input("Please enter the index number for the responses you'd like to delete: "))
            response_dict.pop(list(response_dict)[user_index])  # can't remove items by index, so look up the name
        elif user_choice == 'a':
            return response_dict
        elif user_choice == 'x':
            print("Thank you for using Wubblegum!")
            exit()


def get_readable_response(sw1, sw2):
    if sw1 in response_codes.keys():
        if sw2 in response_codes[sw1].keys():
            return response_codes[sw1][sw2]
        elif 'xx' in response_codes[sw1].keys():
            return response_codes[sw1]['xx']
    else:
        return f'Response code {hex(sw1)} {hex(sw2)} not recognized.'


response_codes = {
    0x61: {
        'xx': 'SW2 indicates the number of response bytes still available'
    },
    0x62: {
        0x00: 'No information given',
        0x81: 'Returned data may be corrupted',
        0x82: 'The end of the file has been reached',
        0x83: 'Invalid DF',
        0x84: 'Selected file is not valid. File descriptor error'
    },
    0x63: {
        0x00: 'Authentication failed. Invalid secret code or forbidden value.',
        0x81: 'File filled up by the last write',
        0xc0: 'Counter value: 0',
        0xc1: 'Counter value: 1',
        0xc2: 'Counter value: 2',
        0xc3: 'Counter value: 3',
        0xc4: 'Counter value: 4',
        0xc5: 'Counter value: 5',
        0xc6: 'Counter value: 6',
        0xc7: 'Counter value: 7',
        0xc8: 'Counter value: 8',
        0xc9: 'Counter value: 9',
        0xca: 'Counter value: a',
        0xcb: 'Counter value: b',
        0xcc: 'Counter value: c',
        0xcd: 'Counter value: d',
        0xce: 'Counter value: e',
        0xcf: 'Counter value: f'
    },
    0x65: {
        0x01: 'Memory failure. There have been problems in writing or reading the EEPROM.',
        0x81: 'Write problem / Memory failure / Unknown mode'
    },
    0x67: {
        0x00: 'Incorrect length or address range error',
        'xx': 'Error, incorrect parameter P3 (ISO code)'
    },
    0x68: {
        0x00: 'The request function is not supported by the card.',
        0x81: 'Logical channel not supported',
        0x82: 'Secure messaging not supported'
    },
    0x69: {
        0x00: 'No successful transaction executed during session',
        0x81: 'Cannot select indicated file, command not compatible with file organization',
        0x82: 'Access conditions not fulfilled',
        0x83: 'Authentication method blocked',
        0x84: 'Referenced data invalidated / Reference data not usable',
        0x85: 'Conditions of use not satisfied /'
              'No currently selected EF, no command to monitor / no Transaction Manager File',
        0x86: 'Command not allowed (no current EF)',
        0x87: 'Expected SM data objects missing',
        0x88: 'SM data objects incorrect',
        0x99: 'Command not allowed / select failed / applet select failed.'
    },
    0x6a: {
        0x00: 'Bytes P1 and/or P2 are incorrect.',
        0x80: 'The parameters in the data field are incorrect',
        0x81: 'Card is blocked or command not supported',
        0x82: 'File not found.',
        0x83: 'Record not found.',
        0x84: 'There is insufficient memory space in record or file',
        0x85: 'Lc inconsistent with TLV structure',
        0x86: 'Incorrect parameters P1-P2',
        0x87: 'The P3 value is not consistent with the P1 and P2 values.',
        0x88: 'Referenced data not found.'
    },
    0x6b: {
        0x00: 'Incorrect reference; illegal address; Invalid P1 or P2 parameter'
    },
    0x6c: {
        0x00: 'Incorrect P3 length.',
        'xx': 'Bad length value in Le; exact correct value is in SW2 (second response code byte)'
    },
    0x6d: {
        0x00: 'Command not allowed. Invalid instruction byte (INS).'
    },
    0x6e: {
        0x00: 'Incorrect application (CLA parameter of a command)'
    },
    0x6f: {
        0x00: 'Checking error'
    },
    0x90: {
        0x00: 'Command executed without error'
    },
    0x91: {
        0x00: 'Purse Balance error cannot perform transaction',
        0x02: 'Purse Balance error'
    },
    0x92: {
        'xx': 'Memory error',
        0x02: 'Write problem / memory failure',
        0x40: 'Error, memory problem'
    },
    0x94: {
        'xx': 'File error',
        0x04: 'Purse selection error or invalid purse',
        0x06: 'Invalid purse detected during the replacement debit step',
        0x08: 'Key file selection error'
    },
    0x98: {
        'xx': 'Security error',
        0x00: 'Warning',
        0x04: 'Access authorization not fulfilled',
        0x06: 'Access authorization in Debit not fulfilled for the replacement debit step',
        0x20: 'No temporary transaction key established',
        0x34: 'Error, Update SSD order sequence not respected'
    },
    0x9f: {
        'xx': 'Success, number of bytes to be read via GET RESPONSE is indicated in SW2 byte.'
    }
}
