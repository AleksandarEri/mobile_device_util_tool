from __future__ import absolute_import
try: 
	import queue
except ImportError:
	import Queue as queue
import threading

class AsyncLogcatReader(threading.Thread):
	"""
	Helper class to implement asynchronous reading of a file
	in a separate thread. Pushes read lines on a queue to
	be consumed in another thread.
	"""

	def __init__(self, process, queue, package_name, device_name):
		threading.Thread.__init__(self)
		self.daemon = True
		self._process = process
		self._fd = process.stdout
		self._queue = queue
		# self._pid = runtime.get_pid()
		self._stop = threading.Event()
		self.package_name = package_name
		self.device_name = device_name

	def run(self):
		"""
		The body of the thread: read lines and put them in the queue.
		"""
		while not self.stopped():
			line = self._fd.readline()
			try:
				line_str = line.decode('utf-8')
				if self.package_name is None:
					self._queue.put(line)
				else:
					if self.package_name in line_str:
						self._queue.put(line)
			except:
				pass
		self._fd.close()

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