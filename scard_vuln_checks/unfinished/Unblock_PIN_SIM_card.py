from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, NoReadersException, CardConnectionException
import sys
sys.path.insert(0, '/home/ghost/wubblegum2/wubblegum/')
from apdu_utils.file_enum import find_files_by_id, find_files_by_path, find_files_by_name, find_files_by_wordlist



def unblock_pin(reader):

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

    command0 = [0x00, 0x2C, 0x00, 0x01]

    try :

        data, sw1, sw2 = connection.transmit(command0)

        if sw1 == 0x90 or sw1 == 0x91 or sw1 == 0x92:
            print("\nUnblock PIN was successful!: " + toHexString( command0 ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])) + ", data= " + str([data]))
        
        elif sw1 == 0x63 and sw2 == 0xF1:
            print("\nUnblock PIN was unsuccessful, with more data being expected : " + toHexString( command0 ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))
    

        elif sw1 == 0x63 and sw2 == 0xF2:
            print("\nUnblock PIN was unsuccessful, with more data being expected with a proactive commmand pending : " + toHexString( command0 ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))
    

        elif sw1 == 0x63:
            print("\nUnblock PIN was successful, with there being 'X' retries left as indicated by SW2 = 'CX'. \n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))

        else: 
            print("\nUnblock PIN was unsuccessful!! : " + toHexString( command0 ) + "\n")
            print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])))
    
    except CardConnectionException :
            pass

if __name__ == "__main__":
    unblock_pin()
