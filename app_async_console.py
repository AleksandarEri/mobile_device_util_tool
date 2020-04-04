import time
import sys
import os
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.messagebox
try:
	import queue
except:
	import Queue as queue
	
from app_log_manager import LogDBManager

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
		self.manager = master

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
		self.manager = self.master
		rootDir = master.rootDir
		self.errorLog = rootDir + "/build/logs/error.log"
		if not os.path.exists(rootDir + "/build"):
			os.makedirs(rootDir + "/build")
		if not os.path.exists(rootDir + "/build/logs"):
			os.makedirs(rootDir + "/build/logs")

	def write(self, string):
		if isinstance(self.master.txtOutput, ThreadSafeConsole):
			self.master.txtOutput.write(string, -1)
		else:
			self.txtOutput.insert("", "end", string, text=string)
		with open(self.errorLog, 'at') as log:
			log.write(string)
		if self.manager.log is not None:
			with open(self.manager.log, 'at') as log:
				log.write(string)

	def flush(self):
		pass

def Diff(li1, li2): 
	return (list(set(li1) - set(li2))) 

class ThreadSafeConsole(tkinter.Text):
	def __init__(self, master, **options):
		tkinter.Text.__init__(self, master, **options)
		self.manager = master
		self.tag_config("err", foreground="red")
		self.tag_config("war", foreground="yellow")
		self.error_indexes = []
		self.warning_indexes = []
		self.queue = queue.Queue()
		self.filter_text = None
		self.db_manager = None
		self.log = None
		#self.update_me()
		

	def createLog(self, device_name):
		if not os.path.exists("logs"):
			os.makedirs("logs")

		rootDir = os.getcwd()
		logName = "%s_%s" % (device_name, time.strftime("%Y-%m-%d", time.localtime()))
		
		logName = "%s/logs/%s.log" % (rootDir, logName)
		with save_text(logName) as f:
			f.close()
			
		self.log = logName

	def setFilter(self, filter_text):
		self.filter_text = filter_text
	
	def write(self, line, device_name):
		timeStamp = time.strftime("%H:%M:%S", time.localtime())
		if line != "\n":
			printLine = timeStamp + " " + line.decode('utf-8')
		else:
			printLine = line
		if self.db_manager is None:
			self.db_manager = LogDBManager(device_name)
		self.db_manager.insert_log_to_db(line.decode('utf-8'))
		self.update_console()
		if self.manager.optLogToFile.get():
			if self.log is None:
				self.createLog(device_name)
			if self.log is not None:
				with save_text_with_append(self.log) as log:
					try:
						log.write(line.decode("utf-8"))
					except:
						pass 

	def clear(self):
		self.queue.put(None)

	def update_me(self):
		try:
			while 1:
				self.update_console()
		except:
			pass
		self.highlight_errors()
		if len(self.error_indexes) > 0:
			self.manager.progress_colour("red")
		elif len(self.warning_indexes) > 0:
			self.manager.progress_colour("yellow")
		self.after(100, self.update_me)
		
		
	def show_results(self, term):
		lines = self.db_manager.get_records(term)
		for line in lines:
			self.insert(tkinter.END, line)
		
	def update_console(self):
		if self.db_manager is not None:
			if self.filter_text is None:
				lines = self.db_manager.get_records(self.filter_text)
				for line in lines:
					self.insert(tkinter.END, line)
			#self.see(tkinter.END)

	def highlight_errors(self):
		for indexes in self.error_indexes:
			self.tag_add("err", indexes[0], indexes[1])
		for indexes in self.warning_indexes:
			self.tag_add("war", indexes[0], indexes[1])