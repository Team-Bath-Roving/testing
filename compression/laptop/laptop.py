'''Config'''
# Directory of image files
IMG_DIR = "img/"

# Aspect ratio for the test camera
CAM_ASPECT_RATIO = 16 / 9

# Camera in greyscale or colour?
CAM_GREYSCALE = True

# ========================================================

# Import modules
import struct
import socket
import json
import threading
import queue
import numpy as np
import cv2
import zlib

from Sockets import SocketTimeout, SendSocket, ReceiveSocket

# Decode an image into a numpy array
def decode_frame(encoded_data):
	'''Decodes bytes into a numpy array representing a frame'''

	# If there is no data, return False
	if not encoded_data: 
		print("No data")
		return False

	flat_frame = np.frombuffer(zlib.decompress(encoded_data), dtype="uint8")

	if CAM_GREYSCALE:
		BPP = 1
	else:
		BPP = 3 # "Bytes per pixel"

	j = CAM_ASPECT_RATIO # 16/9 # known ratio of width/height
	k = flat_frame.shape[0] // BPP

	w = int(np.sqrt(k * j)) # here we do some maths to work out width and height
	h = k // w

	frame = flat_frame.reshape(h, w, BPP)

	return frame


# Listening for rover signals
def listen_function(img_queue):
	PAYLOAD_STRING = "<I"
	PAYLOAD_SIZE = struct.calcsize(PAYLOAD_STRING)

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as recvsock:

		s = ReceiveSocket(recvsock, 5002)
		overflow = b""

		while True:
			try:
				# Unpack the size of the encoded feedback and images
				encoded_sizes, overflow = s.recv_data(PAYLOAD_SIZE, overflow)
				size = struct.unpack(PAYLOAD_STRING, encoded_sizes)[0]

				# Recieve the encoded image and send to the other thread using queue
				encoded_img, overflow = s.recv_data(size, overflow)
				img_queue.put(encoded_img)

			except SocketTimeout:
				# If recv_data runs for too long and doesn't get the data its expecting, timeout and wait for a reconnection
				print("Socket timed out, reconnecting...")
				s.accept()

# Pygame function
def pygame_function(img_queue):

	# Encoded frames received from rover
	encoded_img = False

	while True:

		# Get encoded image from queue
		if img_queue.full():
			encoded_img = img_queue.get()
		
			# Decode image
			frame = decode_frame(encoded_img)

			cv2.imshow("Image", frame)

		if cv2.waitKey(1) == ord("q"):
			break


# Running the program
if __name__ == "__main__":
	img_queue = queue.Queue(1)

	# Runs both listen
	thread = threading.Thread(target=listen_function, daemon=True, args=(img_queue,))
	thread.start()

	pygame_function(img_queue)