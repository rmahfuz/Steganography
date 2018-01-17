import re
import base64
import zlib
#from PIL import Image
from imageio import imread
import numpy as np

#######################################################################################################################
class Payload:
    def __init__(self, rawData = None, compressionLevel = -1, json = None):
        #----------------------------------------------------------------------------------
        if (compressionLevel < -1 or compressionLevel > 9):
            raise ValueError("compressionLevel is invalid")
        if (not isinstance(rawData, np.ndarray)):
            if rawData != None:
                raise TypeError("Unexpected type for rawData")
        if (not isinstance(json, str)):
            if json != None:
                raise TypeError("Unexpected type for json")
        if (not isinstance(rawData, np.ndarray)) and (not isinstance(json, str)):
            raise ValueError("Neither json nor rawData is provided")
        #----------------------------------------------------------------------------------
        self.compressionLevel = compressionLevel
        if isinstance(rawData, np.ndarray):
            if rawData.dtype != np.uint8:
                raise ValueError('rawData should be of type uint8')
            self.rawData = rawData
            self.genJson()
        elif isinstance(json, str):
            self.json = json
            self.genRawData()
        #----------------------------------------------------------------------------------
        self.afterRasterScan = 0
        self.afterDataCompress = 0
        self.afterBase64Encode = 0
        self.type_from_json = ''
        self.size_from_json = ''
        self.isCompressed_from_json = True
    #=================================================================================================================
    def genJson(self):
        self.rasterScan()
        self.dataCompress()
        self.base64Encode()
        self.jsonSerialize()
    #=================================================================================================================
    def genRawData(self):
        self.jsonParse()
        self.base64Decode()
        self.dataDecompress()
        self.compose()
    #=================================================================================================================
    def jsonParse(self): #uses self.json to populate self.afterBase64Encode
        matched = re.match(r'{"type":"(?P<type_from_json>[\w]*)","size":(?P<size_from_json>.*?),"isCompressed":(?P<isCompressed_from_json>.*?),"content":"(?P<content_from_json>.*?)"', self.json)
        self.type_from_json = matched.group('type_from_json')
        self.size_from_json = matched.group('size_from_json')
        if matched.group('isCompressed_from_json') == 'true':
            self.isCompressed_from_json = True
        if matched.group('isCompressed_from_json') == 'false':
            self.isCompressed_from_json = False
        self.afterBase64Encode = matched.group('content_from_json')
    #=================================================================================================================
    def base64Decode(self): #uses self.afterBase64Encode to populate self.afterDataCompress
        self.afterDataCompress = base64.b64decode(self.afterBase64Encode)
    #=================================================================================================================
    def dataDecompress(self): #uses self.afterDataCompress to populate self.afterRasterScan
        if self.isCompressed_from_json == True:
            self.afterRasterScan = zlib.decompress(self.afterDataCompress)
        else:
            self.afterRasterScan = self.afterDataCompress
        self.afterRasterScan = np.fromstring(self.afterRasterScan, dtype = np.uint8)
    #=================================================================================================================
    def compose(self): #uses self.afterRasterScan to populate self.rawData
        if self.type_from_json == 'color':
            self.afterRasterScan.resize((int(self.size_from_json.split(',')[0][1:]), int(self.size_from_json.split(',')[1][:len(self.size_from_json.split(',')[1]) - 1]), 3))
            self.rawData = self.afterRasterScan
        elif self.type_from_json == 'gray':
            self.afterRasterScan.resize((int(self.size_from_json.split(',')[0][1:]), int(self.size_from_json.split(',')[1][:len(self.size_from_json.split(',')[1]) - 1])))
            self.rawData = self.afterRasterScan
        elif self.type_from_json == 'text':
            self.rawData = self.afterRasterScan
        self.rawData = np.array(self.rawData, dtype = np.uint8)
    #=================================================================================================================
    def rasterScan(self): #uses self.rawData to populate self.afterRasterScan
        self.afterRasterScan = self.rawData
        self.afterRasterScan.flatten()
    #=================================================================================================================
    def dataCompress(self): #uses self.afterRasterScan to populate self.afterDataCompress
        if self.compressionLevel == -1:
            self.afterDataCompress = self.afterRasterScan
        else:
            self.afterDataCompress = zlib.compress(self.afterRasterScan, self.compressionLevel)
    #=================================================================================================================
    def base64Encode(self): #uses self.afterDataCompress to populate self.afterBase64Encode
        self.afterBase64Encode = base64.b64encode(self.afterDataCompress)
    #=================================================================================================================
    def jsonSerialize(self): #uses self.afterBase64Encode to populate self.json
        if (len(self.rawData.shape) == 1):
            type_to_set = 'text'
            size_to_set = 'null'
        elif (len(self.rawData.shape) == 2):
            type_to_set = 'gray'
            size_to_set = '"' + str(self.rawData.shape[0]) + ',' + str(self.rawData.shape[1]) + '"'
        elif (len(self.rawData.shape) == 3 and self.rawData.shape[2] == 3):
            type_to_set = 'color'
            size_to_set = '"' + str(self.rawData.shape[0]) + ',' + str(self.rawData.shape[1]) + '"'
        else:
            raise TypeError('self.rawData is not of a valid type!!')
        
        isCompressed_to_set = (self.compressionLevel != -1)
        if isCompressed_to_set == True:
            isCompressed_to_set = 'true'
        else:
            isCompressed_to_set = 'false'
        content_to_set = str(self.afterBase64Encode)
        content_to_set = content_to_set[2:len(content_to_set) - 1]
        self.json = '{"type":"' + type_to_set + '","size":' + size_to_set + ',"isCompressed":' +  isCompressed_to_set + ',"content":"' + str(content_to_set) + '"}'
    #=================================================================================================================

