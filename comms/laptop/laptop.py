'''Config'''
# Network information
ROVER_IP = "localhost"

# Camera information
NUM_CAMS = 1
CAM_NAMES = ["Cam 1"]
ASPECT_RATIO = 16 / 9
CAM_GREYSCALE = False

# ========================================================

# Import modules
from base64 import encode
import pygame
import datetime
import marstime
import struct
import socket
import json
import threading
import queue
import cv2

from classes.FeedManager import FeedManager
# from classes.ActionHandler import ActionHandler
from classes.Sockets import SocketTimeout, SendSocket, ReceiveSocket

# Listening for rover signals
def listen_function(fb_queue, img_queue):
	PAYLOAD_STRING = "<H" + "I" * NUM_CAMS
	PAYLOAD_SIZE = struct.calcsize(PAYLOAD_STRING)

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as recvsock:

		s = ReceiveSocket(recvsock, 5002)
		overflow = b""

		while True:
			try:
				# Unpack the size of the encoded feedback and images
				encoded_sizes, overflow = s.recv_data(PAYLOAD_SIZE, overflow)
				sizes = struct.unpack(PAYLOAD_STRING, encoded_sizes)

				# Receive and decode feedback, then queue if not empty
				encoded_feedback, overflow = s.recv_data(sizes[0], overflow)
				fb = json.loads(encoded_feedback.decode())
				if fb: fb_queue.put(fb)

				# Receive encoded image frames
				for size in sizes[1:]:
					encoded_img, overflow = s.recv_data(size, overflow)
					img_queue.put(encoded_img)

			except SocketTimeout:
				print("Socket timed out, reconnecting...")
				s.accept()

# Pygame function
def pygame_function(fb_queue, img_queue):

	# Set up send socket
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sendsock:

		s = SendSocket(sendsock, ROVER_IP, 5001)
		
		# Wait until rover is connected
		while True:
			if not fb_queue.empty():
				fb = fb_queue.get()
				if fb["Connected"]:
					break
		
		s.connect()

		# Loop until user end the program
		done = False

		# Create instance of FeedManager and set up CameraFeeds 
		fm = FeedManager(CAM_NAMES, ASPECT_RATIO, CAM_GREYSCALE)

		# Encoded frames received from rover
		encoded_frames = [False] * NUM_CAMS

		while not done:

			# Displaying rover feedback
			while not fb_queue.empty():
				print(fb_queue.get()) # [Temp] Just print out feedback to console

			# Displaying camera feeds
			if img_queue.full():
				encoded_frames = [img_queue.get() for _ in range(NUM_CAMS)]
			
			fm.display_feeds(encoded_frames)

			if cv2.waitKey(1) == ord("r"):
				s.send_msg({"FORWARD": 0.2, "SCOOP": -0.6}) # To test sending control message

			elif cv2.waitKey(1) == ord("q"):
				s.send_msg("QUIT_ROVER")
				print("Quitting code")
				break

		raise SystemExit


# Running the program
if __name__ == "__main__":
	fb_queue = queue.Queue(0)
	img_queue = queue.Queue(NUM_CAMS)

	thread = threading.Thread(target=listen_function, daemon=True, args=(fb_queue,img_queue,))
	thread.start()

	pygame_function(fb_queue, img_queue)