import os
import sys
import os.path
import collections
import subprocess
import threading
import time
import json
import base64
import binascii
import tkinter as tk
import tkinter.ttk as ttk
import winsound
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog

try: 
	import queue
except ImportError:
	import Queue as queue

from app_async_logcat import AsyncLogcatReader
from app_async_logcat_writer import AsyncLogcatWriter
from app_async_console import ThreadSafeConsole, StdoutRedirector, StderrRedirector
from app_android_adb_server import ADB, ProfileMemory
from app_ios_device_connector import IOSDeviceConnector
from app_device_log_tab import DeviceLogTab

def processOutput(process):
	while True:
		line = process.stdout.readline()
		if not line:
			line = process.stderr.readline()
		if not line:
			break
		else:
			print("	 " + line.decode("utf-8").rstrip("\r\n"))

class TabQA(tk.Frame):
	def __init__(self, parent):
		if parent is not None:
			tk.Frame.__init__(self, parent.nTabs)
		else:
			tk.Frame.__init__(self, None)
		self.parent = parent
		self.label = "Android"
		self.sceneList = [] # Scenes
		self.adb = ADB()
		self.list_of_connected_devices = {}
		self.installedApps = {}
		self.selected_device = None
		
		if parent is not None:
			parent.nTabs.add(self, text = self.label)
		
		self.grid_columnconfigure(0, weight = 1, minsize = 150)
		self.grid_columnconfigure(1, weight = 1, minsize = 150)
		self.grid_columnconfigure(2, weight = 1, minsize = 300)
		self.buttons = []
		self.rootDir = os.getcwd()() if self.parent == None else self.parent.rootDir
		
		# Thread for scrcpy
		self.scrycopy_thread = None
		
		self.device_tabs = {}
		
		self.buildGUI()
		
	# Run Game Parameters
	def buildGUI(self):		
		# Devices
		adbDevicesResult = self.adb.call("devices", self.adb.devices);
		self.deviceOSVersions = {}
		# self.adb.get_sd_free_space()
		if isinstance(adbDevicesResult, list):
			if len(adbDevicesResult) > 1:
				for x in range(len(adbDevicesResult)):
					if len(adbDevicesResult[x]) > 0:
						value = adbDevicesResult[x]
						self.list_of_connected_devices[value] = x
			else:
				if len(adbDevicesResult) > 0:
					self.list_of_connected_devices[adbDevicesResult[0]] = 1
		
		self.lDevices = tkinter.LabelFrame(self, text = "Devices", padx = 5, pady = 5)
		self.lDevices.grid(column = 0, row = 0, columnspan = 2, rowspan = 3, sticky = "NSWE", padx = 5, pady = 5)
		
		self.bRefreshDevices = tkinter.Button(self.lDevices, text = "Refresh", padx = 5, command = self.refresh_devices)
		self.bRefreshDevices.grid(column = 3, row = 2, sticky = "WNSE", pady=3)
		
		self.bShowConsole = tkinter.Button(self.lDevices, text = "Show Console", padx = 5, command = self.start_console_process )
		self.bShowConsole.grid(column = 3, row = 3, sticky = "WNSE", pady=3)
		
		self.cbDevices = tkinter.ttk.Combobox(self.lDevices, state = "readonly", textvariable = self.list_of_connected_devices, width = 25)
		self.cbDevices.config(values = [""] + list(self.list_of_connected_devices.keys()))
		self.cbDevices.bind("<<ComboboxSelected>>", self.on_device_selected)
		self.cbDevices.grid(column = 0, row = 0, columnspan = 2, sticky = "N")
		self.cbDevices.set("")
		
		# Run Game
		self.lfApplicationUtils = tk.LabelFrame(self, text="Application Scripts", padx = 5, pady = 5)
		self.lfApplicationUtils.grid(column = 2, row = 0, sticky = 'NEWS', padx = 5, pady = 5)
		
		self.lfApplicationUtils.grid_columnconfigure(0, weight = 1)
		self.lfApplicationUtils.grid_columnconfigure(1, weight = 1)
		
		# Scrcpy
		self.optRecordScreen = tk.BooleanVar()
		self.optRecordScreen.set(False)
		
		self.optLogToFile = tk.BooleanVar()
		self.optLogToFile.set(False)
		
		self.chRecordScreen = ttk.Checkbutton(self.lDevices, text = "Record Screen", variable = self.optRecordScreen, command = None)
		self.chRecordScreen.grid(column = 0, row = 1, sticky = 'W')
		
		self.chLogToFile = ttk.Checkbutton(self.lDevices, text = "Log to File", variable = self.optLogToFile, command = self.update_log_to_file_for_device)
		self.chLogToFile.grid(column = 1, row = 1, sticky = 'W')
		
		self.btnShowDevice = ttk.Button(self.lDevices, text = "Show Device", command = self.show_device, width = 15)
		self.btnShowDevice.grid(column = 0, row = 2, sticky = 'W', pady = 3)
		
		self.btnMemoryInfo = ttk.Button(self.lDevices, text = "MemoryInfo", command = self.memory_info, width = 15)
		self.btnMemoryInfo.grid(column = 1, row = 2, sticky = 'W', pady = 3)
		
		self.lDevicesLogs = tkinter.LabelFrame(self, text = "Devices Logs", padx = 5, pady = 5)
		self.lDevicesLogs.grid(column = 0, row = 4, sticky='NSWE', padx=5, pady=5, columnspan=5)
		
		
		self.nTabs = tkinter.ttk.Notebook(self.lDevicesLogs)
		self.nTabs.grid(sticky = 'WENS')
		
		

	def memory_info(self):
		app = self.selected_application.get()
		print("Application: " + app )
		self.memory_profiler = ProfileMemory(self.adb, app, 2)
		
	def update_log_to_file_for_device(self, event = None):
		selected_device = self.selected_device.strip('\t')
		device_log = self.device_tabs[selected_device]
		device_log.setLogToFile(self.optLogToFile)
		
	def refresh_devices(self, event = None):
		self.list_of_connected_devices = {}
		adbDevicesResult = self.adb.call("devices", self.adb.devices);
		self.deviceOSVersions = {}
		# self.adb.get_sd_free_space()
		
		if isinstance(adbDevicesResult, list):
			if len(adbDevicesResult) > 1:
				for x in range(len(adbDevicesResult)):
					key = "Device" + str(x)
					value = adbDevicesResult[x]
					self.list_of_connected_devices[value] = x
			else:
				if len(adbDevicesResult) > 0:
					self.list_of_connected_devices[adbDevicesResult[0]] = 1
				
		self.cbDevices.config(values = [""] + list(self.list_of_connected_devices.keys()))
		self.cbDevices.bind("<<ComboboxSelected>>", self.on_device_selected)
		
	def update_debug_scene_list(self):
		search_term = self.sceneSearchVar.get()
		self.lbSceneList.delete(0, tk.END)
		for item in self.sceneList:
			if search_term.lower() in item.lower():
				if item.find("/") != -1:
					idx = item.find("/") + 1
					substring = item[:idx]
					item = item.replace(substring, "	")
				
	def show_device(self, event = None):
		os.environ['ADB'] = self.adb.adbPath
		self.scrycopy_thread = threading.Thread(target=self.start_scrycopy_process, args=())
		self.scrycopy_thread.daemon = True
		self.scrycopy_thread.start()
		
		
	def start_console_process(self):
		device_log = self.device_tabs[self.selected_device]
		device_log.show_console()
		
	def start_scrycopy_process(self):
		scrcpy_path = os.path.join(os.getcwd(), "utils","scrcpy","scrcpy.exe")
		command_param = [scrcpy_path, "-s", self.adb.current_device_name.rstrip('\t')]
		if self.optRecordScreen.get():
			command_param.append("-r screen.mp4")
		process = subprocess.Popen(command_param, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		processOutput(process)
				
	def on_item_selected(self, event = None):
		item_selected = self.items.get()
		self.item_selected = item_selected
				
	def on_device_selected(self, event = None):
		device_name = str(self.cbDevices.get())
		if len(device_name) > 0:
			device_name = device_name.strip('\t')
			commandParams = ["get_os_version", device_name]
			self.adb.process_args(commandParams)
			self.deviceOSVersions[device_name] = self.adb.result
			
			commandParams = ["get_free_space_location", device_name]
			self.adb.process_args(commandParams)
			
			commandParams = ["get_device_model", device_name]
			self.adb.process_args(commandParams)
			
			commandParams = ["list_packages", device_name]
			self.adb.process_args(commandParams)
			
			self.selected_application = tk.StringVar()
			choices = self.adb.devices_info[self.adb.current_device_name].device_applications
			
			# Filter only needed applications eaither com.zplay (Taponomicon exception) or com.madheadgames.
			applications = choices
			
			self.selected_application.set(applications[0])
			
			commandParams = ["clear_log", device_name]
			self.adb.process_args(commandParams)

			self.applications = tkinter.ttk.Combobox(self.lfApplicationUtils, state = "readonly", textvariable = self.selected_application, width = 40)
			self.applications.config(values = applications)
			self.applications.bind("<<ComboboxSelected>>", self.on_application_selected)
			self.applications.grid(column = 0, row = 0, columnspan = 2, sticky = "N")
			self.applications.set("")
			
			self.bBackupApp = ttk.Button(self.lfApplicationUtils, text = "Backup Application", command = self.backup_application, width = 20)
			self.bBackupApp.grid(column = 0, row = 2, sticky = 'W', pady = 5)
			
			self.bClearPurchases = ttk.Button(self.lfApplicationUtils, text = "Clear Purchase", command = self.clear_purchase, width = 20)
			self.bClearPurchases.grid(column = 0, row = 3, sticky = 'W', pady = 5)
			
			self.bClearData = ttk.Button(self.lfApplicationUtils, text = "Clear Data & Cache", command = self.clear_data, width = 20)
			self.bClearData.grid(column = 1, row = 2, sticky = 'W', pady = 5)
			
			self.bClearData = ttk.Button(self.lfApplicationUtils, text = "Run Application", command = self.run_application, width = 20)
			self.bClearData.grid(column = 1, row = 3, sticky = 'W', pady = 5)
			
			self.selected_device = device_name
			if not device_name in self.device_tabs:
				self.device_tabs[device_name] = DeviceLogTab(self, device_name)
				device_log = self.device_tabs[device_name]
				device_log.show_console()
			
			
	def clear_purchase(self):
		commandParams = ["clear_purchase", self.adb.current_device_name]
		self.adb.process_args(commandParams)
			
	def backup_application(self):
		response = self.selected_application.get()
		commandParams = ["backup", self.adb.current_device_name, response]
		self.adb.process_args(commandParams)
		
		self.unpack_savegame()
		
	def run_application(self):
		application = self.selected_application.get()
		if self.adb.current_device_name is not None:
			commandParams = ["start_app", self.adb.current_device_name, application]
			self.adb.process_args(commandParams)
		
	def show_console(self):
		self.adb.get_logcat_lines()
		
	def clear_data(self):
		if self.adb.current_device_name is not None:
			commandParams = ["clearData", self.adb.current_device_name, self.selected_application.get()]
			self.adb.process_args(commandParams)
			
	def unpack_savegame(self):
		# For unpacking abe we need to run abe.jar but only if AdoptOpenJDK is installed
		adb_extractor_path = os.getcwd() + "/utils/adb/abe.jar"
		zip_path = os.getcwd() + "/utils/7z/7za.exe" 
		backupab_path = os.getcwd() + "/backup.ab"
		save_games_tar_path = os.getcwd() + "/save_game_files.tar"
		
		command_param = ["java", "-jar", adb_extractor_path, "unpack", backupab_path, save_games_tar_path]
		process = subprocess.Popen(command_param, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		processOutput(process)
		process.communicate()
		process.wait()
		returnCode = process.returncode
		process = None
		if returnCode != 0:
			print("Error converting backup.ab  with code: " + str(returnCode))
		else:
			os.remove(backupab_path)
		
			
	def on_application_selected(self, event = None):
		application_name = str(self.applications.get())
		self.selected_application.set(application_name)
			
	def broadcast_message(self, message):
		commandParams = ["broadcast", self.adb.current_device_name, self.selected_application.get(), message]
		self.adb.process_args(commandParams)
	
	def enableButtons(self):
		for button in self.buttons:
			button.config(state = "normal")

	def disableButtons(self, clickedButton):
		for button in self.buttons:
			if button != clickedButton:
				button.config(state = "disabled")
				
	
	#parent methods
	def show_error(self, msg):
		self.parent.show_error(msg)
	
if __name__ == "__main__" :
	tabSound = TabQA(None);