#######################################################################################################################
class Carrier:
    #=================================================================================================================
    def __init__(self, img):
        if (not isinstance(img, np.ndarray)):
            raise TypeError("img should be a numpy array")
        elif len(img.shape) < 3:
            raise ValueError("Number of dimensions of img should not be less than 3")
        elif img.shape[2] < 4:
            raise ValueError("Each pixel of img must have 4 dimensions")
        elif img.dtype != np.uint8:
            raise TypeError('img should be a numpy array of type np.uint8')
        else:
            self.img = img
    #=================================================================================================================
    def payloadExists(self): #returns either True or False
        #carrier = copy.deepcopy(self.img)
        carrier = np.copy(self.img)
        carrier = carrier.flatten()
        carrier.__iand__(3)
        how_big = 80
        idx = np.arange(how_big)
        idx.__imul__(4)
        idx = np.repeat(idx, 4)
        idx.__iadd__([3,2,1,0]*how_big)
        pay = np.take(carrier, idx) #how_big * 4
        pay = np.repeat(pay, 2) #how_big * 8
        pay.__iand__(np.array([2, 1] * (how_big * 4), dtype = np.uint8))
        pay.__irshift__(np.array([1, 0] * (how_big * 4), dtype = np.uint8))
        pay = np.packbits(pay)
        pay = pay.tostring()
        matched = re.match(r'{"type":"(?P<type_from_json>[\w]*)","size":(?P<size_from_json>.*?),"isCompressed":(?P<isCompressed_from_json>.*?),"content":"', str(pay)[2:-1])
        if matched == None:
            return False
        else:
            return True
    #=================================================================================================================
    def embedPayload(self, payload, override = False):
        if type(payload) != Payload:
            raise TypeError('The payload parameter must be an instance of the class Payload') 
        if len(payload.json) > (self.img.shape[0] * self.img.shape[1]):
            raise ValueError('Payload size is larger than what the carrier can hold')
        if override == False and self.payloadExists():
            raise Exception("Current carrier already contains a payload")
        #----------------------------------------------------------------------------------
        to_ret0 = np.copy(self.img)
        to_ret = np.copy(self.img)
        to_ret0.resize(self.img.shape[0] * self.img.shape[1] * self.img.shape[2])
        to_ret.resize(self.img.shape[0] * self.img.shape[1] * self.img.shape[2])
        json_arr = np.fromstring(payload.json, dtype = np.uint8) #array of numbers
        j = np.unpackbits(json_arr)
        even = np.arange(0, len(j), 2)
        odd = np.arange(1, len(j), 2)
        bin_list = (np.take(j, even).__ilshift__(1)).__or__(np.take(j, odd))
        how_big = int(len(bin_list)/4)
        idx = np.arange(how_big)
        idx.__imul__(4)
        idx = np.repeat(idx, 4)
        idx.__iadd__([3,2,1,0]*how_big)
        bin_list = np.take(bin_list, idx)
        tmp = to_ret.__irshift__(2)
        tmp2 = tmp.__ilshift__(2)[0:len(bin_list)]
        to_ret = tmp2.__ior__(bin_list)
        to_ret = np.append(to_ret, to_ret0[len(payload.json)*4:])
            
        to_ret = to_ret.reshape(self.img.shape[0], self.img.shape[1], 4)
        return to_ret
    #=================================================================================================================
    def clean(self): #returns a new np.ndarray
        to_ret =  np.copy(self.img)
        to_ret = to_ret.flatten()
        to_ret.__irshift__(2)
        to_ret.__ilshift__(2)
        ran_nums = np.array(np.random.random_integers(0, 3, len(to_ret)), dtype = np.uint8)
        to_ret.__ior__(ran_nums)
        to_ret.resize(self.img.shape[0], self.img.shape[1], self.img.shape[2])
        return to_ret
    #=================================================================================================================
    def extractPayload(self): #returns an instance of Payload
        if self.payloadExists() == False:
            raise ValueError('There is no payload embedded in the carrier')
        carrier = np.copy(self.img)
        carrier = carrier.flatten()
        carrier.__iand__(3)
        how_big = self.img.shape[0] * self.img.shape[1]
        idx = np.arange(how_big)
        idx.__imul__(4)
        idx = np.repeat(idx, 4)
        idx.__iadd__([3,2,1,0]*how_big)
        pay = np.take(carrier, idx) #how_big * 4
        pay = np.repeat(pay, 2) #how_big * 8
        pay.__iand__(np.array([2, 1] * (how_big * 4), dtype = np.uint8))
        pay.__irshift__(np.array([1, 0] * (how_big * 4), dtype = np.uint8))
        pay = np.packbits(pay)
        pay = pay.tostring()
        to_ret = Payload(None, -1, str(pay)[2:-1])
        return to_ret
    #=================================================================================================================

