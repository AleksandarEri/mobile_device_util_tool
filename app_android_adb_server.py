import os
import platform
import subprocess
import math
import collections
import re
import threading
import time
try: 
	import queue
except ImportError:
	import Queue as queue

from app_async_logcat import AsyncLogcatReader

class DeviceInfo(object):
	def __init__(self):
		super(DeviceInfo, self).__init__()
		self.free_disk_path = ""
		self.free_disk_size = ""
		self.os_version = ""
		self.device_model = ""
		self.device_api_level = 15
		self.device_applications = []
		
	def set_os_version(self, os_version):
		self.os_version = os_version
	
	def set_free_disk_path(self, path):
		self.free_disk_path = path;
		
	def set_device_model(self, device_model):
		self.device_model = device_model
		
	def set_device_api_level(self, device_api_level):
		self.device_api_level = device_api_level
		
	def add_application(self, application):
		if application not in self.device_applications:
			self.device_applications.append(application)
		
class MemoryInfo(object):
	def __init__(self, type, params):
		self.type = type
		self.params = params
		
	def print_memory_info_for_type(self):
		print("Type: " + self.type)
		print("Params: " + str(self.params))
		# print("PSS: " + str(int(self.params[0]) / 1024) + " MB ")
		# print("Shared Dirty: " + str(int(self.params[1]) / 1024) + " MB")
		# print("Shared Private: " + str(int(self.params[2]) / 1024) + " MB")
		# if self.type == "TOTAL" or self.type == "Native":
			# print("Heap Size: " + str(int(self.params[3]) / 1024) + " MB")
			# print("Heap Alloc: " + str(int(self.params[4]) / 1024) + " MB")
			# print("Heap Free: " + str(int(self.params[5]) / 1024) + " MB")
	
	
class ProfileMemory(object):
	""" 
	The run() method will be started and it will run in the background
	until the application exits.
	"""
	def __init__(self, adb, app_id, interval=1):
		""" Constructor
		:type interval: int
		:param interval: Check interval, in seconds
		"""
		self.interval = interval
		self.adb = adb
		self.stop_profiling = False
		self.app_id = app_id
		self.build_parameters  = collections.defaultdict(lambda: 0)
		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True							 # Daemonize thread
		self.thread.start()									 # Start the execution
		
		
	def setAppIdToProfile(self, app_id):
		self.app_id = app_id
	
	def terminate_profiler(self):
		self.stop_profiling = True
		
	def run(self):
		""" Method that runs forever """
		while not self.stop_profiling:
			# Do something
			commandParams = ["memory_dump", self.app_id]
			self.adb.process_args(commandParams)
			
			for mem_info_obj in self.adb.memory_info:
				mem_info_obj.print_memory_info_for_type()
				
			self.adb.memory_info = []
			
			time.sleep(self.interval)
			
class ProfileCPU(object):
	""" Threading example class
	The run() method will be started and it will run in the background
	until the application exits.
	"""
	def __init__(self, interval=10):
		""" Constructor
		:type interval: int
		:param interval: Check interval, in seconds
		"""
		self.interval = interval
		self.adb = ADB()
		self.stop_profiling = False
		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True							 # Daemonize thread
		self.thread.start()									 # Start the execution
	
	def terminate_profiler(self):
		self.stop_profiling = True
		
	def run(self):
		""" Method that runs forever """
		while not self.stop_profiling:
			# Do something
			
			command = "dumpsys cpuinfo | grep " + application_id
			commandParams = ["cpuinfo", command]
			self.adb.process_args(commandParams)
			
			for mem_info_obj in self.adb.memory_info:
				mem_info_obj.print_memory_info_for_type()
				
			self.adb.memory_info = []
			
			time.sleep(self.interval)
	
