#!/usr/bin/python

import sys
import pexpect

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
	qemu_cmd += " -hda " + disk
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

print "QEMU command: " + qemu_cmd

# TODO check share_dir

def login (vm):
	vm.expect(' login: ', timeout=120)
	vm.sendline(username)
	vm.expect('Password: ')
	vm.sendline(password)

def execute_cmd (vm, cmd):
	try:
		vm.expect(' [#\$]')
		vm.sendline(cmd)
	except:
		print 'EXCEPT: ' + cmd
		vm.interact()

def enroll_mok (vm):
	execute_cmd(vm, 'mokutil -P -i mok_key.der')
	# reboot to MokManager
	execute_cmd(vm, 'reboot')

	try:
		vm.expect('Shim UEFI key management', timeout=300)
		vm.send(' ')
	except:
		print 'EXCEPT'
		vm.interact()

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

def delete_mok (vm):
	execute_cmd(vm, 'mokutil -P -d mok_key.der')
	# reboot to MokManager
	execute_cmd(vm, 'reboot')

	try:
		vm.expect('Shim UEFI key management', timeout=300)
		vm.send(' ')
	except:
		print 'EXCEPT'
		vm.interact()

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


# Start the Virtual Machine
vm = pexpect.spawn(qemu_cmd, logfile=out_log)
vm.setecho(False)

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

execute_cmd(vm, 'mokutil -t mok_key.der')
i = vm.expect(['is not enrolled', 'is already enrolled'])
if i == 0:
	print 'Enroll ' + mok_key
	enroll_mok(vm)
	test_item = "enroll";
elif i == 1:
	print 'Delete' + mok_key
	delete_mok(vm)
	test_item = "delete";
else:
	print 'IMPOSSIBLE!!!'
	vm.interact()

login(vm)

execute_cmd(vm, 'mokutil -t mok_key.der')
i = vm.expect(['is not enrolled', 'is already enrolled'])
if i == 0:
	print mok_key + ' is not in the list'
elif i == 1:
	print mok_key + ' is in the list'
else:
	print ':-('
	vm.interact()

# All done!
print 'shutdown the machine'
execute_cmd(vm, 'shutdown -h now')

vm.wait()
print "DONE!"
