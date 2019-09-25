import re

class INI:
	empty_regex = re.compile("EMPTY\d*")

	def __init__(self, filename):
		self.filename = filename
		self.file = None

	def load(self):
		"""Load config file."""
		f = open(self.filename)
		if f:
			self.file = f.readlines()
		else:
			print("File", self.filename, "not found.")

	def write(self, name):
		"""Write a copy of the config file, with any changes applied."""
		if name:
			f = open(name, "x")
			f.writelines(self.file)
			return f

	def find_section_range(self, name):
		"""Determine where a section begins and ends."""
		if self.file:
			start = -1
			for i in range(len(self.file)):
				l = self.file[i]
				if len(l) and l[0] == '[' and start == -1:
					n = l[1: -2]
					if n == name:
						start = i
				elif not start == -1 and l[0] == '[':
					return start, i
			print("Section", name, "not found.")
			return -1, -1

	def get_interval(self, start, end):
		"""Retrieve an interval of lines from the file."""
		return self.file[start: end]

	def remove_section(self, name, list=None, danger_level=0):
		""" Remove a section by name. Danger level indicates how aggressively to remove it.

		:param name: Name of section.
		:param list: Should the section be removed from a list? If yes, name it here.
		:param danger_level: Level of aggression during removal.
			2 is complete deletion, 1 comments section and in list, while 0 comments and places a dummy value in the list.
		"""
		if self.file and name:
			start, end = self.find_section_range(name)
			if not start == -1:
				if danger_level > 1:	# Needs its own variable.
					self.delete_segment(start, end)
				else:
					self.comment_segment(start, end)
				if list:
					self.remove_from_list(name, list, danger_level)

	def remove_from_list(self, value, list, danger_level=0):
		""" Remove a section from a list.
		:param list: Name of list.
		:param danger_level: Level of aggression during removal.
			2 is complete deletion, 1 comments out, while 0 places a dummy value in the list.
		"""
		start, end = self.find_section_range(list)
		if not start == -1:
			i = self.get_list_file_pos(start, end, value)
			if not i == -1:
				if danger_level < 1:
					empty = self.count_empty(start, end)
					n = self.file[i].split("=")[0]
					self.file[i] = n + "=" + "EMPTY" + empty
				elif danger_level < 2:
					self.file[i] = "; " + self.file[i]
				else:
					del self.file[i]

	def get_list_file_pos(self, start, end, value):
		"""Find the exact position of this value in this list, described as an interval in the file."""
		for i in range(start, end):
			l = self.file[i]
			if len(l) and l[0].isdigit():
				if re.match(value, l.split("=")[1]):
					return i
		print(value, "not found in range", start, ",", end)
		return -1

	def count_empty(self, start, end):
		"""Count amount of values in the interval that begin with 'EMPTY'."""
		e = 0
		for i in range(start, end):
			l = self.file[i]
			if len(l) and l[0].isdigit():
				if INI.empty_regex.match(l.split("=")[1]):
					e += 1
		return e

	def replace_segment(self, start, end, new_section):
		"""Replace one section with another."""
		l = len(new_section)
		if (end - start) == l:
			for i, j in zip(range(start, end), range(l)):
				self.file[i] = new_section[j]
		else:
			# Put it in between all that is before and after the old section.
			self.file = self.file[:start].extend(new_section).extend(self.file[end:])

	def remove_all_comments(self):
		"""Go through the file, and delete any comments in the file."""
		if self.file:
			for i in range(len(self.file) - 1, -1, -1):
				line = self.file[i]
				if len(line):
					if line[0] == ";":
						del self.file[i]
					else:
						split = re.split(";", line, 1)
						if len(split) > 1:
							self.file[i] = split[0].rstrip() + "\n"

	def delete_segment(self, start, end):
		"""Completely remove a segment of the file. Typically a section."""
		for i in range(end - 1, start - 1, -1):
			del self.file[i]

	def comment_segment(self, start, end):
		"""Comment out a segment of the file. Typically a section."""
		for i in range(start, end):
			self.file[i] = "; " + self.file[i]

	def reindex_list(self, list):
		"""Go through the list and set the indices to start at 0 and increment. This shouldn't affect any logic or maps.
		:param list: Name of list to reorder.
		"""
		if self.file:
			start, end = self.find_section_range(list)
			if not start == -1:
				section = self.get_interval(start, end)
				j = 0
				new_section = [section[0]]
				for i in range(1, len(section)):
					line = section[i]
					if len(line) and line[0].isdigit():
						split = line.split("=")
						if len(split) > 1:	# There is an error case in the YR rules: 842-GAWETH_ED
							line = str(j) + "=" + split[1]
							j += 1
					new_section.append(line)
				self.replace_segment(start, end, new_section)
