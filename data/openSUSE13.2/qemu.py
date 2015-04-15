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
		if c.islower() == True or c.isdigit():
			sendkey(monitor, c)
		elif c.isupper() == True:
			sendkey(monitor, "shift-" + c.lower())
		elif c == "'":
			sendkey(monitor, "apostrophe")
		elif c == '*':
			sendkey(monitor, "asterisk")
		elif c == '\\':
			sendkey(monitor, "backslash")
		elif c == '[':
			sendkey(monitor, "bracket_left")
		elif c == ']':
			sendkey(monitor, "bracket_right")
		elif c == ',':
			sendkey(monitor, "comma")
		elif c == '.':
			sendkey(monitor, "dot")
		elif c == '=':
			sendkey(monitor, "equal")
		elif c == '`':
			sendkey(monitor, "grave_accent")
		elif c == '+':
			sendkey(monitor, "kp_add")
		elif c == '-':
			sendkey(monitor, "minus")
		elif c == '\n':
			sendkey(monitor, "ret")
		elif c == ';':
			sendkey(monitor, "semicolon")
		elif c == ':':
			sendkey(monitor, "shift-semicolon")
		elif c == '!':
			sendkey(monitor, "shift-1")
		elif c == '@':
			sendkey(monitor, "shift-2")
		elif c == '#':
			sendkey(monitor, "shift-3")
		elif c == '$':
			sendkey(monitor, "shift-4")
		elif c == '%':
			sendkey(monitor, "shift-5")
		elif c == '^':
			sendkey(monitor, "shift-6")
		elif c == '&':
			sendkey(monitor, "shift-7")
		elif c == '(':
			sendkey(monitor, "shift-9")
		elif c == ')':
			sendkey(monitor, "shift-0")
		elif c == '_':
			sendkey(monitor, "shift-minus")
		elif c == '"':
			sendkey(monitor, "shift-apostrophe")
		elif c == '/':
			sendkey(monitor, "slash")
		elif c == ' ':
			sendkey(monitor, "spc")
		elif c == '\t':
			sendkey(monitor, "tab")
		else:
			print "unknown key: " + c

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