#######################################################################################################################
if __name__ == "__main__":
    """
    #==========Testing Payload:=======================================================================================
    #pay1 = np.asarray(Image.open('data/payload1.png')) #reading rawData1
    pay1 = imread('data/payload1.png') #reading rawData1
    pay1_ins = Payload(pay1, -1, None)
    with open("data/payload1.json", 'r') as to_read:
        json1 = to_read.read()
    print(json1 == pay1_ins.json)
    #----------------------------------------------------------------------------------
    with open('data/payload1.json', 'r') as to_read: #reading json1
        json1 = to_read.read()
    json1_ins = Payload(None, -1, json1)
    #=================================================================================================================
    #pay2 = np.asarray(Image.open('data/payload2.png')) #reading rawData2
    pay2 = imread('data/payload2.png') #reading rawData2
    pay2_ins = Payload(pay2, 7, None)
    #print(pay2_ins.json)
    #----------------------------------------------------------------------------------
    with open('data/payload2.json', 'r') as to_read: #reading json2
        json2 = to_read.read()
    json2_ins = Payload(None, 7, json2)
    #print(json2_ins.rawData)
    #=================================================================================================================
    with open('data/payload3.txt', 'r') as to_read: #reading rawData3
        content = to_read.read()
    pay3 = np.fromstring(content, dtype=np.uint8)
    pay3_ins = Payload(pay3, 5, None)
    #print(pay3_ins.json)
    #----------------------------------------------------------------------------------
    with open('data/payload3.json', 'r') as to_read: #reading json3
        json3 = to_read.read()
    json3_ins = Payload(None, 5, json3)
    #print(json3_ins.rawData)
    #=================================================================================================================
    #=========Testing Carrier's Embed=================================================================================
    """
    car = imread('data/embedded1_-1.png') #reading carrier
    car_ins = Carrier(car)
    pay1 = imread('data/payload1.png') #reading rawData1
    pay1_ins = Payload(pay1, -1, None)
    embedded_pay1 = car_ins.embedPayload(pay1_ins, True)
    embedded_pay1_sample = imread('data/embedded1_-1.png') #reading carrier
    print(np.array_equal(embedded_pay1, embedded_pay1_sample))
    #ans = (embedded_pay1 == embedded_pay1_sample)
    #print(np.extract((ans == False), ans))
    """
    #=================================================================================================================
    car = imread('data/carrier.png') #reading carrier
    car_ins = Carrier(car)
    pay2 = imread('data/payload2.png') #reading rawData2
    pay2_ins = Payload(pay2, 7, None)
    embedded_pay2 = car_ins.embedPayload(pay2_ins)
    embedded_pay2_sample = imread('data/embedded2_7.png') #reading carrier
    print('answer = ', embedded_pay2 == embedded_pay2_sample)
    #=================================================================================================================
    car = imread('data/carrier.png') #reading carrier
    car_ins = Carrier(car)
    with open('data/payload3.txt', 'r') as to_read: #reading rawData3
        content = to_read.read()
    pay3 = np.fromstring(content, dtype=np.uint8)
    pay3_ins = Payload(pay3, 5, None)
    embedded_pay3 = car_ins.embedPayload(pay3_ins)
    embedded_pay3_sample = imread('data/embedded3_5.png') #reading carrier
    print('answer = ', embedded_pay3 == embedded_pay3_sample)
    #=================================================================================================================
    #=====Testing Carrier's Extract===================================================================================
    embedded_pay1 = imread('data/embedded1_-1.png') #reading carrier embedded with payload1
    car_ins = Carrier(embedded_pay1)
    pay1_result = car_ins.extractPayload()
    pay1 = imread('data/payload1.png') #reading rawData1
    print(np.array_equal(pay1, pay1_result.rawData))
    #print('answer = ', pay1_result.rawData == pay1)
    #=================================================================================================================
    embedded_pay2 = imread('data/embedded2_7.png') #reading carrier embedded with payload2
    car_ins = Carrier(embedded_pay2)
    pay2_result = car_ins.extractPayload()
    pay2 = imread('data/payload2.png') #reading rawData2
    print('answer = ', pay2_result.rawData == pay2)
    #=================================================================================================================
    embedded_pay3 = imread('data/embedded3_5.png') #reading carrier embedded with payload3
    car_ins = Carrier(embedded_pay3)
    pay3_result = car_ins.extractPayload()
    print('done extracting')
    with open('data/payload3.txt', 'r') as to_read: #reading rawData3
        content = to_read.read()
    pay3 = np.fromstring(content, dtype=np.uint8)
    print('answer = ', pay3_result.rawData == pay3)
    #=================================================================================================================
    embedded_pay1 = imread('data/embedded1_-1.png') #reading carrier embedded with payload1
    car_ins = Carrier(embedded_pay1)
    print(car_ins.clean() == embedded_pay1)
    expectedValue = imread("data/embedded1_-1.png")
    print('expectedValue = ', expectedValue[-7:])
    """

    


