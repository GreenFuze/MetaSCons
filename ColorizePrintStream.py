import sys
import colorama
from colorama import Fore, Back, Style
import re
from typing import TextIO


class ColorizedWrapper(object):
	def __init__(self, stream: TextIO, patterns : list[tuple[str, colorama.ansi.AnsiFore|colorama.ansi.AnsiBack|colorama.ansi.AnsiStyle]]):
		self.patterns = patterns
		self.stream = stream
		
	def install_stdout(self):
		sys.stdout = self

	def uninstall_stdout(self):
		sys.stdout = self.stream

	def install_stderr(self):
		sys.stderr = self

	def uninstall_stderr(self):
		sys.stderr = self.stream

	def write(self, text):		
		# Check each pattern and apply the first matching color
		for pattern, color in self.patterns:
			if re.search(pattern, text):
				colored_text = color + text + Fore.RESET
				self.stream.write(colored_text)
				break
		else:
			# If no pattern matches, write the text as is
			self.stream.write(f'{text}')

	def flush(self):
		self.stream.flush()
		