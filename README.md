# Steganography
Embedding secret messages into images

In this project, I create the utility of embedding a message (text or image file) called payload into a carrier image, such that the carrier image looks the same to the human eye even after embedding. This is because embedding creates such slight changes in each pixel that it cannot be detected by the human eye.
Steganography.py has the code for doing the actual embedding. Processor.py has the code to implement a Graphical User Interface (GUI) through which users can drag and drop their payload and carrier images, and embed the payload into the carrier (the GUI only works with image payloads though, not text payloads)

Steganography.py contains the functions to do the embedding/extracting of payload into/from carrier, and Processor.py implements the GUI functionality.


How the embedding works:

1) Raster Scan: The payload is raster-scanned (row-major reading of pixels). For a colored image, the Red, Green and Blue scanner array are concatenated.

2) Compression: The raster-scanned data is compressed using the gzip file format.

3) XML Serialization: The compressed payload, along with metadata such as size of the payload and compression level, is converted into XML format.

4) Base64 encoding: This array of 8-bit elements is converted into an array of 6-bit elements, so that it can be divided into 3 bits of 2 parts each.

5) Modifying the carrier: Each 2-bit part of the 6-bit number is used to replace the two least-significant bits of the Red, Green and Blue pixel values of the carrier image, such that the red pixel gets the least significant 2 bits of the payload, and the blue pixel gets the most significant 2 bits.
