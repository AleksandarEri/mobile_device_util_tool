from __future__ import absolute_import
try: 
	import queue
except ImportError:
	import Queue as queue
import threading
import time

class AsyncLogFileReader(threading.Thread):
	"""
	Helper class to implement asynchronous reading of a file
	in a separate thread. Pushes read lines on a queue to
	be consumed in another thread.
	"""

	def __init__(self, logFile, console):
		threading.Thread.__init__(self)
		self.daemon = True
		self._stop = threading.Event()
		self.last_position = 0
		self.log_file = logFile
		self.console_output = console

	def run(self):
		"""
		The body of the thread: read lines and put them in the queue.
		"""
		while not self.stopped():
			if self.log_file is not None:
				try:
					with open(self.log_file, 'r') as f:
						f.seek(self.last_position)
						new_data = f.read()
						new_position = f.tell()
						if self.last_position != new_position:
							self.last_position = new_position
							self.process(new_data.splitlines())
				except:
					pass
			time.sleep(5) #sleep some amount of time

	def process(self, lines):
		for line in lines:
			self.console_output.updateConsole(line)

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()
