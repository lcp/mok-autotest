#!/usr/bin/python

import os
import cv2
import time
import numpy
import socket
import tempfile

def sendkey (monitor, key):
	monitor.send("sendkey " + key + "\n")

def sendstring (monitor, string):
	for c in string:
		monitor.send("sendkey " + c + "\n")

def match_screen (monitor, working_dir, data_path, ref_screen):
	refdump = os.path.join(data_path, ref_screen)
	tmpdump = os.path.join(working_dir, "tmpdump.ppm")

	if os.path.exists(refdump) == False:
		print refdump + " no found"
		return False

	# dump the screen
	monitor.send("screendump " + tmpdump + "\n")

	# FIXME wait screendump
	time.sleep(1)

	if os.path.exists(tmpdump) == False:
		print "Failed to dump the screen"
		return False

	# compare the screendumps
	ref_img = cv2.imread(refdump, 0)
	tmp_img = cv2.imread(tmpdump, 0)

	try:
		res = cv2.matchTemplate(tmp_img, ref_img, cv2.TM_CCOEFF_NORMED)
	except cv2.error:
		return False

	threshold = 0.8
	loc = numpy.where(res >= threshold)
	if loc != (0, 0):
		return False

	return True

def match_screen_wait (monitor, working_dir, data_path, ref_screen, wait_time, retry):
	count = 0

	match = match_screen(monitor, working_dir, data_path, ref_screen)

	while match == False:
		count += 1
		if retry != -1 and count > retry:
			return False

		time.sleep(wait_time)
		match = match_screen(monitor, working_dir, data_path, ref_screen)

	return True

def shutdown (monitor):
	monitor.send("system_powerdown\n")
