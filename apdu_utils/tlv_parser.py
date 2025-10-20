from struct import unpack
from binascii import hexlify
import pdb

def parse_tlv(tlv_data, tag_len=1, length_len=1, nested=False, compact_tlv=False):
    #pdb.set_trace()
    tlv_data = bytes(tlv_data)
    total_len = len(tlv_data)
    if compact_tlv:
        header_len = 1
    else:
        header_len = tag_len + length_len
    if total_len < header_len:
        if nested:
            return None
        else:
            return []
    objects = []
    pos = 0
    while total_len - pos >= header_len:
        if compact_tlv:
            header = tlv_data[pos]
            # split byte into first four and last four bits per compact-tlv spec
            tag = header >> 4
            value_len = header % 16
        else:
            header = tlv_data[pos:pos+header_len]
            tag = hexlify(header[:tag_len])
            value_len = 0
            for i in range(length_len):
                value_len << 8
                value_len += ord(header[tag_len+i:])
        pos += header_len
        if len(tlv_data[pos:]) < value_len:
            if nested:
                return None
            else:
                return tlv_data
        else:
            value = tlv_data[pos:pos+value_len]
        if nested:
            parsed = parse_tlv(value, nested=True)
            if parsed != None:
                value = parsed
        objects.append([tag, value])
        pos += value_len
    if pos != total_len:
        return tlv_data
    else:
        return objects