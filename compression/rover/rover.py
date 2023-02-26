# Network information
LAPTOP_IP = "localhost"

# ========================================================

# Import modules
import cv2
import numpy as np
import socket
import time
import struct
from random import randint
from Sockets import SendSocket, ReceiveSocket

# Make changes to the frame before encoding and sending
def compress_frame(frame):

	# Convert to greyscale
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# Scale the frame down
	sf = 0.4
	frame = cv2.resize(frame, (0, 0), fx=sf, fy=sf)

	return frame

def main_function():
	try:
		# Start video capture
		cap = cv2.VideoCapture(0)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sendsock:

			# Connect to laptop
			s = SendSocket(sendsock, LAPTOP_IP, 5002, "<I")
			s.connect()

			# Define how frequently to send image
			prev_time = time.perf_counter()
			freq = 1/20
			i = 0

			# Main rover loop
			while True:

				# Send feedback and images
				if time.perf_counter() - prev_time > freq:

					ret, frame = cap.read()

					if not ret:
						raise Exception("Capture cannot be read, restart file")
					else:
						# Any changes that are done to the image should be done in this function
						frame = compress_frame(frame)

					if i == 0:
						data_size = s.send(frame)
						print(data_size)
						i += 1
					else:
						s.send(frame)

					prev_time = time.perf_counter()

	except KeyboardInterrupt:
		print("<> KeyboardInterrupt caught, exiting")
		cap.release()
		raise SystemExit

if __name__ == "__main__":
	main_function()