class ADB(object):
	def __init__(self):
		super(ADB, self).__init__()
		self.adbPath = os.getcwd() + "/utils/adb/adb.exe"
		self.result = None
		self.current_device_name = None
		self.devices_info = collections.OrderedDict()
		self.memory_info = []
		self.last_screenshot_id = 0;
		self.operation_dict = {
			"devices" : {
				"args": "devices",
				"process_function" : self.devices
			},
			"upload" : {
				"args": "-s {args[1]} push {args[2]} {args[3]}",
				"process_function": self.upload
			},
			"get" : {
				"args": "-s {args[1]} pull {args[2]} {args[3]}",
				"process_function": self.get
			},
			"install" : {
				"args": "-s {args[1]} install {args[2]} {args[3]}",
				"process_function": self.install
			},
			"makeDir" : {
				"args": "-s {args[1]} shell mkdir {args[2]}",
				"process_function": self.makeDir
			},
			"make_dir_current_device": {
				"args": "shell mkdir {args[1]}",
				"process_function": self.makeDir
			},
			"reinstall" : {
				"args": "-s {args[1]} shell pm install -r {args[2]}",
				"process_function": self.reinstall
			},
			"uninstall" : {
				"args": "-s {args[1]} shell pm uninstall {args[2]}",
				"process_function": self.uninstall
			},
			"clearData" : {
				"args": "-s {args[1]} shell pm clear {args[2]}",
				"process_function": self.clearData
			},
			"shell" : {
				"args": "-s {args[1]} shell {args[2]}",
				"process_function": self.shell
			},
			"kill" : {
				"args": "kill {args[1]}",
				"process_function": self.kill
			},
			"memory_dump" : {
				"args": "shell dumpsys meminfo {args[1]}",
				"process_function": self.memory_dump_info
			},
			"check_has_device_root_access": {
				"args" : "-s {args[1]} su ",
				"process_function" : self.on_device_has_root_access
			},
			"copy_tombstones" : {
				"args" : "cp -r tombstones/* {args[1]}",
				"process_function" : self.on_copy_tombstones
			},
			"remove_dir": {
				"args": "shell {args[1]} rm -r {args[2]}",
				"process_function": self.on_cpu_info
			},
			"process_crash_dumps" : {
				"args" : "{args[1]} -sym {args[2]} -dump {args[3]} > {args[4]}",
				"process_function" : self.on_process_crash_dumps
			},
			"get_os_version": {
				"args": "-s {args[1]} shell getprop ro.build.version.release",
				"process_function": self.on_get_os_version
			},
			"get_free_space_location": {
				"args": "-s {args[1]} shell df ",
				"process_function": self.on_get_free_space_location
			},
			"take_screenshot": {
				"args": "shell screencap -p /sdcard/screenshots/{args[1]}",
				"process_function": self.on_screenshot_taken
			},
			"download_screenshots": {
				"args": "pull {args[1]} {args[2]}",
				"process_function": self.on_screenshots_downloaded
			},
			"get_next_screenshot_num": {
				"args": "shell ls -a {args[1]}",
				"process_function" : self.on_list_screenshots
			},
			"get_device_model": {
				"args": "-s {args[1]} shell getprop ro.product.brand",
				"process_function" : self.on_device_model
			},
			"get_device_api_level": {
				"args": "-s {args[1]} shell getprop ro.build.version.sdk",
				"process_function" : self.on_device_api_level
			},
			"cpuinfo": {
				"args": "shell \"{args[1]}\"",
				"process_function": self.on_cpu_info
			},
			"broadcast": {
				"args": "-s {args[1]} shell am broadcast -n \"{args[2]}/com.changeme.BroadcastReceiver\" --es CH \"{args[3]}\"",
				"process_function": self.on_broadcast_message
			},
			"list_packages": {
				"args": "-s {args[1]} shell pm list packages -3",
				"process_function": self.on_list_packages
			},
			"backup": {
				"args": "-s {args[1]} backup -noapk {args[2]}",
				"process_function": self.on_backup_application
			},
			"clear_purchase": {
				"args": "-s {args[1]) shell pm clear com.android.vending",
				"process_function": self.on_clear_purchases
			},
			"start_app": {
				"args": "-s {args[1]} shell am start -n {args[2]}/com.activity.to_start",
				"process_function": self.on_broadcast_message
			},
			"console": {
				"args": "-s {args[1]} logcat -v time",
				"process_function": self.on_console_output
			},
			"clear_log": {
				"args": "-s {args[1]} logcat -b all -c",
				"process_function": self.on_broadcast_message
			}
		}
		
	def get_logcat_lines(self):
		timeout=10000
		while not self.stdout_reader.eof():
			print("Trying to run reader")
			try:
				line = self.stdout_queue.get(timeout=timeout)
			except queue.Empty:
				print('%s\'s logcat output is silent for %d seconds. Considering that as steady state. Taking a snapshot with Collector now\n', self.package_name, timeout)
				break
			if line is None:
				break
			else:
				print(line)

	def logcat_start(self, package):
		return self.logcat('-v threadtime')

	def logcat_clean(self):
		return self.adb('logcat -c')
		
	def on_console_output(self, line):
		pass
		
	def on_clear_purchases(self, line):
		print(repr(line))
		
	def on_backup_application(self, line):
		print(repr(line))
		
	def on_list_packages(self, line):
		package_name = line[8:]
		self.devices_info[self.current_device_name].add_application(package_name)
		
	def on_broadcast_message(self, line):
		print("Received line: " + repr(line))
		
	def on_cpu_info(self, line):
		print("Line: " + str(line))
		
	def on_device_api_level(self, line):
		self.devices_info[self.current_device_name].set_device_api_level(str(line))
		return str(line)
		
	def on_device_model(self, line):
		self.devices_info[self.current_device_name].set_device_model(str(line))
		return str(line)
		
	def on_list_screenshots(self, line):
		if line is not None:
			try:
				self.last_screenshot_id = int(re.findall(r'\d+', str(line))[0])
			except:
				self.last_screenshot_id = 0
			
		print("Id: " + str(self.last_screenshot_id))
		
	def on_screenshot_taken(self, line):
		self.last_screenshot_id = self.last_screenshot_id + 1
	
	def on_screenshots_downloaded(self, line):
		print("Downloading images")
	
	def get_free_disk_location_for_device(self, device_name):
		if device_name in self.devices_info:
			return self.devices_info[device_name].free_disk_path
			
	def get_device_model_name(self, device_name):
		if device_name in self.devices_info:
			return self.devices_info[device_name].device_model
	
	def process_args(self, args):
		print("Processing args: " +str(args))
		if (args[0] in self.operation_dict.keys()):
			operation_attributes = self.operation_dict[args[0]]
			self.current_device_name = args[1]
			self.call(operation_attributes["args"].format(args = args), operation_attributes["process_function"])
			return True
		return False
		
	def call(self, command, process_function):
		self.result = None
		command_result = ''
		command_text = self.adbPath + ' %s' % command
		print("Command text: " +command_text)
		results = subprocess.Popen(command_text, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
		lines = []
		self.filter_output(results, lines, process_function)
		results.communicate()
		if results.returncode != 0:
			return results.returncode
		else:
			return self.result
		
	def filter_output(self, process, lines, process_function):
		line = process.stdout.readline()
		while line:
			lines.append(line.decode("utf-8").rstrip("\r\n"))
			print("	 " + lines[-1])
			if process_function is not None:
				process_function(lines[-1])
			line = process.stdout.readline()
		else:
			line = process.stderr.readline()
		
	def stop_adb_process(self):
		os.system('pkill adb.exe')
		
	def reconnect_adb_process(self):
		command_result = ''
		command_text = self.adbPath + ' reconnect '
		print("Command text: " +command_text)
		# results = os.popen(command_text, "r")
		result = subprocess.Popen(command_text, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
		#processOutput(result)
		result.communicate()
		if result.returncode != -1:
			print("Error within adb")
			return result.returncode
		else:
			return result
		
	def start_adb_process(self, command):
		command_result = ''
		command_text = self.adbPath + ' %s' % command
		print("Command text: " +command_text)
		# results = os.popen(command_text, "r")
		result = subprocess.Popen(command_text, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
		#processOutput(result)
		result.communicate()
		if result.returncode != -1:
			print("Error within adb")
			return result.returncode
		else:
			return result
			
	def devices(self, line):
		if not line.startswith("List of devices attached"):
			device_name = line.replace("device", "")
			if len(device_name) > 0:
				self.result.append(device_name)
		else:
			self.result = []
			
	def memory_dump_info(self, line):
		match = re.split('\s+', line.strip())
		# Skip data after the 'App Summary' line.  This is to fix builds where
		# they have more entries that might match the other conditions.
		if len(match) >= 2 and match[0] == 'App' and match[1] == 'Summary':
			print("Skipping Header")
		else:
			if "Unknown" in match[0] or "TOTAL" in match[0] or "Native" in match[0]:
				params = []
				for i in range(1, len(match)):
					params.append(match[i])
					
				meminfo_obj = MemoryInfo(str(match[0]), params)
				self.memory_info.append(meminfo_obj)
			
		
	def on_device_has_root_access(self, line):
		print("Line: " +line)
		
	def on_copy_tombstones(self, line):
		print("Line: " +line)
	
	def on_process_crash_dumps(self, line):
		print("Line: " +line)
		
	def get_crash_dump(self, line):
		print("Line: " +line)
		
	def on_get_os_version(self, line):
		if len(line) > 0:
			major_version = line.split('.')[0]
			self.result = int(major_version)
		
	def on_get_free_space_location(self, line):
		line_prefixes = ["storage","/mnt/shell"]
		device_info_obj = None;
		if self.current_device_name in self.devices_info:
			if self.devices_info[self.current_device_name] != None:
				device_info_obj = self.devices_info[self.current_device_name]
		else:
			device_info_obj = DeviceInfo()
			self.devices_info[self.current_device_name] = device_info_obj
		
		for line_prefix in line_prefixes:
			if line_prefix in line and not "knox-emulated" in line:
				lines = line.split('\n')
				lines[0] = lines[0].replace('Mounted on', 'Mounted_on')
				data = lines[0].split()
				if len(data) >= 4:
					if len(device_info_obj.free_disk_size) > 0:
						device_info_size_letter = device_info_obj.free_disk_size[-1:]
						device_info_size_value = device_info_obj.free_disk_size[:-1]
					
						size_suffix_letter = data[3][-1:]
						size_value = data[3][:-1]
					
						# check if letters are the same then compare values
						if device_info_size_letter == size_suffix_letter:
							if device_info_size_value <= size_value:
								device_info_obj.free_disk_size = str(data[3])
								device_info_obj.free_disk_path = data[0]
						else:
							if size_suffix_letter == "G" and device_info_size_letter == "M":
								device_info_obj.free_disk_size = str(data[3])
								device_info_obj.free_disk_path = data[0]
							elif size_suffix_letter == "M" and device_info_size_letter == "K":
								device_info_obj.free_disk_size = str(data[3])
								device_info_obj.free_disk_path = data[0]
					else:
						device_info_obj.free_disk_size = str(data[3])
						device_info_obj.free_disk_path = data[0]
						
	def get_obb_path_for_device(self, device_name):
		device_info_obj = self.devices_info[device_name]
		if "mnt/shell/emulated" in device_info_obj.free_disk_path:
			return device_info_obj.free_disk_path + "/obb/"
		if "mnt/shell/container" in device_info_obj.free_disk_path:
			return "mnt/shell/emulated" + "/obb/"
			
		return device_info_obj.free_disk_path + "/Android/obb/"
		
	def get_sd_free_space(self):
		# TODO: Improve this
		result = self.call("shell df /storage/emulated")
		print("Result: " +str(result))
		free = result
		# for nexus it is in sdcard/Android/obb
		return free

	def upload(self, line):
		print(line)

	def get(self, line):
		print(line)

	def install(self, line):
		print(line)

	def makeDir(self, line):
		print(line)

	def reinstall(self, line):
		print(line)

	def uninstall(self, line):
		print(line)

	def clearData(self, line):
		print(line)

	def shell(self, line):
		print(line)
		
	def kill(self, line):
		print(line)
	
	def start(self, app):
		pack = app.split()
		result = "Nothing to run"
		if pack.length == 1:
			result = self.call("shell am start " + pack[0])	   
		elif pack.length == 2:
			result = self.call("shell am start " + pack[0] + "/." + pack[1])
		elif pack.length == 3:
			result = self.call("shell am start " + pack[0] + " " + pack[1] + "/." + pack[2])
		return result

	def screen(self, res):
		result = self.call("am display-size " + res)
		return result

	def dpi(self, dpi):
		result = self.call("am display-density " + dpi)
		return result

	def screenRecord(self, param):
		params = param.split()
		if params.length == 1:
			result = self.call("shell screenrecord " + params[0])
		elif params.length == 2:
			result = self.call("shell screenrecord --time-limit " + params[0] + " " + params[1])
		return result

	def screenShot(self, output):
		self.call("shell screencap -p /sdcard/temp_screen.png")
		self.get("/sdcard/temp_screen.png", output)
		self.call("shell rm /sdcard/temp_screen.png")
