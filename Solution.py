import os
import platform
import SCons
import colorama
from .Project import Project
from .ColorizePrintStream import ColorizedWrapper
import sys
from enum import Enum
from SCons.Environment import Environment
from SCons.Defaults import DefaultEnvironment

from .Toolset import Toolset

class OperatingSystem(Enum):
	WINDOWS = "Windows"
	LINUX = "Linux"
	MACOS = "MacOS"

class Solution:
	def __init__(self, name: str, path: str, output_path_root: str, environment: Environment = DefaultEnvironment()):
		self.name = name
		self.projects = []
		self.path = os.path.abspath(path)
		self.output_path_root = os.path.abspath(output_path_root)
		self.toolsets = {}

		if environment is None:
			self.environment = Environment()
		else:
			self.environment = environment

		if platform.system() == 'Windows':
			self.set_environment_variable_from_host(['LocalAppData', 'AppData', 'ProgramData', 'ProgramFiles', 'SystemRoot', 'TEMP', 'TMP', 'USERPROFILE', 'windir'])

		self.stdout_color_patterns = []
		self.stderr_color_pattern = []

	@property
	def absolute_path(self)->str:
		return self.path
	
	@property
	def absolute_output_path(self)->str:
		return self.output_path_root
	
	def create_project(self, name: str, path_relative_to_solution: str, output_path_root_relative_to_solution: str, git_url: str|None = None)->Project:
		project = Project(name, self, path_relative_to_solution, output_path_root_relative_to_solution, git_url)
		self.projects.append(project)
		return project

	def add_project(self, project: Project)->None:
		self.projects.append(project)
	
	def print_solution_tree(self)->None:
		indent = 0
		print(f"Solution: {self.name}")
		for project in self.projects:
			project.print_project_tree(indent+1)

	def add_toolset(self, name: str, toolset: Toolset)->None:
		self.toolsets[name] = toolset

	def find_toolset(self, name: str)->Toolset|None:
		if name in self.toolsets:
			return self.toolsets[name]
		else:
			return None

	def set_environment_variable_from_host(self, keys: list[str])->None:
		for key in keys:
			self.environment['ENV'][key] = os.environ[key]

	def set_environment_variable(self, key: str, value: str)->None:
		self.environment['ENV'][key] = value

	def set_stdout_color_patterns(self, patterns_and_colors: list[tuple[str, colorama.ansi.AnsiFore|colorama.ansi.AnsiBack|colorama.ansi.AnsiStyle]])->None:
		self.stdout_color_patterns = patterns_and_colors

	def set_stderr_color_patterns(self, patterns_and_colors: list[tuple[str, colorama.ansi.AnsiFore|colorama.ansi.AnsiBack|colorama.ansi.AnsiStyle]])->None:
		self.stderr_color_patterns = patterns_and_colors

	def install_colorize_stdout(self)->None:
		self.stdout_colorizer = ColorizedWrapper(sys.stdout, self.stdout_color_patterns)
		self.stdout_colorizer.install_stdout()

	def install_colorize_stderr(self)->None:
		self.stderr_colorizer = ColorizedWrapper(sys.stderr, self.stderr_color_patterns)
		self.stderr_colorizer.install_stderr()

	def exit(self, exit_code: int)->None:
		self.environment.Exit(exit_code) # type: ignore - added to environment dynamically

