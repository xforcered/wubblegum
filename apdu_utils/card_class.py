import pdb

import json
from .cla_ins_enum import known_ins_values
from smartcard.util import toHexString

"""
The hierarchy of a card state as represented in Wubblegum is like this:

{
    # Files
    "a00000063a": {                 # identifier
        "ef_data": "asdf",            # EF Data
        "file_select_method": "name", # method of selection (id, name, or path)
        # Records
        "records": {
            "0" : "foobar", # record 0
            "1" : "garply"  # record 1
        },
        # Commands
        "commands": {
            "00" : { # Class (CLA) 00 
                # Commands (INS)
                [
                    "20", # VERIFY
                    "a4"  # SELECT
                ]
            }
        }
    }
}
"""

class CardClass:
    card = {}
    capabilities = {}
    atr = ""
    current_file = None
    
    def __init__(self, card=None):
        if card != None:
            self.load(card)
    
    def to_json(self):
        #TODO: include ATR / historical bytes in card JSON
        return json.dumps(self.card)
    
    # --- DISPLAY CARD STRUCTURE ---
    def __str__(self):
        pretty_output = ""
        for file in self.get_file_list():
            if file == "":
                pretty_output += f"Implicit file selection:\n"
            else:
                pretty_output += f"File {file}:\n"
            for cla in self.get_cla_list(file):
                pretty_output += f"- CLA {cla}:\n"
                for ins in self.get_ins_list(file, cla):
                    description = ''
                    ins = int(ins,16)
                    if ins in known_ins_values:
                        description = ' - ' + known_ins_values[ins]
                    pretty_output+= f"--- INS {ins:02x}{description}\n"
        return pretty_output

    def reset(self):
        self.card = {}
        self.capabilities = {}
        self.atr = ""
        self.current_file = None

    def load(self, filename):
        with open(filename, 'r') as card_file:
            self.card = json.load(card_file)
        return
    
    def save(self, filename):
        if filename is None:
            return
        with open(filename, 'w') as card_file:
            json.dump(self.card, card_file)
        return

    def get_cla_list(self, file):
        if type(file) == list:
            file = toHexString(file,1)
        if self.card.get(file):
            return list(self.card[file]["commands"].keys())
        else:
            return []

    def add_cla(self, file, cla):
        if type(file) == list:
            file = toHexString(file,1)
        if type(cla) == int:
            cla = f'{cla:02x}'
        try:
            if not self.card[file]["commands"].get(cla):
                self.card[file]["commands"][cla] = []
        except:
            pdb.set_trace()
        return

    def remove_cla(self, file, cla):
        if type(file) == list:
            file = toHexString(file,1)
        if type(cla) == int:
            cla = f'{cla:02x}'
        self.card[file]["commands"].pop(cla)
        return

    def get_file_list(self):
        return list(self.card.keys())

    def get_file(self, file):
        if type(file) == list:
            file = toHexString(file,1)
        return self.card.get(file)
    
    def add_file(self, file, file_type, file_data="", records={}, commands={}):
        if type(file) == list:
            file = toHexString(file,1)
        if file_type not in ["name", "id", "path"]:
            raise ValueError('The method of file selection is not one of: name, id, path')
        if not self.card.get(file):
            self.card[file] = {
                                    "ef_data":file_data,
                                    "file_select_method":file_type,
                                    "records":records,
                                    "commands":commands
                                  }
        return

    def remove_file(self,file):
        if type(file) == list:
            file = toHexString(file,1)
        self.card.pop(file)
        return

    def get_file_data(self, file):
        if type(file) == list:
            file = toHexString(file,1)
        return self.card[file].get("ef_data")
    
    def get_file_type(self, file):
        if type(file) == list:
            file = toHexString(file,1)
        return self.card[file].get("file_select_method")
    
    def set_file_data(self, file, data):
        if type(file) == list:
            file = toHexString(file,1)
        self.card[file]["ef_data"] = data
        return
    
    def get_ins_list(self, file, cla):
        if type(file) == list:
            file = toHexString(file,1)
        if type(cla) == int:
            cla = f'{cla:02x}'
        ins_list = self.card[file]["commands"].get(cla)
        return [] if not ins_list else ins_list
    
    def add_ins(self, file, cla, ins):
        if type(file) == list:
            file = toHexString(file,1)
        if type(cla) == int:
            cla = f'{cla:02x}'
        if type(ins) == int:
            ins = f'{ins:02x}'
        if ins not in self.card[file]["commands"][cla]:
            self.card[file]["commands"][cla].append(ins)
        return
    
    def remove_ins(self, file, cla, ins):
        if type(file) == list:
            file = toHexString(file,1)
        if type(cla) == int:
            cla = f'{cla:02x}'
        if type(ins) == int:
            ins = f'{ins:02x}'
        self.card[file]["commands"][cla].remove(ins)
        return
    
    def get_record_list(self, file):
        if type(file) == list:
            file = toHexString(file,1)
        return self.card[file]["records"].items()
    
    def get_record(self, file, record_id):
        if type(file) == list:
            file = toHexString(file,1)
        return self.card[file]["records"].get(record_id)
    
    def set_record(self, file,record_id, data):
        if type(file) == list:
            file = toHexString(file,1)
        self.card[file]["records"][record_id] = data
        return
    
    def remove_record(self, file, record_id):
        if type(file) == list:
            file = toHexString(file,1)
        self.card[file]["records"].pop(record_id)
        return