#!/usr/bin/python

import os
import sys
import pexpect
import subprocess

mok_key = 'whatever.der'

username='root'
password=' '
mok_password = password

disk = "os-13.1-minimal.img"
firmware = "/usr/share/qemu/ovmf-x86_64-suse.bin"
mem_size = "1024"
share_dir = "share"
logfile = 'automate.log'
#logfile = None

qemu_cmd = "qemu-system-x86_64 -enable-kvm -nographic"
if disk != None:
	backing_img = disk + '.backing'
	qemu_cmd += " -hda " + backing_img
if firmware != None:
	qemu_cmd += " -bios " + firmware
if mem_size != None:
	qemu_cmd += " -m " + mem_size
if share_dir != None:
	qemu_cmd += " -fsdev local,id=exp,path=" + share_dir + ",security_model=mapped-file"
	qemu_cmd += " -device virtio-9p-pci,fsdev=exp,mount_tag=v_share"

if logfile != None:
	out_log = file(logfile,'w')
else:
	out_log = sys.stdout

print 'Auto Test Start'

# create the backing image
img_cmd = 'qemu-img create -f qcow2 -b ' + disk + ' ' + backing_img
subprocess.check_call(img_cmd.split(), stdout=subprocess.PIPE)

# TODO check share_dir

def unexpected (vm, message):
	print "UNEXPECTED: " + message
	vm.terminate()
	os.remove(backing_img)
	sys.exit(1)

def login (vm):
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

def enroll_mok (vm):
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

def delete_mok (vm):
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

# Start the Virtual Machine
vm = pexpect.spawn(qemu_cmd, logfile=out_log)

# log user into the system
login(vm)

# mount the share directory
execute_cmd(vm, 'mkdir share')
execute_cmd(vm, 'mount -t 9p -o trans=virtio v_share share -oversion=9p2000.L')
# copy the key
execute_cmd(vm, 'cp -f share/' + mok_key + " mok_key.der")
# umount the share directory
execute_cmd(vm, 'umount share')
execute_cmd(vm, 'rm -rf share')

while True:
	i = test_mok(vm)
	if i == 0:
		enroll_mok(vm)
		test_item = "enroll";
	elif i == 1:
		delete_mok(vm)
		test_item = "delete";

	login(vm)

	i = test_mok(vm)
	if i == 0 and test_item == "delete":
		print 'MOK delete [PASSED]'
		test_item = "done"
	elif i == 1 and test_item == "enroll":
		print 'MOK enroll [PASSED]'
	else:
		print 'MOK ' + test_item + ' [FAILED]'
		unexpected(vm, 'test item ' + test_item)

	if test_item == "done":
		break

# All done!
execute_cmd(vm, 'shutdown -h now')

vm.wait()

os.remove(backing_img)

print "DONE!"
