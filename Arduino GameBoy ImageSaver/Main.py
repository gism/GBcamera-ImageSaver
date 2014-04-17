import sys
from arduinoSerial import openArduinoSerial
from imgBMP import ThreadSaveImage
import Queue
import conf

white = {'r' : 255, 'g' : 255, 'b' : 255} 
lgrey = {'r' : 200, 'g' : 200, 'b' : 200}
dgrey = {'r' : 128, 'g' : 128, 'b' : 128}
black = {'r' : 0, 'g' : 0, 'b' : 0}

def gbColor(code):
    if code == 0:
        return white
    elif code == 1:
        return lgrey
    elif code == 2:
        return dgrey
    elif code == 3:
        return black
    else:
        return -1

def getColors(sData):
    # Data is a string value unsigned byte.
    pxData = []
    iData = int(sData)
    if iData > 255 or iData < 0:
        return -1
    for i in range(4):
        pxColor = iData % 2
        iData = iData >> 1
        pxColor = pxColor + (iData % 2) * 2
        iData = iData >> 1
        pxData.append(gbColor(pxColor))
    pxData.reverse() 
    return pxData

def attachMatrix(matrix, dots):
    for dot in dots:
        matrix.append(dot)
    return matrix

def dec2bin(iDec):
    # 1-Byte max
    sByte = ""
    for i in range(8):
        sBit = str(iDec % 2)
        iDec = iDec >> 1
        sByte = sBit + sByte
    return sByte

def getBrand(dataBody):
    i=0
    imgBrand = []
    while i<len(dataBody):
        try:
            sByte1 = dec2bin(int(dataBody[i]))
            sByte2 = dec2bin(int(dataBody[i+1]))
            
            for b in range(8):
                dot = int(sByte1[b]) + 2 * int(sByte2[b])
                imgBrand.append(gbColor(dot))
            i = i+2
        except:
            print "ERROR: getBrand()"
            print dataBody
            break
    return imgBrand

try:
    ardSerial = openArduinoSerial()
except:
    print ("ERROR: Unable to open Serial PORT.")
    sys.exit()

def stateMachine(): 
    
    # Launch save image Thread, Necesita optimizar
    gbImage=Queue.Queue()
    saveImage = ThreadSaveImage(gbImage)
    saveImage.start()
    f = open(conf.FOLDER + "\log.txt", "w")
    f.close
    f = open(conf.FOLDER + "\log.txt", "a")
    printCmd = 0
    while True:
        GBresponse = ardSerial.readline()
        GBresponse = GBresponse.replace("\r\n", "")
        
        # Uncomment to see GB => PC data.
        log = "stateMachineCmd: \t" + str(printCmd) + "\t | Data: \t" + str(GBresponse)                  
        print>>f, log 
        print "stateMachineCmd: \t", printCmd, "\t | Data: \t", GBresponse
        
        if (printCmd ==0):
            # Acknowledge Byte 1 (Must be 0x88).
            if(GBresponse == str(136)):
                printCmd = 1
            elif(GBresponse =="?"):
                ardSerial.write("!")
            else:
                printCmd = 0
                
        elif (printCmd==1):
            # Acknowledge Byte 2 (Must be 0x33).
            if(GBresponse == str(51)):
                printCmd=2
            else:
                printCmd= 0
                
        elif (printCmd ==2):
            # GBcommand code:
            # =====================
            # 0x01 (1) = Initialize   [NO DATA]
            # 0x02 (2) = Print        [DATA = 0x1?]
            # 0x03 (3) = Unknown
            # 0x04 (4) = Data         [160x16 px]   
            # 0x0F (15) = Inquiry     [NO DATA]
            if (GBresponse == str(1)):
                printCmd = 3
            elif (GBresponse == str(2)):
                printCmd = 50
            elif (GBresponse == str(4)):
                printCmd = 20
            elif (GBresponse == str(15)):
                printCmd = 90
            else:
                printCmd = 0
                
        elif (printCmd == 3):
            # Initialize sequence - Compression byte
            printCmd = 4
            
        elif (printCmd == 4):
            # Initialize sequence - Data Length LSB (Must be 0).
            printCmd = 5
            
        elif (printCmd == 5):
            # Initialize sequence - Data Length MSB (Must be 0).
            printCmd = 6
            
        elif (printCmd == 6):
            # Initialize sequence - Checksum LSB (Must be 0).
            printCmd = 7
            
        elif (printCmd == 7):
            # Initialize sequence - Checksum MSB (Must be 0).
            printCmd = 8
            
        elif (printCmd == 8):
            # Initialize sequence - Acknowledgement code (Arduino to GB: Must be 0x80 or 0x81).
            printCmd = 9
            
        elif (printCmd == 9):
            # Initialize sequence - Status Code
            # Print Status code
            # =============================
            # 0000 0000 = Normal status
            # 1XXX XXXX = Error#1: Low batteries
            # X1XX XXXX = Error#4: Heat level at the printing head is unusual (too hot or too cold)
            # XX1X XXXX = Error#3: Paper jam
            # XXXX 1XXX = Ready to print
            # XXXX X1XX = Print request
            # XXXX XX1X = Printer busy
            # XXXX XXX1 = Bad checksum
            printCmd = 0   
        
        elif (printCmd == 20):
            # Data sequence - Compression byte        
            printCmd = 21
            
        elif (printCmd == 21):
            # Data sequence - Body length LSB
            bodyLength = int(GBresponse)
            printCmd = 22
            
        elif (printCmd == 22):
            # Data sequence - Body length LSB
            bodyLength = bodyLength + int(GBresponse) * 256
            i = 1
            gbBand = []
            bodyData = []
            printCmd = 23
        
        elif (printCmd == 23):
            # Data body
            bodyData.append(GBresponse)
            if (i < bodyLength):
                i= i + 1
            else:
                printCmd = 24        
        
        elif (printCmd == 24):
            if (len(bodyData)==640):
                gbBand = getBrand(bodyData)
            if (len(gbBand)==2560):
                gbImage.put(gbBand)
            printCmd = 0
                            
        elif (printCmd == 50):
            # Print sequence - Compression byte
            printCmd = 51
            
        elif (printCmd == 51):
            # Print sequence - Body length LSB
            bodyLength = int(GBresponse)
            printCmd = 52
            
        elif (printCmd == 52):
            # Print sequence - Body length LSB
            # Body data on a print command is always 0x04h.
            bodyLength = bodyLength + int(GBresponse) * 256
            printCmd = 53
            
        elif (printCmd == 53):
            # Print sequence - Unknown byte, it's always 0x01. 
            printCmd = 54
        
        elif (printCmd == 54):
            # Print sequence - Margins. 
            upperMargin = int(GBresponse) // 16
            lowerMargin = int(GBresponse) - upperMargin * 16
            printCmd = 55
            
        elif (printCmd == 55):
            # Print sequence - Palette. 
            imgPalette = GBresponse
            printCmd = 56
            
        elif (printCmd == 56):
            # Print sequence - "Ink" density or heater power. 
            imgPalette = GBresponse
            printCmd = 57
            
        elif (printCmd == 57):
            # Print sequence - Checksum LSB. 
            printCmd = 58
            
        elif (printCmd == 58):
            # Print sequence - Checksum MSB. 
            printCmd = 0
            
        elif (printCmd == 90):
            # Inquiry command - Compression byte
            printCmd = 91
            
        elif (printCmd == 91):
            printCmd = 0
            
        else:
            printCmd = 0
            print("ERROR: flow error")
            
def main():
    try:
        stateMachine()
    except:
        ardSerial.close()

if __name__ == "__main__":
    main()