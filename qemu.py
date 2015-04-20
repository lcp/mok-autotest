#!/usr/bin/python

import os
import cv2
import time
import socket
import pexpect
import tempfile
from fdpexpect import fdspawn

class QemuError(Exception):
	def __init__(self, msg):
		self.msg = msg

def cv2_image_match (image, template):
	try:
		res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
	except cv2.error:
		return False

	min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
	if max_val < 0.8:
		return False

	return True

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

	def take_screenshot (self, output):
		# dump the screen
		self.monitor.send("screendump " + self.screenfifo + "\n")

		# read from fifo
		fp_fifo = open(self.screenfifo)
		fp_dump = open(output, "w+")

		buf = fp_fifo.read()
		while buf != "":
			fp_dump.write(buf)
			buf = fp_fifo.read()

		fp_fifo.close()
		fp_dump.close()

	def match_partial_screen (self, ref_screen, x_start, x_end, y_start, y_end):
		refdump = os.path.join(self.testcase_path, ref_screen)

		if os.path.exists(refdump) == False:
			print refdump + " no found"
			return False

		self.take_screenshot(self.screenshot)

		# compare the screendumps
		ref_img = cv2.imread(refdump, 0)
		tmp_img = cv2.imread(self.screenshot, 0)

		# crop ref_img with start and end
		crop_img = ref_img[y_start:y_end, x_start:x_end]

		return cv2_image_match(tmp_img, crop_img)

	def match_partial_screen_wait (self, ref_screen, wait_time, retry,
				       x_start, x_end, y_start, y_end):
		count = 0

		match = self.match_partial_screen(ref_screen, x_start, x_end,
						  y_start, y_end)

		while match == False:
			count += 1
			if retry > 0 and count > retry:
				raise QemuError("Failed to match " + ref_screen)

			time.sleep(wait_time)
			match = self.match_partial_screen(ref_screen, x_start, x_end,
							  y_start, y_end)

	def match_screen (self, ref_screen):
		refdump = os.path.join(self.testcase_path, ref_screen)

		if os.path.exists(refdump) == False:
			print refdump + " no found"
			return False

		self.take_screenshot(self.screenshot)

		# compare the screendumps
		ref_img = cv2.imread(refdump, 0)
		tmp_img = cv2.imread(self.screenshot, 0)

		return cv2_image_match(tmp_img, ref_img)

	def match_screen_wait (self, ref_screen, wait_time, retry):
		count = 0

		match = self.match_screen(ref_screen)

		while match == False:
			count += 1
			if retry > 0 and count > retry:
				raise QemuError("Failed to match " + ref_screen)

			time.sleep(wait_time)
			match = self.match_screen(ref_screen)

	def pexpect_serial (self, string, wait_time):
		try:
			self.serial_exp.expect(string, timeout=wait_time)
			return True
		except:
			return False

	def write_serial (self, string):
		self.serial_exp.sendline(string)

	def shutdown (self):
		self.monitor.send("system_powerdown\n")

	def disconnect (self):
		self.monitor.shutdown()
		self.monitor.close()
		self.serial.shutdown()
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

		self.serial_exp = pexpect.fdpexpect.fdspawn(self.serial.fileno(), logfile=self.serial_log)

		# setup the pipe for screendump
		self.screenfifo = os.path.join(self.working_dir, "screenfifo")
		if os.path.exists(self.screenfifo) == False:
			os.mkfifo(self.screenfifo)

	def __init__ (self, monitor_socket, serial_socket, working_dir, testcase_path, serial_log=None):
		self.monitor_socket = monitor_socket
		self.serial_socket = serial_socket
		self.working_dir = working_dir
		self.testcase_path = testcase_path

		self.serial_log = serial_log

		self.screenshot = os.path.join(self.working_dir, "screenshot.ppm")
