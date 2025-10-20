import pdb
from .tlv_parser import parse_tlv
from smartcard.util import toHexString

def parse_historical_bytes(historical_bytes, card_state=None):
    # TODO: populate card state with discovered information as appropriate
    category_indicator_byte = historical_bytes.pop(0)
    if category_indicator_byte == 0x0:
        status_indicator = historical_bytes[-3:]
        historical_bytes = historical_bytes[:-3]
        print(f'* Last three bytes of historical bytes are a status indicator: {toHexString(status_indicator)}')
        print(f'- Card life cycle status (LCS) is {status_indicator[0]:02x}')
        print(f'- Card status (SW1-SW2) is {status_indicator[1]:02x} {status_indicator[2]:02x}')
    elif category_indicator_byte == 0x80:
        print('* Status indicator is included as compact TLV element')
    elif category_indicator_byte == 0x10:
        dir_data_reference = historical_bytes.pop(0)
        print(f'* DIR data reference included: {dir_data_reference}')
    parsed_bytes = parse_tlv(historical_bytes, compact_tlv=True)
    # DEBUG
    #pdb.set_trace()
    if type(parsed_bytes) == bytes:
        print(f'* Could not parse historical bytes. Bailing out...')
        return
    for (tag, value) in parsed_bytes:
        if tag == 0x1:
            print(f'* Country code: {value}')
        elif tag == 0x2:
            print(f'* Issuer ID: {value}')
        elif tag == 0xf:
            print(f'* Application identifier found: {value}')
        elif tag == 0x3:
            print('* Card service descriptor found:')
            if value[0] & 0x80:
                print('--- Supports file selection by full DF name')
            if value[0] & 0x40:
                print('--- Supports file selection by partial DF name')
            if value[0] & 0x20:
                print('--- Data available in EF.DIR')
            if value[0] & 0x10:
                print('--- Data available in EF.ATR')
            ef_dir_atr_access_svc = (value[0] >> 1) % 0x8
            if ef_dir_atr_access_svc == 4:
                print('--- EF.DIR & EF.ATR accessible by READ BINARY cmd')
            if ef_dir_atr_access_svc == 0:
                print('--- EF.DIR & EF.ATR accessible by READ RECORD cmd')
            if ef_dir_atr_access_svc == 2:
                print('--- EF.DIR & EF.ATR accessible by GET DATA cmd')
        elif tag == 0x4:
            command_len = len(value)
            print('* Initial data string recovery APDU specified:')
            if command_len == 1:
                # READ BINARY, expected response len specified
                # TODO: issue APDU to card and retrieve initial data string
                print(f'- 00 B0 00 00 {toHexString(value)}')
            elif command_len == 2:
                ef_structure = value[0] >> 7
                if ef_structure == 1:
                    # READ BINARY, short EF specified
                    # TODO: issue APDU to card and retrieve initial data string
                    print(f'- 00 B0 {toHexString( [value[0]] )} 00 {toHexString( [value[1]] )}')
                else:
                    # READ RECORD, short EF specified
                    # TODO: issue APDU to card and retrieve initial data string
                    # set P2 bits 8-4 to initial access byte bits 5-1, set bits 3-1 to 0b110
                    p2 = ((value[0] << 3) & 0xff) + 0x110
                    print(f'- 00 B2 01 {toHexString( [p2] )} {toHexString( [value[1]] )}')
            elif command_len >= 5:
                print(f'- {toHexString(value)}')
        elif tag == 0x5:
            print(f'* Card issuer data: {value}')
        elif tag == 0x6:
            print(f'* Pre-issuing data: {value}')
        elif tag == 0x7:
            print('* Card capabilities data:')
            capabilities_len = len(value)
            if capabilities_len >= 1:
                print('* Supported file selection methods:')
                if value[0] & 0x80:
                    print('--- Full DF name')
                if value[0] & 0x40:
                    print('--- Partial DF name')
                if value[0] & 0x20:
                    print('--- Path')
                if value[0] & 0x10:
                    print('--- File identifier')
                if value[0] & 0x08:
                    print('--- Implicit file selection')
                if value[0] & 0x04:
                    print('--- Short EF identifiers supported')
                if value[0] & 0x02:
                    print('--- Record number supported')
                if value[0] & 0x01:
                    print('--- Record identifier supported')
            elif capabilities_len >= 2:
                print('* Data coding:')
                if value[1] & 0x80:
                    print('--- EFs of TLV structure supported')
                # data encoded into second and third bits of byte
                write_func_value = value[1] % 0x80 >> 5
                print('--- Behavior of write functions: ', end='')
                if write_func_value == 0:
                    print('One-time write')
                elif write_func_value == 1:
                    print('Proprietary')
                elif write_func_value == 2:
                    print('Write OR')
                elif write_func_value == 3:
                    print('Write AND')
                if value[1] & 0x10:
                    print('--- value FF valid as first byte of BER-TLV tag fields')
                else:
                    print('--- value FF NOT valid as first byte of BER-TLV tag fields')
                # data encoded into last nibble of byte
                print(f'* Data unit size in quartets: {value[1] & 0x0f}')
            elif capabilities_len == 3:
                if value[2] & 0x80:
                    print('* Command chaining supported')
                if value[2] & 0x40:
                    print('* Extended Lc and Le fields supported')
                logical_channel_num_assignment = value[2] % 0x20 >> 3
                if logical_channel_num_assignment == 0:
                    print('* No logical channel')
                else:
                    print('* Logical channel number assignment supported:')
                    if logical_channel_num_assignment & 0x2:
                        print('--- By card')
                    if logical_channel_num_assignment & 0x1:
                        print('--- By terminal')
                max_logical_channels = value[2] % 0x08
                if max_logical_channels == 7:
                    print('* Eight or more logical channels supported')
                else:
                    print(f'* Logical channels supported: {max_logical_channels+1}')
        elif tag == 0x8:
            status_indicator_length = len(value)
            if status_indicator_length == 1:
                print(f'* Card life cycle status (LCS) is {value[0]:02x}')
            elif status_indicator_length == 2:
                print(f'- Card status (SW1-SW2) is {value[0]:02x} {value[1]:02x}')
            elif status_indicator_length == 3:
                print(f'* Card life cycle status (LCS) is {value[0]}')
                print(f'- Card status (SW1-SW2) is {value[1]:02x} {value[2]:02x}')

        
        # TODO: finish adding support for remaining tags specified in ISO 7816-4