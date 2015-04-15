#!/usr/bin/python

import os
import cv2
import time
import socket
import tempfile

class QemuError(Exception):
	def __init__(self, msg):
		self.msg = msg

class QemuControl:
	def sendkey (self, key):
		self.monitor.send("sendkey " + key + "\n")

	def sendstring (self, string):
		for c in string:
			if c.islower() == True or c.isdigit():
				self.sendkey(c)
			elif c.isupper() == True:
				self.sendkey("shift-" + c.lower())
			elif c == "'":
				self.sendkey("apostrophe")
			elif c == '*':
				self.sendkey("asterisk")
			elif c == '\\':
				self.sendkey("backslash")
			elif c == '[':
				self.sendkey("bracket_left")
			elif c == ']':
				self.sendkey("bracket_right")
			elif c == ',':
				self.sendkey("comma")
			elif c == '.':
				self.sendkey("dot")
			elif c == '=':
				self.sendkey("equal")
			elif c == '`':
				self.sendkey("grave_accent")
			elif c == '+':
				self.sendkey("kp_add")
			elif c == '-':
				self.sendkey("minus")
			elif c == '\n':
				self.sendkey("ret")
			elif c == ';':
				self.sendkey("semicolon")
			elif c == ':':
				self.sendkey("shift-semicolon")
			elif c == '!':
				self.sendkey("shift-1")
			elif c == '@':
				self.sendkey("shift-2")
			elif c == '#':
				self.sendkey("shift-3")
			elif c == '$':
				self.sendkey("shift-4")
			elif c == '%':
				self.sendkey("shift-5")
			elif c == '^':
				self.sendkey("shift-6")
			elif c == '&':
				self.sendkey("shift-7")
			elif c == '(':
				self.sendkey("shift-9")
			elif c == ')':
				self.sendkey("shift-0")
			elif c == '_':
				self.sendkey("shift-minus")
			elif c == '"':
				self.sendkey("shift-apostrophe")
			elif c == '/':
				self.sendkey("slash")
			elif c == ' ':
				self.sendkey("spc")
			elif c == '\t':
				self.sendkey("tab")
			else:
				print "unknown key: " + c

	def match_screen (self, ref_screen):
		refdump = os.path.join(self.testcase_path, ref_screen)
		tmpdump = os.path.join(self.working_dir, "tmpdump.ppm")

		if os.path.exists(refdump) == False:
			print refdump + " no found"
			return False

		# dump the screen
		self.monitor.send("screendump " + tmpdump + "\n")

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

		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		if max_val < 0.8:
			return False

		return True

	def match_screen_wait (self, ref_screen, wait_time, retry):
		count = 0

		match = self.match_screen(ref_screen)

		while match == False:
			count += 1
			if retry != -1 and count > retry:
				return False

			time.sleep(wait_time)
			match = self.match_screen(ref_screen)

		return True

	def shutdown (self):
		self.monitor.send("system_powerdown\n")

	def disconnect (self):
		self.monitor.close()
		self.serial.close()

	def connect (self):
		# Connect to monitor_socket
		if os.path.exists(self.monitor_socket) == False:
			raise QemuError(self.monitor_socket + "doesn't exist.")

		if os.path.exists(self.serial_socket) == False:
			raise QemuError(self.serial_socket + "doesn't exist.")

		self.monitor = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.monitor.connect(self.monitor_socket)

		self.serial = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.serial.connect(self.serial_socket)

	def __init__ (self, monitor_socket, serial_socket, working_dir, testcase_path):
		self.monitor_socket = monitor_socket
		self.serial_socket = serial_socket
		self.working_dir = working_dir
		self.testcase_path = testcase_path
