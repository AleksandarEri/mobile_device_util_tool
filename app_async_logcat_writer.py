from __future__ import absolute_import
try: 
	import queue
except ImportError:
	import Queue as queue
import threading

from app_async_console import ThreadSafeConsole

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

class AsyncLogcatWriter(threading.Thread):
	"""
	Helper class to implement asynchronous writing to a console
	in a separate thread.
	"""

	def __init__(self, master, reader, log_queue, timeout, device_name):
		threading.Thread.__init__(self)
		self.daemon = True
		self.reader = reader
		self.log_queue = log_queue
		self.timeout = timeout
		self.master = master
		self.device_name = device_name
		self._stop = threading.Event()

	def write(self, string):
		stringType = 0
		if isinstance(self.master.txtOutput, ThreadSafeConsole):
			self.master.txtOutput.write(string, self.device_name)
		else:
			self.master.txtOutput.insert("", "end", text=string)
	
	def run(self):
		"""
		The body of the thread: read lines and put them in the queue.
		"""
		while not self.reader.eof():
			
			try:
				line = self.log_queue.get(timeout=self.timeout)
			except queue.Empty:
				print('%s\'s logcat output is silent for %d seconds. Considering that as steady state. Taking a snapshot with Collector now\n', "GameName", self.timeout)
				break
			if line is None:
				break
			else:
				self.write(line)

	def eof(self):
		"""
		Check whether there is no more content to expect.
		"""
		return not self.is_alive() and self._queue.empty()

	def stop(self):
		self._stop.set()
		self._queue.put('\0')

	def stopped(self):
		return self._stop.isSet()