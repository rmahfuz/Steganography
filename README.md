# Steganography
Embedding secret messages into images

In this project, I create the utility of embedding a message (text or image file) called payload into a carrier image, such that the carrier image looks the same to the human eye even after embedding. This is because embedding creates such slight changes in each pixel that it cannot be detected by the human eye.
Steganography.py has the code for doing the actual embedding. Processor.py has the code to implement a Graphical User Interface (GUI) through which users can drag and drop their payload and carrier images, and embed the payload into the carrier (the GUI only works with image payloads though, not text payloads)

Steganography.py contains the functions to do the embedding/extracting of payload into/from carrier, and Processor.py implements the GUI functionality.
