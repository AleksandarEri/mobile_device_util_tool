import os
import platform
import subprocess
import math
import collections
import re
import threading
import time

class IOSDeviceConnector(object):
	def __init__(self):
		super(IOSDeviceConnector, self).__init__()
		self.devicesPath = os.getcwd() + "/utils/iosloginfo/sdsdeviceid.exe"
		self.deviceInfo = os.getcwd() + "/utils/iosloginfo/sdsdeviceinfo.exe"
		self.deviceLog = os.getcwd() + "/utils/iosloginfo/sdsiosloginfo.exe"
		self.deviceCrash = os.getcwd() + "/utils/iosloginfo/sdsioscrashlog.exe"
		self.operation_executor = {
			"devices": self.devicesPath,
			"device_info": self.deviceInfo,
			"device_log": self.deviceLog,
			"device_crash": self.deviceCrash
		}
		self.result = []
		self.current_device_name = None
		self.devices_info = collections.OrderedDict()
		self.operation_dict = {
			"devices" : {
				"args": "-l -d",
				"process_function" : self.devices
			}
		}
		
	def process_args(self, args):
		print("Processing args: " +str(args))
		if (args[0] in self.operation_dict.keys()):
			operation_attributes = self.operation_dict[args[0]]
			self.current_device_name = args[1]
			self.call(operation_attributes["args"].format(args = args), operation_attributes["process_function"])
			return True
		return False
		
	def call(self, operator, command, process_function):
		self.result = None
		command_result = ''
		command_text = self.operation_executor[operator] + ' %s' % command
		print("iOS Command: " +command_text)
		results = subprocess.Popen(command_text, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
		lines = []
		self.result = []
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
		
	def devices(self, line):
		if not line.startswith("List of devices attached"):
			device_name = line.replace("device", "")
			if len(device_name) > 0:
				self.result.append(device_name)
	
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
	
