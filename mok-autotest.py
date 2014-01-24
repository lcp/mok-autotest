#!/usr/bin/python

import os
import sys
import getopt
import shutil
import pexpect
import tempfile
import subprocess

backing_img = None
share_dir = None

def print_help ():
	print sys.argv[0] + " -k <DER file> -p <password> -v <vm image> -u <uefi image> -l <log file>"

def unexpected (vm, message):
	print "UNEXPECTED: " + message
	vm.terminate()
	os.remove(backing_img)
	shutil.rmtree(share_dir)
	sys.exit(1)

def login (vm, username, password):
	try:
		vm.expect(' login: ', timeout=120)
		vm.sendline(username)
		vm.expect('Password: ')
		vm.sendline(password)
	except:
		unexpected (vm, 'failed to login')

def execute_cmd (vm, cmd):
	try:
		vm.expect(' [#\$]')
		vm.sendline(cmd)
	except:
		unexpected (vm, cmd)

def enroll_mok (vm, mok_password):
	execute_cmd(vm, 'mokutil -P -i mok_key.der')
	# reboot to MokManager
	execute_cmd(vm, 'reboot')

	try:
		vm.expect('Shim UEFI key management', timeout=300)
		vm.send(' ')

		vm.expect('Enroll MOK');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('View key 0');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('No');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('Password:');
		vm.sendline(mok_password + '\r')

		vm.expect('OK');
		vm.sendline('\r')
	except:
		unexpected (vm, 'failed to enroll MOK')

def delete_mok (vm, mok_password):
	execute_cmd(vm, 'mokutil -P -d mok_key.der')
	# reboot to MokManager
	execute_cmd(vm, 'reboot')

	try:
		vm.expect('Shim UEFI key management', timeout=300)
		vm.send(' ')

		vm.expect('Delete MOK');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('View key 0');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('No');
		vm.send('\033[B') # down
		vm.sendline('\r')

		vm.expect('Password:');
		vm.sendline(mok_password + '\r')

		vm.expect('OK');
		vm.sendline('\r')
	except:
		unexpected (vm, 'failed to delete MOK')

def test_mok (vm):
	execute_cmd(vm, 'mokutil -t mok_key.der')
	i = vm.expect(['is not enrolled', 'is already enrolled'])
	if i == 0 or i == 1:
		return i
	else:
		unexpected(vm, 'failed to test MOK')

def main (argv):
	vm_img = None
	logfile = None
	out_log = None
	mok_key = None
	password = None

	firmware = "/usr/share/qemu/ovmf-x86_64-suse.bin"

	# parse the arguments
	try:
		opts, args = getopt.getopt(argv,"hk:l:p:u:v:",["key=", "log=", "password=", "uefi=","vm_image="])
	except getopt.GetoptError:
		print_help()
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print_help()
			sys.exit()
		elif opt in ("-k", "--key"):
			mok_key = arg
		elif opt in ("-l", "--log"):
			logfile = arg
		elif opt in ("-u", "--uefi"):
			firmware = arg
		elif opt in ("-p", "--password"):
			password = arg
		elif opt in ("-v", "--vm_image"):
			vm_img = arg

	if vm_img == None or mok_key == None or password == None:
		print_help()
		sys.exit(2)

	# prepare for the test
	username='root'
	mok_password = password

	# create a temporary dir
	share_dir = tempfile.mkdtemp(prefix="moktest-")

	mem_size = "1024"
	backing_img = vm_img + '.backing'

	qemu_cmd = "qemu-system-x86_64 -enable-kvm -nographic"
	qemu_cmd += " -hda " + backing_img
	qemu_cmd += " -bios " + firmware
	qemu_cmd += " -m " + mem_size
	qemu_cmd += " -fsdev local,id=exp,path=" + share_dir + ",security_model=mapped-file"
	qemu_cmd += " -device virtio-9p-pci,fsdev=exp,mount_tag=v_share"

	if logfile != None:
		out_log = file(logfile,'w')

	print 'Auto Test Start'

	# create the backing image
	img_cmd = 'qemu-img create -f qcow2 -b ' + vm_img + ' ' + backing_img
	subprocess.check_call(img_cmd.split(), stdout=subprocess.PIPE)

	# copy the key to share_dir
	shutil.copyfile(mok_key, share_dir + "/mok_key.der")

	# Start the Virtual Machine
	vm = pexpect.spawn(qemu_cmd, logfile=out_log)

	login(vm, username, password)

	# mount the share directory
	execute_cmd(vm, 'mkdir share')
	execute_cmd(vm, 'mount -t 9p -o trans=virtio v_share share -oversion=9p2000.L')
	# copy the key
	execute_cmd(vm, 'cp -f share/mok_key.der mok_key.der')
	# umount the share directory
	execute_cmd(vm, 'umount share')
	execute_cmd(vm, 'rm -rf share')
	shutil.rmtree(share_dir)

	i = test_mok(vm)
	if i == 0:
		test_item = "enroll"
	elif i == 1:
		test_item = "delete"

	while True:
		if test_item == "enroll":
			enroll_mok(vm, mok_password)
		elif test_item == "delete":
			delete_mok(vm, mok_password)

		login(vm, username, password)

		i = test_mok(vm)
		if i == 0 and test_item == "delete":
			print 'MOK delete [PASSED]'
			test_item = "done"
		elif i == 1 and test_item == "enroll":
			print 'MOK enroll [PASSED]'
			test_item = "delete"
		else:
			print 'MOK ' + test_item + ' [FAILED]'
			unexpected(vm, 'test item ' + test_item)

		if test_item == "done":
			break

	# All done!
	vm.terminate()

	os.remove(backing_img)

	print "DONE!"

if __name__ == "__main__":
	main(sys.argv[1:])
