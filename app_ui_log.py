"""
Copyright 2020 by Aleksandar Eri
"""

import os
import os.path
import time
import sys
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.messagebox
try:
	import queue
except:
	import Queue as queue
	
def save_text_with_append(filename):
	try:
		f = open(filename, "at", encoding="utf-8")
	except:
		f = open(filename, "a")
	return f

def save_text(filename):
	try:
		f = open(filename, "wt", encoding="utf-8")
	except:
		f = open(filename, "w")
	return f

class StdoutRedirector(object):
	def __init__(self, master):
		self.master = master
		self.manager = master.manager

	def write(self, string):
		stringType = 0
		if string.startswith("WARNING"):
			stringType = 1
		self.master.txtOutput.write(string, stringType)
		if self.manager.log is not None:
			with save_text_with_append(self.manager.log) as log:
				log.write(string)

	def flush(self):
		pass

class StderrRedirector(object):
	def __init__(self, master):
		self.master = master
		self.manager = self.master.manager
		rootDir = master.manager.rootDir
		self.errorLog = rootDir + "/logs/error.log"
		if not os.path.exists(rootDir + "/logs"):
			os.makedirs(rootDir + "/logs")


	def write(self, string):
		self.master.txtOutput.write(string, -1)
		with open(self.errorLog, 'at') as log:
			log.write(string)
		if self.manager.log is not None:
			with open(self.manager.log, 'at') as log:
				log.write(string)

	def flush(self):
		pass

class ThreadSafeConsole(tkinter.Text):
	def __init__(self, master, **options):
		tkinter.Text.__init__(self, master, **options)
		self.manager = master.manager
		self.tag_config("err", foreground="red")
		self.tag_config("war", foreground="yellow")
		self.error_indexes = []
		self.warning_indexes = []
		self.queue = queue.Queue()
		self.update_me()

	def write(self, line, error = 0):
		timeStamp = time.strftime("%H:%M:%S", time.localtime())
		if line != "\n" and error == 0:
			printLine = timeStamp + " " + line
		else:
			printLine = line
		self.queue.put((printLine, error))

	def clear(self):
		self.queue.put(None)

	def update_me(self):
		try:
			while 1:
				line = self.queue.get_nowait()
				if line is None:
					self.delete(1.0, tkinter.END)
					self.error_indexes = []
					self.warning_indexes = []
				else:
					error = line[1]
					line = line[0]
					if error != 0:
						startPos = str((float(self.index("end"))  - 1)/ 1)
						endPos = str((float(startPos) + 1) / 1)
						if error == -1:
							self.error_indexes.append((startPos,endPos))
						elif error == 1:
							self.warning_indexes.append((startPos,endPos))

					self.insert(tkinter.END, str(line))
					status = line[line.find(" ") + 1:].strip()
					if len(status) > 5:
						status_max_length = 50
						self.manager.write_status(status
												  if len(status) < status_max_length
												  else "%s...%s" % (status[:status_max_length//2],
																	status[-status_max_length//2:]))
				try:
					self.see(tkinter.END)
					self.update_idletasks()
				except:
					pass
		except:
			pass
		self.highlight_errors()
		if len(self.error_indexes) > 0:
			self.manager.progress_colour("red")
		elif len(self.warning_indexes) > 0:
			self.manager.progress_colour("yellow")
		self.after(100, self.update_me)

	def highlight_errors(self):
		for indexes in self.error_indexes:
			self.tag_add("err", indexes[0], indexes[1])
		for indexes in self.warning_indexes:
			self.tag_add("war", indexes[0], indexes[1])

class TabLog(tkinter.Frame):
	def __init__(self, manager):
		tkinter.Frame.__init__(self, manager.nTabs)
		self.manager = manager
		self.rootDir = manager.rootDir
		self.label = 'Log'
		manager.nTabs.add(self, text = self.label)
		self.grid_columnconfigure(2, weight = 1)
		self.grid_columnconfigure(5, weight = 1)
		self.grid_rowconfigure(0, weight = 1)

		# Logs
		self.lbLogs = tkinter.Listbox(self, selectmode = tkinter.EXTENDED, font = tkinter.font.Font(size = 7),
									  exportselection=0)
		self.lbLogs.grid(column = 0, row = 0, columnspan = 4, sticky = "NWSE", padx = 5, pady = 5)
		self.updateLogs()

		self.sLogs = tkinter.Scrollbar(self, orient = tkinter.VERTICAL)
		self.sLogs.config(command = self.lbLogs.yview)
		self.sLogs.grid(column = 4, row = 0, sticky = 'NWS')
		self.lbLogs.config(yscrollcommand=self.sLogs.set)


		# Console
		self.outputFont = tkinter.font.Font(family="Courier", size=10)

		self.txtOutput = ThreadSafeConsole(self, wrap='word', font = self.outputFont, bg="black", fg="white")
		self.txtOutput.grid(column = 5, row = 0, sticky='NSWE', padx=5, pady=5)
		self.txtOutput.insert(tkinter.END, "Device Manager" + os.linesep + "-----------" + os.linesep + os.linesep)

		sys.stdout = StdoutRedirector(self)
		sys.stderr = StderrRedirector(self)

		# Logo
		tkinter.Label(self, image = self.manager.img).grid(column = 7, row = 0, sticky = 'NE')

		# Console scroll bar
		self.sConsole = tkinter.Scrollbar(self, orient = tkinter.VERTICAL)
		self.sConsole.config(command = self.txtOutput.yview)
		self.sConsole.grid(column = 6, row = 0, sticky = 'NSEW')

		self.txtOutput.config(yscrollcommand=self.sConsole.set)


		self.create_context_menus()

	def create_context_menus(self):
		self.menuConsole = tkinter.Menu(self.txtOutput, tearoff=0)
		self.menuConsole.add_separator()
		self.menuConsole.add_command(label="Clear console",	command=self.mtd_btn_clear_console)
		self.txtOutput.bind("<Button-3>", self.menuConsolePopup)

		self.menuLogs = tkinter.Menu(self.lbLogs, tearoff=0)
		self.menuLogs.add_separator()
		self.menuLogs.add_command(label="Refresh",	command=self.updateLogs)

	# Console Context Menu

	def mtd_btn_copy(self):
		self.manager.root.clipboard_clear()
		self.manager.root.clipboard_append(self.txtOutput.selection_get())

	def mtd_btn_copy_all(self):
		self.manager.root.clipboard_clear()
		self.manager.root.clipboard_append(self.txtOutput.get(1.0, tkinter.END))

	def mtd_btn_clear_console(self):
		self.txtOutput.clear()

	def menuConsolePopup(self, event):
		self.menuConsole.post(event.x_root, event.y_root)

	# Logs Context Menu
	def updateLogs(self, event = None):
		self.lbLogs.delete(0, tkinter.END)
		logsFolder = "logs"
		if os.path.exists(self.rootDir + "/" + logsFolder):
			for log in os.listdir(self.rootDir + "/" + logsFolder):
				if os.path.isfile(self.rootDir + "/" + logsFolder + "/" + log):
					self.lbLogs.insert(tkinter.END, log)
