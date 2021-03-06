import sqlite3
import re

from sqlite3 import Error

class LogDBManager(object):
	def __init__(self, device_name):
		self.con = None
		self.cursor = None
		self.con = self.create_db(device_name)
		self.cursor = self.create_table(self.con)
		self.last_fetched_row = 0 
		
	def create_db(self, device_name):
		try:
			db_name = str(device_name) + ".db"
			con = sqlite3.connect(db_name, check_same_thread=False)
			return con
		except Error:
			print(Error)
			pass
			
	def create_table(self, con):
		try:
			cursorObj = self.con.cursor()
			cursorObj.execute("CREATE TABLE logs(Id INTEGER PRIMARY KEY AUTOINCREMENT, loginfo text)")
			con.commit()
			self.cursor = self.con.cursor()
		except:
			self.cursor = self.con.cursor()
			pass
	
	def insert_log_to_db(self, log):
		if self.cursor is None:
			self.cursor = self.con.cursor()
		try:
			self.cursor.execute("INSERT INTO logs(loginfo) VALUES(?)", [log])
			self.con.commit()
		except Exception as ec:
			print("Error inserting: " + repr(ec))
			pass
		self.cursor = self.con.cursor()
		
	def get_records(self, filter_text):
		all_data = None
		if filter_text is not None:
			sql_command = ""
			if self.last_fetched_row == 0:
				sql_command = "SELECT * FROM logs WHERE	 logs.loginfo LIKE '%" + filter_text + "%';"
			else:
				sql_command = "SELECT * FROM logs WHERE logs.loginfo LIKE '%" + filter_text + "%' AND logs.ID > " + str(self.last_fetched_row) + ";"
			all_data = self.cursor.execute(sql_command).fetchall()
		else:
			if self.last_fetched_row == 0:
				all_data = self.cursor.execute("SELECT * from logs").fetchall()
			else:
				all_data = self.cursor.execute("SELECT * from logs WHERE logs.ID > " + str(self.last_fetched_row) + ";").fetchall()
		returned_data = []
		for row in all_data:
			returned_data.append(row[1])
		self.last_fetched_row += len(all_data) 
		return returned_data