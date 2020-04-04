'''
'''

import tkinter
try:
	import queue
except:
	import Queue as queue

class ProgressBar(tkinter.Frame):
	def __init__(self, master, width=300, height=20, bg='gray', fillcolor='blue',
			   value=0.0, text=None, font=None, textcolor='black', *args, **kw):
		tkinter.Frame.__init__(self, master, bg=bg, width=width, height=height, *args, **kw)
		self._value = value
		self.queue = queue.Queue()

		self._canv = tkinter.Canvas(self, bg=self['bg'], width=self['width'], height=self['height'],
							  highlightthickness=0, relief='flat', bd=0)
		self._canv.pack(fill='both', expand=1)
		self._rect = self._canv.create_rectangle(0, 0, 0, self._canv.winfo_reqheight(), fill=fillcolor,
										width=0)

		self._text = self._canv.create_text(self._canv.winfo_reqwidth()/2, self._canv.winfo_reqheight()/2,
										 text='', fill=textcolor)
		self.text = ""
		if font:
			self._canv.itemconfigure(self._text, font=font)

		self.width = self._canv.winfo_width()
		self.height = self._canv.winfo_height()
		self.colour = fillcolor
		self.set(value, text)
		self.update_me()

	def _update_coords(self):
		'''Updates the position of the text and rectangle inside the canvas when the size of
		the widget gets changed.'''
		try:
			# looks like we have to call update_idletasks() twice to make sure
			# to get the results we expect
			self._canv.update_idletasks()
			self.width = self._canv.winfo_width() if self._canv.winfo_width() is not None else self.width
			self.height = self._canv.winfo_height() if self._canv.winfo_height() is not None else self.height
			self._canv.coords(self._text, self.width/2, self.height/2)
			self._canv.coords(self._rect, 0, 0, self.width*self._value/100, self.height)
			self._canv.update_idletasks()
		except:
			pass

	def get(self):
		return self._value, self.text

	def update_me(self):
		try:
			while 1:
				value, text = self.queue.get_nowait()
				update = False
				if value != self._value:
					self._value = value
					update = True
					if value <= 0.0:
						value = 0.0
						self.set_colour('blue')
					elif round(value) >= 100:
						value = 100
						self.set_colour('green')
					self.updateTextColor(value)
					if self.width is not None and self.height is not None:
						self._canv.coords(self._rect, 0, 0, self.width*value/100, self.height)

				if text is None:
					text = str(int(round(value))) + ' %'
				if text != self.text:
					self.text = text
					update = True
					if self.width is not None and self.height is not None:
						self._canv.coords(self._text, self.width/2, self.height/2)
						self._canv.itemconfigure(self._text, text=text)

				self.width = self._canv.winfo_width()
				self.height = self._canv.winfo_height()
				if update:
					self._canv.update_idletasks()
		except:
			pass
		self.after(100, self.update_me)

	def set(self, value=0.0, text=None):
		self.lastValue = value
		self.queue.put((value, text))

	def step(self, step):
		self.set(self.lastValue + step)

	def set_colour(self, colour):
		if self.colour != colour:
			try:
				self._canv.itemconfig(self._rect, fill = colour)
				self.colour = colour
			except:
				pass

	def updateTextColor(self, value):
		colour = self.colour
		if (colour == "red" or colour == 'blue') and value >= 50:
			self._canv.itemconfig(self._text, fill = "white")
		else:
			self._canv.itemconfig(self._text, fill = "black")
