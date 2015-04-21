#!/usr/bin/python

import os
import sys
import time
import socket

class VMError(Exception):
	def __init__(self, msg):
		self.msg = msg

def setup_image (vm_control, password):
	# grub2
	vm_control.match_partial_screen_wait("sle11-sp3-installation-grub2.png", 5, 10, 260, 530, 70, 100)
	print "grub2"
	vm_control.sendkey("ret")

	# Welcome
	vm_control.match_screen_wait("sle11-sp3-welcome.png", 5, -1)
	time.sleep(1)
	print "Welcome"
	vm_control.sendkey("alt-a")
	vm_control.sendkey("alt-n")

	# Media Check
	vm_control.match_screen_wait("sle11-sp3-media-check.png", 5, 3)
	print "Media Check"
	vm_control.sendkey("alt-n")

	# Installation Mode
	vm_control.match_screen_wait("sle11-sp3-installation-mode.png", 5, 3)
	print "Installation Mode"
	vm_control.sendkey("alt-n")

	# Clock and Time Zone
	vm_control.match_screen_wait("sle11-sp3-clock-and-time-zone.png", 5, 3)
	print "Clock and Time Zone"
	vm_control.sendkey("alt-n")

	# Server Base Scenario
	vm_control.match_screen_wait("sle11-sp3-server-base-scenario.png", 5, 3)
	print "Server Base Scenario"
	vm_control.sendkey("alt-n")

	# Installation Settings
	print "Installation Settings"
	vm_control.match_screen_wait("sle11-sp3-installation-settings.png", 5, 3)
	vm_control.sendkey("alt-i")
	time.sleep(3)
	vm_control.sendkey("alt-a")
	time.sleep(5)
	vm_control.sendkey("alt-i")

	# Reboot
	vm_control.match_partial_screen_wait("sle11-sp3-grub2.png", 5, -1, 300, 500, 70, 100)
	print "grub2"
	vm_control.sendkey("ret")

	# Password for the System Administrator
	vm_control.match_screen_wait("sle11-sp3-password-admin.png", 5, 120)
	print "Password for the System Administrator"
	vm_control.sendstring(password)
	vm_control.sendkey("alt-f")
	vm_control.sendstring(password)
	vm_control.sendkey("alt-n")
	
	# Hostname and Domain Name
	vm_control.match_screen_wait("sle11-sp3-hostname-and-domain-name.png", 5, 3)
	print "Hostname and Domain Name"
	vm_control.sendkey("alt-n")

	# Network Configuration
	vm_control.match_screen_wait("sle11-sp3-network-configuration.png", 5, 30)
	print "Network Configuration"
	vm_control.sendkey("alt-n")

	# Test Internet Connection
	vm_control.match_screen_wait("sle11-sp3-test-internet.png", 5, 30)
	print "Test Internet Connection"
	vm_control.sendkey("alt-o")
	vm_control.sendkey("alt-n")

	# Network Services Configuration
	vm_control.match_screen_wait("sle11-sp3-network-services-configuration.png", 5, 30)
	print "Network Services Configuration"
	vm_control.sendkey("alt-s")
	vm_control.sendkey("alt-n")

	# User Authentication Method
	vm_control.match_screen_wait("sle11-sp3-user-authentication-method.png", 5, 3)
	print "User Authentication Method"
	vm_control.sendkey("alt-o")
	vm_control.sendkey("alt-n")

	# New Local User
	vm_control.match_screen_wait("sle11-sp3-new-local-user.png", 5, 3)
	print "New Local User"
	#	User's Full Name
	vm_control.sendstring("linux")
	#	Password
	vm_control.sendkey("alt-p")
	vm_control.sendstring(password)
	vm_control.sendkey("alt-o")
	#	Confirm Password
	vm_control.sendstring(password)
	vm_control.sendkey("alt-n")

	# Release Notes
	vm_control.match_screen_wait("sle11-sp3-release-notes.png", 5, 30)
	print "Release Notes"
	vm_control.sendkey("alt-n")

	# Hardware Configuration
	vm_control.match_screen_wait("sle11-sp3-hardware-configuration.png", 5, 30)
	print "Hardware Configuration"
	vm_control.sendkey("alt-n")

	# Installation Completed
	vm_control.match_screen_wait("sle11-sp3-installation-completed.png", 5, 3)
	print "Installation Completed"
	vm_control.sendkey("alt-c")
	vm_control.sendkey("alt-f")

	# GDM
	vm_control.match_partial_screen_wait("sle11-sp3-gdm.png", 5, 30, 111, 685, 180, 420)
	print "Installation done"

def enable_serial_console (vm_control, password):
	# Switch to console
	vm_control.sendkey("ctrl-alt-f2")
	time.sleep(3)

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

	# wait update-bootloader
	time.sleep(20)
