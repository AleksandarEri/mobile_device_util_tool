import os
import sys
import os.path
import collections
import subprocess
import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter
import tkinter.ttk

try: 
	import queue
except ImportError:
	import Queue as queue

from app_async_logcat import AsyncLogcatReader
from app_async_logcat_writer import AsyncLogcatWriter
from app_async_console import ThreadSafeConsole

class DeviceLogTab(tk.Frame):
	def __init__(self, parent, name):
		if parent is not None:
			tk.Frame.__init__(self, parent.nTabs)
		else:
			tk.Frame.__init__(self, None)
		self.parent = parent
		self.label = name
		
		if parent is not None:
			parent.nTabs.add(self, text = self.label)
			
		self.buttons = []
		self.device_name = name.strip('\t')
		self.bConsoleRunning = False
		
		self.buildUI()
		
	def buildUI(self):
				
		self.optLogToFile = tk.BooleanVar()
		self.optLogToFile.set(False)
		
		
		self.outputFont = tkinter.font.Font(family="Courier", size=10)

		# Search Input
		self.androidFilterVar = tkinter.StringVar()
		self.androidFilterVar.trace("w", lambda name, index, mode: None )
		self.eSearchScenes = tkinter.Entry(self, textvariable = self.androidFilterVar)
		self.eSearchScenes.grid(row = 3, column = 0, columnspan=2, sticky = "ENW")
		
		self.bSearch = tkinter.ttk.Button(self, text = "Search",	command = self.search_in_logs)
		self.bSearch.grid(column = 2, row = 3, sticky = "W")
		self.buttons += [self.bSearch]
		
		self.bClear = tkinter.ttk.Button(self, text = "Clear",	command = self.clear_search)
		self.bClear.grid(column = 2, row = 3, sticky = "E", columnspan=1)
		self.buttons += [self.bClear]
		
		self.bRefresh = tkinter.ttk.Button(self, text = "Refresh",	command = self.refresh_search )
		self.bRefresh.grid(column = 3, row = 3, sticky = "ENW")
		self.buttons += [self.bRefresh]
		
		self.txtOutput = ThreadSafeConsole(self, wrap='word', font = self.outputFont, bg="black", fg="white")
		self.txtOutput.grid(column = 0, row = 4, sticky='NSWE', padx=5, pady=5, columnspan=4)
		self.txtOutput.insert(tkinter.END, "Device Log" + os.linesep + "-----------" + os.linesep + os.linesep)
		self.sConsole = tkinter.Scrollbar(self, orient = tkinter.VERTICAL)
		self.sConsole.config(command = self.txtOutput.yview)
		self.sConsole.grid(column = 5, row = 4, sticky = 'NSEW')

		self.txtOutput.config(yscrollcommand=self.sConsole.set)
		
	def search_in_logs(self, event = None):
		search_term = self.androidFilterVar.get()
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(search_term)
		self.txtOutput.show_results(search_term)
		
	def clear_search(self, event = None):
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(None)
		self.androidFilterVar.set(None)
		self.eSearchScenes.config(textvariable = None)
		
	def refresh_search(self, event = None):
		search_term = self.androidFilterVar.get()
		self.txtOutput.delete(1.0, tkinter.END)
		self.txtOutput.setFilter(search_term)
		self.txtOutput.show_results(search_term)
		
	def setLogToFile(self, state):
		self.optLogToFile.set(state)
		
	def show_console(self):
		if not self.bConsoleRunning:
			command_param = [self.parent.adb.adbPath, "-s", self.device_name, "logcat", "-v", "time"]
			self.logcat = subprocess.Popen(command_param, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
			self.stdout_queue = queue.Queue()
			self.package_name = self.parent.selected_application.get()
			self.stdout_reader = AsyncLogcatReader(self.logcat, self.stdout_queue, self.package_name, self.device_name)
			self.stdout_reader.start()
			self.console_writer = AsyncLogcatWriter(self, self.stdout_reader, self.stdout_queue, 1000, self.device_name)
			self.console_writer.start()
			self.bConsoleRunning = True