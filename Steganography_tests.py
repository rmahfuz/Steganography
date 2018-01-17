import time
from os.path import join
import unittest

from numpy import ndarray as nmat
from imageio import *
from Steganography import *
from checkClean import assertCleaningIsRandom


class ImageAssertion:
    """
    Provides a convenience method for comparing two numpy arrays.
    """
    @staticmethod
    def assertArrayEqual(array1, array2):

        if not isinstance(array1, nmat) or not isinstance(array2, nmat):
            raise AssertionError("One or more of the input parameters are not valid arrays.")

        if array1.shape != array2.shape:
            raise AssertionError("Array shapes do not match.")

        if array1.dtype != array2.dtype:
            raise AssertionError("Array types do not match.")

        if not np.array_equal(array1, array2):
            raise AssertionError("Arrays do not match.")

def readFile(path):

    with open(path, "r") as xFile:
        content = xFile.read()

    return content


class SteganographyTestSuite(unittest.TestCase, ImageAssertion):

    folder = "data"

    def test_checkLibraries(self):

        import numpy as np
        import scipy as sp
        import imageio as io

        with self.subTest(key="numpy"):
            version = np.__version__

            self.assertEqual(version, '1.13.3')

        with self.subTest(key="scipy"):
            version = sp.__version__

            self.assertEqual(version, '1.0.0')

        with self.subTest(key="imageio"):
            version = io.__version__

            self.assertEqual(version, '2.2.0')

    def test_PayloadBadInitializer(self):

        with self.subTest(key="Bad Data"):
            rawData = [[1, 1], [0, 0]]
            self.assertRaises(TypeError, Payload, rawData)

        with self.subTest(key="Bad JSON"):
            self.assertRaises(TypeError, Payload, json=[63, 0, 11, 5])

        with self.subTest(key="Missing Parameters"):
            self.assertRaises(ValueError, Payload)

        with self.subTest(key="Bad Compression Level"):
            rawData = imread(join(self.folder, "payload1.png"))
            self.assertRaises(ValueError, Payload, rawData=rawData, compressionLevel=10)

    def test_PayloadWithRawDataInput(self):

        with self.subTest(key="Color Image"):
            json = readFile(join(self.folder, "payload1.json"))

            rawData = imread(join(self.folder, "payload1.png"))
            payload = Payload(rawData, -1)

            expectedValue = json
            actualValue = payload.json

            self.assertEqual(expectedValue, actualValue)

        with self.subTest(key="Gray Image"):
            json = readFile(join(self.folder, "payload2.json"))

            rawData = imread(join(self.folder, "payload2.png"))
            payload = Payload(rawData, 7)

            expectedValue = json
            actualValue = payload.json

            self.assertEqual(expectedValue, actualValue)

        with self.subTest(key="Text File"):
            json = readFile(join(self.folder, "payload3.json"))
            text = readFile(join(self.folder, "payload3.txt"))

            rawData = np.fromstring(text, dtype=np.uint8)
            payload = Payload(rawData, 5)

            expectedValue = json
            actualValue = payload.json

            self.assertEqual(expectedValue, actualValue)

    def test_PayloadWithContentInput(self):

        with self.subTest(key="Color Image"):
            json = readFile(join(self.folder, "payload1.json"))

            rawData = imread(join(self.folder, "payload1.png"))
            payload = Payload(json=json)

            expectedValue = rawData
            actualValue = payload.rawData

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Gray Image"):
            json = readFile(join(self.folder, "payload2.json"))

            rawData = imread(join(self.folder, "payload2.png"))
            payload = Payload(json=json)

            expectedValue = rawData
            actualValue = payload.rawData

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Text File"):
            json = readFile(join(self.folder, "payload3.json"))
            text = readFile(join(self.folder, "payload3.txt"))

            rawData = np.fromstring(text, dtype=np.uint8)
            payload = Payload(json=json)

            expectedValue = rawData
            actualValue = payload.rawData

            self.assertArrayEqual(expectedValue, actualValue)

    def test_CarrierInitializerAndValidation(self):

        with self.subTest(key="Initializer Check"):
            img = [[1, 1], [0, 0]]
            self.assertRaises(TypeError, Carrier, img)

        with self.subTest(key="Invalid Carrier Type"):
            img = imread(join(self.folder, "payload2.png"))
            self.assertRaises(ValueError, Carrier, img)

    def test_CarrierImmutability(self):

        with self.subTest(key="After Cleaning"):
            img = imread(join(self.folder, "carrier.png"))
            ref = img.copy()
            c = Carrier(img)
            c.clean()

            self.assertArrayEqual(ref, c.img)

        with self.subTest(key="After Embedding"):
            img = imread(join(self.folder, "carrier.png"))
            ref = img.copy()
            c = Carrier(img)
            p = Payload(imread(join(self.folder, "payload2.png")))
            c.embedPayload(p)

            self.assertArrayEqual(ref, c.img)

        with self.subTest(key="After Extraction"):
            img = imread(join(self.folder, "embedded1_-1.png"))
            ref = img.copy()
            c = Carrier(img)
            c.extractPayload()

            self.assertArrayEqual(ref, c.img)

    def test_CarrierCheckingForPayload(self):

        with self.subTest(key="No Payload"):
            img = imread(join(self.folder, "carrier.png"))
            c = Carrier(img)

            begin = time.clock()
            actualValue = c.payloadExists()
            end = time.clock()

            duration = end - begin

            self.assertTrue(duration < 5 and not actualValue)

        with self.subTest(key="Payload Present"):
            img = imread(join(self.folder, "embedded3_5.png"))
            c = Carrier(img)
            begin = time.clock()
            actualValue = c.payloadExists()
            end = time.clock()

            duration = end - begin

            self.assertTrue(duration < 5 and actualValue)

    def test_CarrierCleaning(self):

        img = imread(join(self.folder, "embedded2_7.png"))
        carrier = Carrier(img)

        clean1 = carrier.clean()
        clean2 = carrier.clean()

        with self.subTest(key="Cleaning Once"):

            assertCleaningIsRandom(img, clean1)

        with self.subTest(key="Cleaning Twice"):

            assertCleaningIsRandom(img, clean2)

        with self.subTest(key="Random Clean"):

            self.assertFalse(np.array_equal(clean1, clean2))

    def test_CarrierEmbeddingValidation(self):

        with self.subTest(key="Incorrect Parameter"):
            img = imread(join(self.folder, "payload1.png"))
            c = Carrier(imread(join(self.folder, "carrier.png")))

            self.assertRaises(TypeError, c.embedPayload, payload=img)

        with self.subTest(key="Payload Exists"):
            p = Payload(imread(join(self.folder, "dummy.png")))
            c = Carrier(imread(join(self.folder, "embedded2_7.png")))

            self.assertRaises(Exception, c.embedPayload, payload=p)

        with self.subTest(key="Large Payload"):
            p = Payload(imread(join(self.folder, "dummy.png")))
            c = Carrier(imread(join(self.folder, "dummyCarrier.png")))

            self.assertRaises(ValueError, c.embedPayload, payload=p)

    def test_CarrierEmbedding(self):

        with self.subTest(key="Color Image"):
            p = Payload(imread(join(self.folder, "payload1.png")), -1)
            c = Carrier(imread(join(self.folder, "carrier.png")))

            expectedValue = imread(join(self.folder, "embedded1_-1.png"))
            actualValue = c.embedPayload(p)

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Gray Image"):
            p = Payload(imread(join(self.folder, "payload2.png")), 7)
            c = Carrier(imread(join(self.folder, "carrier.png")))

            expectedValue = imread(join(self.folder, "embedded2_7.png"))
            actualValue = c.embedPayload(p)

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Text"):
            text = readFile(join(self.folder, "payload3.txt"))
            rawData = np.fromstring(text, dtype=np.uint8)
            p = Payload(rawData, 5)
            c = Carrier(imread(join(self.folder, "carrier.png")))

            expectedValue = imread(join(self.folder, "embedded3_5.png"))
            actualValue = c.embedPayload(p)

            self.assertArrayEqual(expectedValue, actualValue)

    def test_CarrierExtraction(self):

        with self.subTest(key="Color Image"):
            c = Carrier(imread(join(self.folder, "embedded1_-1.png")))

            expectedValue = imread(join(self.folder, "payload1.png"))
            actualValue = c.extractPayload().rawData

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Gray Image"):
            c = Carrier(imread(join(self.folder, "embedded2_7.png")))

            expectedValue = imread(join(self.folder, "payload2.png"))
            actualValue = c.extractPayload().rawData

            self.assertArrayEqual(expectedValue, actualValue)

        with self.subTest(key="Text"):
            c = Carrier(imread(join(self.folder, "embedded3_5.png")))
            text = readFile(join(self.folder, "payload3.txt"))
            rawData = np.fromstring(text, dtype=np.uint8)

            expectedValue = rawData
            actualValue = c.extractPayload().rawData

            self.assertArrayEqual(expectedValue, actualValue)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
