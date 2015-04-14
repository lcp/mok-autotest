#!/usr/bin/python

import os
import sys
import qemu
import time
import socket

def setup_image (monitor_socket, serial_socket, working_dir, testcase_path):

	# Connect to monitor_socket
	if os.path.exists(monitor_socket) == False:
		print "Failed to connect to QEMU monitor"
		sys.exit(1)

	monitor = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	monitor.connect(monitor_socket)

	# openSUSE shim prompt
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "shim-cert-prompt.png", 5, -1)
	print "openSUSE shim prompt"
	if match == False:
		# TODO Better error handling
		print "Failed to match shim-cert-prompt.png"
		return
	time.sleep(2)
	qemu.sendkey(monitor, "down")
	qemu.sendkey(monitor, "ret")

	time.sleep(5)

	# grub2
	# TODO screenshot
	print "grub2"
	qemu.sendkey(monitor, "ret")

	# Welcome
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-welcome.png", 5, -1)
	print "Welcome"
	qemu.sendkey(monitor, "alt-n")

	# Installation Options
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-installation-options.png", 5, 3)
	print "Installation Options"
	qemu.sendkey(monitor, "alt-n")

	# Suggested Partitioning
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-suggested-partitioning.png", 5, 3)
	print "Suggested Partitioning"
	qemu.sendkey(monitor, "alt-n")

	# Clock and Time Zone
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-clock-and-time-zone.png", 5, 3)
	print "Clock and Time Zone"
	qemu.sendkey(monitor, "alt-n")

	# Desktop Selection
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-desktop-selection.png", 5, 3)
	print "Desktop Selection"
	#	other
	qemu.sendkey(monitor, "alt-o")
	time.sleep(1)
	#	text mode
	qemu.sendkey(monitor, "alt-i")
	time.sleep(1)
	qemu.sendkey(monitor, "alt-n")

	# Create New User
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-create-new-user.png", 5, 3)
	print "Create New User"
	#	User's Full Name
	qemu.sendstring(monitor, "linux")
	#	Password
	qemu.sendkey(monitor, "alt-p")
	qemu.sendstring(monitor, "not a s3cret")
	qemu.sendkey(monitor, "alt-o")
	#	Confirm Password
	qemu.sendstring(monitor, "not a s3cret")
	qemu.sendkey(monitor, "alt-n")

	# Installation Settings
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-installation-settings.png", 5, 3)
	print "Installation Settings"
	time.sleep(2)
	qemu.sendkey(monitor, "alt-i")
	time.sleep(5)
	qemu.sendkey(monitor, "alt-i")

	# Wait the image setup
	match = qemu.match_screen_wait(monitor, working_dir, testcase_path,
				       "os13.2-login.png", 10, -1)
	print "All done"

	qemu.shutdown(monitor)

	monitor.close()
