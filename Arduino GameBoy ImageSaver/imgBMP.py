#!/usr/bin/python
import struct, random
import threading, Queue
import conf

# modified from http://pseentertainmentcorp.com/smf/index.php?topic=2034.0

# important values: offset, headerlength, width, height and colordepth
# This is for a Windows Version 3 DIB header
# You will likely want to customize the width and height
default_bmp_header = {'mn1':66,             # B
                      'mn2':77,             # M
                      'filesize':0,
                      'undef1':0,
                      'undef2':0,
                      'offset':54,          # 6 (36h)
                      'headerlength':40,    # (
                      'width':200,
                      'height':200,
                      'colorplanes':0,
                      'colordepth':24,      # CAN
                      'compression':0,
                      'imagesize':0,
                      'res_hor':0,
                      'res_vert':0,
                      'palette':0,
                      'importantcolors':0}

def bmp_write(header, pixels, filename):
    '''It takes a header (based on default_bmp_header), 
    the pixel data (from structs, as produced by get_color and row_padding),
    and writes it to filename'''
    header_str = ""
    header_str += struct.pack('<B', header['mn1'])
    header_str += struct.pack('<B', header['mn2'])
    header_str += struct.pack('<L', header['filesize'])
    header_str += struct.pack('<H', header['undef1'])
    header_str += struct.pack('<H', header['undef2'])
    header_str += struct.pack('<L', header['offset'])
    header_str += struct.pack('<L', header['headerlength'])
    header_str += struct.pack('<L', header['width'])
    header_str += struct.pack('<L', header['height'])
    header_str += struct.pack('<H', header['colorplanes'])
    header_str += struct.pack('<H', header['colordepth'])
    header_str += struct.pack('<L', header['compression'])
    header_str += struct.pack('<L', header['imagesize'])
    header_str += struct.pack('<L', header['res_hor'])
    header_str += struct.pack('<L', header['res_vert'])
    header_str += struct.pack('<L', header['palette'])
    header_str += struct.pack('<L', header['importantcolors'])
    #create the outfile
    outfile = open(filename, 'wb')
    #write the header + pixels
    outfile.write(header_str + pixels)
    outfile.close()

def row_padding(width, colordepth):
    '''returns any necessary row padding'''
    byte_length = width*colordepth/8
    # how many bytes are needed to make byte_length evenly divisible by 4?
    padding = (4-byte_length)%4 
    padbytes = ''
    for i in range(padding):
        x = struct.pack('<B',0)
        padbytes += x
    return padbytes

def pack_color(red, green, blue):
    '''accepts values from 0-255 for each value, returns a packed string'''
    return struct.pack('<BBB',blue,green,red)

def pack_hex_color(hex_color):
    '''accepts RGB hex colors like '#ACE024', returns a packed string'''
    base = 16
    red = int(hex_color[1:3], base)
    green = int(hex_color[3:5], base)
    blue = int(hex_color[5:7], base)
    return pack_color(red, green, blue)
    

###################################    
def test():
    header = default_bmp_header
    header["width"] = 255
    header["height"] = 255
    #Function to generate a random number between 0 and 255
    def rand_color():
        x = random.randint(0,255)
        return x

    #Build the byte array.  This code takes the height
    #and width values from the dictionary above and
    #generates the pixels row by row.  The row_padding
    #stuff is necessary to ensure that the byte count for each
    #row is divisible by 4.  This is part of the specification.
    pixels = ''
    i=255
    for row in range(header['height']-1,-1,-1):# (BMPs are L to R from the bottom L row)
        j=255
        for column in range(header['width']):
            r = rand_color()
            r=j
            g = rand_color()
            g=i
            b = rand_color()
            b=i
            pixels = pixels + pack_color(r, g, b)
            j=j-1
        i=i-1
        pixels += row_padding(header['width'], header['colordepth'])
            
    #call the bmp_write function with the
    #dictionary of header values and the
    #pixels as created above.
    bmp_write(header, pixels, conf.FOLDER + "\test.bmp")

def reorderBrand(pxSequence):
    a=[]
    for i in xrange(16):
        a.append([])
        for j in xrange(160):
            a[i].append([])
    
    for row in xrange(2):
        for tile in xrange(20):
            for i in xrange(8):
                for j in xrange(8):
                    a[i + row * 8][j + tile*8]=pxSequence[row *1280 + tile * 64 + 8 * i + j]
    return a

def checkFilename(filenameRoot):
    
    i=0
    filename = filenameRoot + str(i) + ".BMP"
    
    while(1):
        try:
            with open(filename) as f: pass
            i = i + 1
            filename = filenameRoot + str(i) + ".BMP"
        except:
            return filename
    
def saveMatrix(iMatrix):
    
    header = default_bmp_header
    header["width"] = 160
    header["height"] = 16
    
    # iMatrix = reorderBrand(iMatrix)
       
    pixels = ''
    for row in range(header['height']-1,-1,-1): #(BMPs are L to R from the bottom L row to top R row)
        for column in range(header['width']):
            red = iMatrix[row][column]['r']
            green = iMatrix[row][column]['g']
            blue = iMatrix[row][column]['b']
            pixels = pixels + pack_color(red, green, blue)
        pixels += row_padding(header['width'], header['colordepth'])
    imagePath = checkFilename(conf.FOLDER + "\GBimage")
    bmp_write(header, pixels, imagePath)

def saveImage(iMatrix):
    
    header = default_bmp_header
    header["width"] = 160
    header["height"] = 144
    
    pixels = ''
    for row in range(header['height']-1,-1,-1): # (BMPs are L to R from the bottom L row to top R row)
        for column in range(header['width']):
            try:
                red = iMatrix[row][column]['r']
                green = iMatrix[row][column]['g']
                blue = iMatrix[row][column]['b']
                pixels = pixels + pack_color(red, green, blue)
            except:
                red = 255
                green = 0
                blue = 00
                pixels = pixels + pack_color(red, green, blue)
                print "ERROR:"
                print iMatrix[row][column]                                      
        pixels += row_padding(header['width'], header['colordepth'])
    imagePath = checkFilename(conf.FOLDER + "\GBimage")
    bmp_write(header, pixels, imagePath)
    
class ThreadSaveImage(threading.Thread):
    """Threaded Url Grab"""
    
    def __init__(self, gbImageQueue):
        threading.Thread.__init__(self)
        self.gbImageQueue = gbImageQueue
                 
    def run(self):
        gbImage = []
        i=0
        while True:
            qData = self.gbImageQueue.get(True)
            if qData=='KILL':
                break                
            brand = qData
            
            try:
                brand = reorderBrand(brand)
            except:
                print "Error: reorderBrand"
                print brand
            for a in brand:
                gbImage.append(a)
            i = i + 1
            if(i==9):
                saveImage(gbImage)
                gbImage = []
                i=0
