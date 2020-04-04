import os
import os.path
import collections
import subprocess
import threading
import tkinter as tk
import tkinter.ttk as ttk
import winsound
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
try:
	import winsound
except:
	pass
try:
	import queue
except ImportError:
	import Queue as queue

from app_ios_device_connector import IOSDeviceConnector
from app_async_logcat import AsyncLogcatReader
from app_async_logcat_writer import AsyncLogcatWriter
from app_async_console import ThreadSafeConsole, StdoutRedirector, StderrRedirector

class TabIOS(tk.Frame):
	def __init__(self, parent):
		if parent is not None:
			tk.Frame.__init__(self, parent.nTabs)
		else:
			tk.Frame.__init__(self, None)
		self.parent = parent
		self.label = "iOS"
		self.iOSDC = IOSDeviceConnector()
		self.list_of_connected_devices = {}
		
		if parent is not None:
			parent.nTabs.add(self, text = self.label)
		
		self.grid_columnconfigure(0, weight = 1, minsize = 100)
		self.grid_columnconfigure(1, weight = 1, minsize = 150)
		self.grid_columnconfigure(2, weight = 1, minsize = 300)
		self.buttons = []
		self.rootDir = os.getcwd() if self.parent == None else self.parent.rootDir
		self.buildGUI()
		
	# Run Game Parameters
	def buildGUI(self):
		idcDevicesResult = self.iOSDC.call("devices", self.iOSDC.operation_dict["devices"]["args"], self.iOSDC.devices);
		# self.adb.get_sd_free_space()
		if isinstance(idcDevicesResult, list):
			if len(idcDevicesResult) > 1:
				for x in range(len(idcDevicesResult)):
					if len(idcDevicesResult[x]) > 0:
						value = idcDevicesResult[x]
						self.list_of_connected_devices[value] = x
			else:
				if len(idcDevicesResult) > 0:
					self.list_of_connected_devices[idcDevicesResult[0]] = 1
		
		self.lDevices = tkinter.LabelFrame(self, text = "Devices", padx = 5, pady = 5)
		self.lDevices.grid(column = 0, row = 0, columnspan = 2, rowspan = 3, sticky = "NSWE", padx = 5, pady = 5)
		
		self.bRefreshDevices = tkinter.Button(self.lDevices, text = "Refresh", padx = 5, command = None)
		self.bRefreshDevices.grid(column = 0, row = 1, sticky = "WNSE", pady=3)
		
		self.cbDevices = tkinter.ttk.Combobox(self.lDevices, state = "readonly", textvariable = self.list_of_connected_devices, width = 25)
		self.cbDevices.config(values = [""] + list(self.list_of_connected_devices.keys()))
		self.cbDevices.bind("<<ComboboxSelected>>", self.on_device_selected)
		self.cbDevices.grid(column = 0, row = 0, columnspan = 2, sticky = "N")
		self.cbDevices.set("")
		
		self.iOSFilter = tkinter.StringVar()
		self.iOSFilter.trace("w", lambda name, index, mode: None )
		
		self.optLogToFile = tk.BooleanVar()
		self.optLogToFile.set(False)
		
		self.chLogToFile = ttk.Checkbutton(self.lDevices, text = "Log to File", variable = self.optLogToFile, command = None)
		self.chLogToFile.grid(column = 1, row = 1, sticky = 'W')
		
		
		self.eSearchScenes = tkinter.Entry(self, textvariable = self.iOSFilter)
		self.eSearchScenes.grid(row = 3, column = 0, columnspan=2, sticky = "ENW")
		
		self.bSearch = tkinter.ttk.Button(self, text = "Search",	command = self.search_in_logs )
		self.bSearch.grid(column = 2, row = 3, sticky = "W")
		self.buttons += [self.bSearch]
		
		self.bClear = tkinter.ttk.Button(self, text = "Clear",	command = self.clear_search )
		self.bClear.grid(column = 2, row = 3, sticky = "E", columnspan=1)
		self.buttons += [self.bClear]
		
		self.bRefresh = tkinter.ttk.Button(self, text = "Refresh",	command = self.refresh_search )
		self.bRefresh.grid(column = 3, row = 3, sticky = "ENW")
		self.buttons += [self.bRefresh]
		
		# Get Console log for device
		self.bListDeviceUdids = ttk.Button(self.lDevices, text = "Get Console Log", command = self.start_console_process, width = 15)
		self.bListDeviceUdids.grid(column = 0, row = 2, sticky = 'WN', pady = 5)
		self.buttons += [self.bListDeviceUdids]
		
		self.bCrashLogs = ttk.Button(self.lDevices, text = "Get Crash Log", command = self.get_crash_log, width = 15)
		self.bCrashLogs.grid(column = 1, row = 2, sticky = 'WN', pady = 5)
		self.buttons += [self.bCrashLogs]
		
		self.outputFont = tkinter.font.Font(family="Courier", size=10)
		self.txtOutput = ThreadSafeConsole(self, wrap='word', font = self.outputFont, bg="black", fg="white")
		self.txtOutput.grid(column = 0, row = 4, sticky='NSWE', padx=5, pady=5, columnspan=4)
		self.txtOutput.insert(tkinter.END, "Device Log" + os.linesep + "-----------" + os.linesep + os.linesep)
		self.sConsole = tkinter.Scrollbar(self, orient = tkinter.VERTICAL)
		self.sConsole.config(command = self.txtOutput.yview)
		self.sConsole.grid(column = 5, row = 4, sticky = 'NSEW', ipady=20)
		self.txtOutput.config(yscrollcommand=self.sConsole.set)
		
	
	def printFromMain(self):
		print("msg")
		
	def search_in_logs(self, event = None):
		search_term = self.iOSFilter.get()
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(search_term)
		self.txtOutput.show_results(search_term)
		
	def clear_search(self, event = None):
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(None)
		self.iOSFilter.set(None)
		self.eSearchScenes.config(textvariable = None)
		
	def refresh_search(self, event = None):
		search_term = self.iOSFilter.get()
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(search_term)
		self.txtOutput.show_results(search_term)
		
	def update_scene_list(self):
		search_term = self.sceneSearchVar.get()
		self.txtOutput.setFilter(search_term)
		
	def start_console_process(self):
		device_name = str(self.cbDevices.get())
		print("Device: "+ device_name)
		self.iOSDC.current_device_name = device_name.rstrip('\t')
		command_param = [self.iOSDC.deviceLog, "-u", self.iOSDC.current_device_name, "-d"]
		print("Command: " + repr(command_param))
		self.iOSDC.logcat = subprocess.Popen(command_param, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
		self.iOSDC.stdout_queue = queue.Queue()
		self.iOSDC.stdout_reader = AsyncLogcatReader(self.iOSDC.logcat, self.iOSDC.stdout_queue, None, device_name)
		self.iOSDC.stdout_reader.start()
		self.console_writer = AsyncLogcatWriter(self, self.iOSDC.stdout_reader, self.iOSDC.stdout_queue, 2000, device_name)
		self.console_writer.start()
		self.bListDeviceUdids.config(text = 'Stop Console')
		
	def get_crash_log(self):
		print("Not implemented")
		
	def on_device_selected(self, event = None):
		device_name = str(self.cbDevices.get())
		self.iOSDC.current_device_name = device_name
		
	def listdevices(self):
		device_ids = os.path.join(os.getcwd(), "utils", "iosloginfo", "sdsdeviceid.exe")
		command = [device_ids, "-l", "-d"]
		self.call_subprocess(command)
	
	def call_subprocess(self, command):
		print("Trying to call: " + repr(command))
		results = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
		lines = []
		self.filter_output(results, lines)
		results.communicate()
		if results.returncode != 0:
			return results.returncode
		else:
			return results.returncode

	def filter_output(self, process, lines):
		line = process.stdout.readline()
		while line:
			lines.append(line.decode("utf-8").rstrip("\r\n"))
			print("	 " + lines[-1])
			line = process.stdout.readline()
		else:
			line = process.stderr.readline()

	def on_from_sound_selected(self, event = None):
		pass
	
	def on_to_sound_selected(self, event = None):
		pass
		
	def update_convert_options(self, event = None):
		pass
		
	def on_language_selected(self, event = None):
		pass
	
	def enableButtons(self):
		for button in self.buttons:
			button.config(state = "normal")

	def disableButtons(self, clickedButton):
		for button in self.buttons:
			if button != clickedButton:
				button.config(state = "disabled")
	
	#Manager methods
	def show_error(self, msg):
		self.manager.show_error(msg)
	
if __name__ == "__main__" :
	tabIOS= TabIOS(None);