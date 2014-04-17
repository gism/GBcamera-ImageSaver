import serial, glob
import platform

arduinoBaudrate = 115200    # Arduino Serial baudrate.
TOUT = 7                    # Serial timeout in seconds.

# ===========================================
# Detect Serial ports
# ===========================================

#Only list serial for windows.
def listSerialWin():
    # Scan for available ports. Return a list of tuples (num, name)
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append( (i, s.portstr))
            s.close()
        except serial.SerialException:
            pass
    return available

#Cross plataform
def listSerial():
    system_name = platform.system()
    if system_name == "Windows":
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append(i)
                s.close()
            except serial.SerialException:
                pass
        return available
    elif system_name == "Darwin":
        # Mac
        return glob.glob('/dev/tty*') + glob.glob('/dev/cu*')
    else:
        # Assume Linux or something else
        return glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

# ===========================================
# / Detect Serial ports
# ===========================================

def arduinoSerialPort():
    # This function should return the COM port where arduino es connected:
    
    expectedResponse = "GameBoy ImageSaver"
    
    detectedPorts = listSerial()
    for comPort in detectedPorts:
        candidatePort = serial.Serial(comPort, arduinoBaudrate, timeout = TOUT)
        print "Checking port: " + candidatePort.portstr + " (" + str(comPort) + ")"
        firstRead = candidatePort.readline()
        if (firstRead == ""):
            print "No response from: " + candidatePort.portstr + " (" + str(comPort) + ")"
        elif (firstRead.find(expectedResponse)!=-1):
            print "Arduino GameBoy ImageSaver found on: " + candidatePort.portstr + " (" + str(comPort) + ")"
            return comPort
        else:
            print "NOT found on: " + candidatePort.portstr + " (" + str(comPort) + ")"
    return -1

def openArduinoSerial():
    comPort = arduinoSerialPort()
    if comPort != -1:
        try:
            s = serial.Serial(comPort, arduinoBaudrate)
        except:
            print "Error: On serial connection."
    else:
        print "Error: Unable to connect with GameBoy Printer."
    return s