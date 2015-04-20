import qemu
import time

def execute_cmd_wait (vm_control, cmd, timeout):
	try:
		vm_control.pexpect_serial(' [#\$]', timeout)
		vm_control.write_serial(cmd)
	except:
		print "Could not execute " + cmd

def execute_cmd (vm_control, cmd):
	execute_cmd_wait(vm_control, cmd, -1)

def boot_and_login (vm_control, password):
	# grub2
	vm_control.match_partial_screen_wait("os13.2-grub2.png", 5, 3, 0, 800, 0, 200)
	print "grub2"
	vm_control.sendkey("ret")

	# Wait the image setup
	vm_control.pexpect_serial(" login: ", 300)
	vm_control.write_serial("root")
	vm_control.pexpect_serial('[pP]assword: ', 120)
	vm_control.write_serial(password)

def install_mokutil(vm_control):
	execute_cmd_wait(vm_control, "zypper ref", 300)
	execute_cmd_wait(vm_control, "zypper in -l -f mokutil", 300)
	vm_control.pexpect_serial("Continue? \[y/n/? shows all options\] (y):", 10)
	vm_control.write_serial("y")

def install_shim (vm_control):
	print "mount share"

	execute_cmd(vm_control, "mkdir share")
	execute_cmd(vm_control, "mount -t 9p -o trans=virtio v_share share -oversion=9p2000.L")

	# TODO Copy and install shim
	time.sleep(60)

	print "umount share"
	# umount the share directory
	execute_cmd(vm_control, "umount share")
	execute_cmd(vm_control, "rm -rf share")
