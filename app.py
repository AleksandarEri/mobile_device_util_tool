import tkinter
import tkinter.ttk
import tkinter.messagebox

try:
	import winsound
except:
	pass

import os
import os.path
import sys
import inspect
import collections
import platform

from app_ui_qa				import TabQA
from app_ui_ios				import TabIOS
from app_progress_bar		import ProgressBar

# Class Application
class Application(tkinter.Frame):
	def __init__(self):
		self.rootDir = os.getcwd()
		os.chdir(self.rootDir if self.rootDir[-1] != ':' else self.rootDir + '/')

		self.log = None

		self.root = tkinter.Tk()
		self.create_icon()

		tkinter.Frame.__init__(self, self.root)
		self.grid()

		self.size = (840, 540)
		self.system = platform.system()
		self.latestSettingsRead = False

		# 64-base image code
		logoFile = "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"
		self.img = tkinter.PhotoImage(data = logoFile).subsample(2)

		self.cfg = collections.defaultdict(lambda: "")
		self.vStatusMessage = tkinter.StringVar()

		self.lastX = None
		self.lastY = None
		self.createGUI()

		self.root.resizable(False, False)

		self.cleanupLogs()
		self.root.bind("<Configure>", self.onConfigChanged)
		self.position(self.lastX, self.lastY)

		self.root.mainloop()
		self.write_status("Device Manager v0.3")


	def onConfigChanged(self, event):
		try:
			if self.lastX != self.root.winfo_x() or self.lastY != self.root.winfo_y():
				self.lastX = self.root.winfo_x()
				self.lastY = self.root.winfo_y()
		except:
			pass

	def position(self, x = None, y = None):
		w = self.root.winfo_screenwidth()
		h = self.root.winfo_screenheight()
		half_w = int((w - self.size[0])/2)
		half_h = int((h - self.size[1])/2)
		if x is None or y is None or not (0 <= int(x) < (2 * half_w)) or not (0 <= int(y) < (2 * half_h)):
			x = half_w
			y = half_h
			self.lastX = x
			self.lastY = y
		x = int(x)
		y = int(y)
		self.root.geometry('{}x{}+{}+{}'.format(self.size[0], self.size[1], x, y))

	# GUI
	def createGUI(self):
		self.set_configuration()
		self.create_tabs()
		self.create_status_bar()
		self.root.title("Device Manager v0.3")

	def create_icon(self):
		#iconFile = "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"
		#icon = tkinter.PhotoImage(data=iconFile)
		#self.root.tk.call('wm', 'iconphoto', self.root._w, icon)
		pass

	def set_configuration(self):
		self.root.grid_columnconfigure(0, weight = 1)
		self.root.grid_rowconfigure(0, weight = 1)
		self.grid(sticky = "NEWS")
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(0, weight = 1)

	def create_tabs(self):
		self.nTabs = tkinter.ttk.Notebook(self)
		self.nTabs.grid(sticky = 'WENS')
		self.fTabQA = TabQA(self)
		self.fTabIOS = TabIOS(self)

	def create_status_bar(self):
		self.statusBar = tkinter.Label(self, textvariable = self.vStatusMessage)
		self.statusBar.grid(sticky = 'W')
		self.vStatusMessage.set(str("Device Manager v0.3"))

	def create_progress_bar(self):
		self.progress = ProgressBar(self, relief='ridge', bd=3)
		self.progress.grid(sticky = 'EWS')
		self.progress_reset()

	def callOptionCallbacks(self):
		pass 

	def enableButtons(self):
		pass

	def disableButtons(self, clickedButton = None):
		pass

	# Pre Run and On Open Methods
	@staticmethod
	def cleanupLogs():
		if os.path.exists("build/logs"):
			maxLogs = 3
			if len(os.listdir("build/logs")) > maxLogs:
				logs = sorted([log for log in os.listdir("build/logs") if log.endswith(".log")])
				prefixes = ["Atlas", "Exe", "Build", "Data"]
				sufixes = []
				for log in logs:
					prefix = log.split('_')[0]
					if prefix not in prefixes:
						sufixes.append(prefix)

					sufix = '_'.join(log.split('_')[3:])
					if sufix not in sufixes:
						sufixes.append(sufix)

				for prefix in prefixes:
					for sufix in sufixes:
						sublogs = [log for log in logs if log.startswith(prefix) and log.endswith(sufix)]
						for sublog in sublogs:
							logs.remove(sublog)
						for i in range(len(sublogs) - maxLogs):
							os.remove("build/logs/%s" % sublogs[i])

	def progress_step(self, arg):
		self.progress.step(arg)

	def progress_reset(self):
		self.progress.set(0, "")

	def progress_finish(self):
		pass

	def progress_colour(self, colour):
		self.progress.set_colour(colour)
		error_limit = 5
		if colour == "red":
			self.enableButtons()
			if self.progress.lastValue < error_limit:
				self.progress.set(error_limit)
	
	
	def write_status(self, msg):
		self.vStatusMessage.set(str(msg))

	def updateLogs(self):
		self.fLogTab.updateLogs()

	# Error message
	def show_error(self, error_string):
		string = error_string + "\r\n" + "Func: " + inspect.stack()[1][3] + "\r\n" + "Line: " + str(inspect.stack()[1][2]) + "\r\n" + "Desc: " + str(sys.exc_info()[1])
		self.root.after(500, tkinter.messagebox.showerror, "CRITICAL ERROR", string)

app = Application()
