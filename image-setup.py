#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import subprocess

DEFAULT_UEFI = "/usr/share/qemu/ovmf-x86_64-ms.bin"

def print_help ():
	print "This program will create a qemu image and setup the SUSE distros with the UEFI firmware"
	print "for the further tests."
	print "Parameters:"
	print "--qemu-image <qemu_image>"
	print "\tthe name of the qemu image to be created"
	print ""
	print "--iso <OS ISO image>"
	print "\tthe iso image of the OS"
	print ""
	print "--uefi <uefi_code>"
	print "\tthe path to the UEFI firmware"
	print "\tDefault: " + DEFAULT_UEFI
	print ""
	print "--force"
	print "\toverwrite the existing qemu image"
	print ""
	print "--testcase-path"
	print "\tthe path to the testcases"
	print ""
	print "--working-dir"
	print "\tthe directory for the files to be created"

def main (argv):
	uefi = DEFAULT_UEFI
	qemu_img = None
	iso_img = None
	force_rewrite = False
	testcase_path = None

	working_dir = os.getcwd()

	# parse the arguments
	try:
		opts, args = getopt.getopt(argv, "hfu:q:i:t:w:",
					   ["force", "uefi=", "qemu-image=",
					    "iso=", "testcase-path=", "working_dir="])
	except getopt.GetoptError:
		print_help()
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print_help()
			sys.exit()
		elif opt in ("-u", "--uefi"):
			uefi = arg
		elif opt in ("-q", "--qemu-image"):
			qemu_img = arg
		elif opt in ("-i", "--iso"):
			iso_img = arg
		elif opt in ("-f", "--force"):
			force_rewrite = True
		elif opt in ("-t", "--testcase-path"):
			testcase_path = arg
		elif opt in ("-w", "--working-dir"):
			working_dir = arg

	# Check the parameters
	if qemu_img == None or iso_img == None or testcase_path == None:
		print_help()
		sys.exit(1)

	if os.path.exists(qemu_img) == True:
		if force_rewrite == False:
			print qemu_img + " already exists."
			sys.exit(1)
		else:
			os.remove(qemu_img)

	if os.path.exists(iso_img) == False:
		print iso_img + " doesn't exist."
		sys.exit(1)

	if os.path.exists(uefi) == False:
		print uefi + " doesn't exist."
		sys.exit(1)

	if os.path.isdir(testcase_path) == True:
		testcase_path = os.path.abspath(testcase_path)
		sys.path.append(testcase_path)
		import vmimage
	else:
		print testcase_path + " is no a directory."
		sys.exit(1)

	if os.path.isdir(working_dir) == True:
		working_dir = os.path.abspath(working_dir)
	else:
		print working_dir + " is no a directory."
		sys.exit(1)

	qemu_img = os.path.join(working_dir, qemu_img)
	monitor_socket = os.path.join(working_dir, "monitor_socket")
	serial_socket = os.path.join(working_dir, "serial_socket")

	# Create the qemu-image
	subprocess.call(["qemu-img", "create", "-f", "qcow2", qemu_img, "20G" ])

	qemu_opt = ""

	# UEFI firmwares
	qemu_opt += " -bios " + uefi

	# Enable KVM
	qemu_opt += " -enable-kvm"

	# VGA type
	qemu_opt += " -vga std"

	# memory: 1GB
	qemu_opt += " -m 1024"

	# monitor socket
	qemu_opt += " -monitor unix:" + monitor_socket + ",server,nowait"

	# serial socket
	qemu_opt += " -serial unix:" + serial_socket + ",server,nowait"

	# hard drive
	qemu_opt += " -hda " + qemu_img

	# cdrom
	qemu_opt += " -cdrom " + iso_img

	# use sdl instead of gtk
	qemu_opt += " -sdl"

	qemu_cmd = "qemu-system-x86_64" + qemu_opt

	print "qemu command: " + qemu_cmd + "\n"
	# start the VM
	vm = subprocess.Popen(qemu_cmd.split(), stdout=subprocess.PIPE)

	# TODO signal handling
	#      watch the status of qemu

	# wait qemu to start
	time.sleep (5)

	# TODO scripts to setup the image
	vmimage.setup_image(monitor_socket, serial_socket, working_dir, testcase_path)

	# TODO enable serial console

	vm.wait()

if __name__ == "__main__":
	main(sys.argv[1:])
