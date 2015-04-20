#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import signal
import socket
import subprocess

from qemu import QemuControl
from qemu import QemuError

DEFAULT_UEFI = "/usr/share/qemu/ovmf-x86_64-ms.bin"
Password = "not a s3cret"
vm = None

def print_help ():
	print "This program will use the specified qemu image for shim test."
	print "Parameters:"
	print "--qemu-image <qemu_image>"
	print "\tthe name of the qemu image to use"
	print ""
	print "--uefi <uefi_code>"
	print "\tthe path to the UEFI firmware"
	print "\tDefault: " + DEFAULT_UEFI
	print ""
	print "--testcase-path"
	print "\tthe path to the testcases"
	print ""
	print "--working-dir"
	print "\tthe directory of the qemu image and other temporary files"
	print ""
	print "--serial-log"
	print "\tthe log of the serial port"

def sig_handler (signum, frame):
	if signum == signal.SIGINT and vm != None and vm.poll != None:
		vm.kill()
		sys.exit(1)

def main (argv):
	uefi = DEFAULT_UEFI
	qemu_img = None
	testcase_path = None
	working_dir = os.getcwd()
	serial_log = None

	# parse the arguments
	try:
		opts, args = getopt.getopt(argv, "hu:q:t:w:s:",
					   ["uefi=", "qemu-image=",
					    "testcase-path=", "working_dir=",
					    "serial-log="])
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
		elif opt in ("-t", "--testcase-path"):
			testcase_path = arg
		elif opt in ("-w", "--working-dir"):
			working_dir = arg
		elif opt in ("-s", "--serial-log"):
			serial_log = arg

	# Check the parameters
	if qemu_img == None or testcase_path == None:
		print_help()
		sys.exit(1)

	if os.path.exists(uefi) == False:
		print "Could not find " + uefi
		sys.exit(1)

	if os.path.isdir(testcase_path) == True:
		testcase_path = os.path.abspath(testcase_path)
		sys.path.append(testcase_path)
		import shim
	else:
		print testcase_path + " is no a directory."
		sys.exit(1)

	if os.path.isdir(working_dir) == True:
		working_dir = os.path.abspath(working_dir)
	else:
		print working_dir + " is no a directory."
		sys.exit(1)

	qemu_img = os.path.join(working_dir, qemu_img)

	if os.path.exists(qemu_img) == False:
		print "Could not find " + qemu_img

	backing_img = qemu_img + ".backing"
	share_dir = os.path.join(working_dir, "share")

	if os.path.exists(share_dir) == False:
		try:
			os.mkdir(share_dir)
		except OSError:
			print "Could not create " + share_dir

	if serial_log != None:
		serial_log = os.path.join(working_dir, serial_log)
		out_log = file(serial_log,'w')

	# create the backing image
	img_cmd = 'qemu-img create -f qcow2 -b ' + qemu_img + ' ' + backing_img
	subprocess.check_call(img_cmd.split(), stdout=subprocess.PIPE)

	monitor_socket = os.path.join(working_dir, "monitor_socket")
	serial_socket = os.path.join(working_dir, "serial_socket")

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
	qemu_opt += " -drive file=" + backing_img

	# share dir
	qemu_opt += " -fsdev local,id=exp,path=" + share_dir + ",security_model=mapped-file"
	qemu_opt += " -device virtio-9p-pci,fsdev=exp,mount_tag=v_share"

	# vnc display
	# FIXME change the port?
	qemu_opt += " -vnc :1,share=force-shared"

	qemu_cmd = "qemu-system-x86_64" + qemu_opt

	print "qemu command: " + qemu_cmd + "\n"

	# signal handling
	signal.signal(signal.SIGINT, sig_handler)

	# start the VM
	vm = subprocess.Popen(qemu_cmd.split(), stdout=subprocess.PIPE)

	# wait qemu to start
	time.sleep (5)

	vm_control = QemuControl(monitor_socket, serial_socket, working_dir,
				 testcase_path, serial_log=out_log)
	vm_control.connect()

	# TODO start test
	# scripts to setup the image
	try:
		shim.boot_and_login(vm_control, Password)
		shim.install_mokutil(vm_control)
		shim.install_shim(vm_control)
	except socket.error:
		print "qemu socket error"
		if vm.poll() == None:
			vm.kill()
		sys.exit(1)
	except QemuError as e:
		print e.msg
		if vm.poll() == None:
			vm.kill()
		sys.exit(1)

	# wait for the last command
	time.sleep(1)

	vm_control.shutdown()

	vm.wait()

	os.remove(backing_img)

if __name__ == "__main__":
	main(sys.argv[1:])
