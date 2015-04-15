#!/usr/bin/python

import os
import sys
import qemu
import time
import socket

class VMError(Exception):
	def __init__(self, msg):
		self.msg = msg

def setup_image (vm_control, password):
	# openSUSE shim prompt
	match = vm_control.match_screen_wait("shim-cert-prompt.png", 5, -1)
	if match == False:
		raise VMError("Failed to match shim-cert-prompt.png")
	print "openSUSE shim prompt"
	time.sleep(2)
	vm_control.sendkey("down")
	vm_control.sendkey("ret")

	time.sleep(5)

	# grub2
	# TODO screenshot
	print "grub2"
	vm_control.sendkey("ret")

	# Welcome
	match = vm_control.match_screen_wait("os13.2-welcome.png", 5, -1)
	if match == False:
		raise VMError("Failed to match shim-cert-prompt.png")
	time.sleep(1)
	print "Welcome"
	vm_control.sendkey("alt-n")

	# Installation Options
	match = vm_control.match_screen_wait("os13.2-installation-options.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-installation-options.png")
	time.sleep(1)
	print "Installation Options"
	vm_control.sendkey("alt-n")

	# Suggested Partitioning
	match = vm_control.match_screen_wait("os13.2-suggested-partitioning.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-suggested-partitioning.png")
	time.sleep(1)
	print "Suggested Partitioning"
	vm_control.sendkey("alt-n")

	# Clock and Time Zone
	match = vm_control.match_screen_wait("os13.2-clock-and-time-zone.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-clock-and-time-zone.png")
	time.sleep(1)
	print "Clock and Time Zone"
	vm_control.sendkey("alt-n")

	# Desktop Selection
	match = vm_control.match_screen_wait("os13.2-desktop-selection.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-desktop-selection.png")
	time.sleep(1)
	print "Desktop Selection"
	#	other
	vm_control.sendkey("alt-o")
	time.sleep(1)
	#	text mode
	vm_control.sendkey("alt-i")
	time.sleep(1)
	vm_control.sendkey("alt-n")

	# Create New User
	match = vm_control.match_screen_wait("os13.2-create-new-user.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-create-new-user.png")
	time.sleep(1)
	print "Create New User"
	#	User's Full Name
	vm_control.sendstring("linux")
	#	Password
	vm_control.sendkey("alt-p")
	vm_control.sendstring(password)
	vm_control.sendkey("alt-o")
	#	Confirm Password
	vm_control.sendstring(password)
	vm_control.sendkey("alt-n")

	# Installation Settings
	match = vm_control.match_screen_wait("os13.2-installation-settings.png", 5, 3)
	if match == False:
		raise VMError("Failed to match os13.2-installation-settings.png")
	time.sleep(1)
	print "Installation Settings"
	time.sleep(2)
	vm_control.sendkey("alt-i")
	time.sleep(5)
	vm_control.sendkey("alt-i")

	# Wait the image setup
	match = vm_control.match_screen_wait("os13.2-login.png", 10, -1)
	if match == False:
		raise VMError("Failed to match os13.2-login.png")
	print "Installation done"

def enable_serial_console (vm_control, password):
	# Wait the image setup
	match = vm_control.match_screen_wait("os13.2-login.png", 10, -1)
	if match == False:
		raise VMError("Failed to match os13.2-login.png")

	vm_control.sendstring("root\n")
	time.sleep(5)
	vm_control.sendstring(password + "\n")
	time.sleep(5)

	sed_cmd = "sed -i"
	sed_cmd += " 's/GRUB_CMDLINE_LINUX_DEFAULT=\"/& console=tty0 console=ttyS0,38400n8 /'"
	sed_cmd += " /etc/default/grub"

	print "serial console parameters"
	vm_control.sendstring(sed_cmd + "\n")

	time.sleep(5)

	print "update-bootloader"
	vm_control.sendstring("update-bootloader --refresh\n")
