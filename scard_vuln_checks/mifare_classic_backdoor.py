from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, NoReadersException
from apdu_utils import mifare_sector_read



def load_and_auth_default_keys(reader):

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


    
    default_keys = [[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], 
                    [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5], 
                    [0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5], 
                    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]]

    #load key
    load_key = [0xFF, 0x82, 0x20, 0x00, 0x06]
    #auth using key
    general_auth = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01,0x00,0x00,0x60,0x00]

    successful_loading_counter = 0
    successful_authentication_counter = 0

    print("\nDEFAULT KEYS LOADED AND AUTHENTICATED:\n")
    
    for i in default_keys:

        command1 = load_key + i
        data, sw1, sw2 = connection.transmit(command1)
        
        if sw1 == 0x90 or sw1 == 0x61:
            #print("\nThe key was loaded successfully : " + toHexString( command1 ) + "\n")
            successful_loading_counter+=1
            #if select command works, then disable the verification
            #print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])) + ", data= " + str([data]))
            
            command2=general_auth + []
            
            data2, sw1_2, sw2_2 = connection.transmit(command2)

            if sw1_2 == 0x90 or sw1_2 == 0x61:
                print("\nThe key authenticated successfully : " + toHexString( command2 ) + "\n")
                successful_authentication_counter+=1
                #print("sw1 = " + str(toHexString([sw1_2])) + ", sw2 = " + str(toHexString([sw2_2])) + ", data= " + str([data2]))
              
                #Start checking sector read
                mifare_sector_read.mifare_sector_read(connection) 
            else: 
                print(f"\rThe key authentication was unsuccessful! : {toHexString( command2 )}",end='',flush=True)
               # print("sw1 = " + str(toHexString([sw1_2])) + ", sw2 = " + str(toHexString([sw2_2])) + ", data= " + str([data2]))
        else:
            print(f"\rUnfortunately the key did not successfully load!: {toHexString( command1 )}",end='',flush=True)
        #    print([sw1] + [sw2] + [data])
            break

    print("\n\nDEFAULT KEY COUNT:")
    print("\nSuccessful key loading: " + str(successful_loading_counter))
    print("Successful attempts at authentication: " + str(successful_authentication_counter))

    

def load_and_auth_backdoor_keys(reader):

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
    

    backdoor_keys = [[0xA3, 0x96, 0xEF, 0xA4, 0xE2, 0x4F],
                    [0xA3, 0x16, 0x67, 0xA8, 0xCE, 0xC1], 
                    [0x51, 0x8B, 0x33, 0x54, 0xE7, 0x60]]
    
    #load key
    load_key = [0xFF, 0x82, 0x20, 0x00, 0x06]
    
    #auth using key
    general_auth = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x00, 0x60, 0x00]

    successful_loading_counter = 0
    successful_authentication_counter = 0

    print("\n\nBACKDOOR KEYS LOADED AND AUTHENTICATED:\n")
    
    for i in backdoor_keys:
        command1 = load_key + i
        data, sw1, sw2 = connection.transmit(command1)
        
        if sw1 == 0x90 or sw1 == 0x61:
            #print("\nThe key was loaded successfully : " + toHexString( command1 ) + "\n")
            successful_loading_counter+=1
        #if select command works, then disable the verification
            #print("sw1 = " + str(toHexString([sw1])) + ", sw2 = " + str(toHexString([sw2])) + ", data= " + str([data]))
            
            command2=general_auth 
            
            data2, sw1_2, sw2_2 = connection.transmit(command2)

            if sw1_2 == 0x90 or sw1_2 == 0x61:
                print("\nThe key authenticated successfully : " + toHexString( command2 ) + "\n")
                #print("sw1 = " + str(toHexString([sw1_2])) + ", sw2 = " + str(toHexString([sw2_2])) + ", data= " + str([data2]))
                successful_authentication_counter+=1
                #Start checking sector read
                mifare_sector_read.mifare_sector_read(connection) 
            else: 
                print(f"\rThe key authentication was unsuccessful! : {toHexString( i )}",end='',flush=True)
               # print("sw1 = " + str(toHexString([sw1_2])) + ", sw2 = " + str(toHexString([sw2_2])) + ", data= " + str([data2]))
        else:
            print(f"\rUnfortunately the key did not successfully load!: {toHexString( command1 )}",end='',flush=True)
           # print([sw1] + [sw2] + [data])
            break
           

    print("\n\nBACKDOOR KEY COUNT:")
    print("\nSuccessful key loading: " + str(successful_loading_counter))
    print("Successful attempts at authentication: " + str(successful_authentication_counter))

if __name__ == "__main__":
    load_and_auth_default_keys()
    load_and_auth_backdoor_keys()