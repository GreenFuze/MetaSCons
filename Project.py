import SCons
import os
from typing import TYPE_CHECKING
import SCons.Environment
from git import Repo

from .Action import Action
from .Toolset import Toolset

if TYPE_CHECKING:
	from .Solution import Solution

class Project:
	def __init__(self, name: str, parent: 'Solution|Project', path_relative_to_parent: str, output_path_root_relative_to_parent: str, git_url: str|None = None):
		from .Solution import Solution
		self.name = name
		self.path_relative_to_parent = path_relative_to_parent
		self.output_path_root_relative_to_parent = output_path_root_relative_to_parent

		self.git_url = git_url

		self.parent = parent
		self.elements = []
		self.environment: SCons.Environment.Environment = parent.environment.Clone()

		self.toolsets = {}

	@property
	def absolute_path(self) -> str:
		return os.path.join(self.parent.absolute_path, self.path_relative_to_parent)
	
	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.parent.absolute_output_path, self.output_path_root_relative_to_parent)

	# ensure_project_exists at the given path
	# and if not, it clones the project including its submodules
	def verify_project_exist(self) -> bool:
		if not os.path.exists(self.absolute_path):
			try:
				if self.git_url is None:
					raise ValueError(f'Project "{self.name}" does not exist and no git url is provided to clone it.')

				print(f'{self.absolute_path} does not exist. Cloning from {self.git_url} branch "main"... ', end='')
				repo = Repo.clone_from(self.git_url, self.absolute_path, branch='main', recursive=True)
				print(f'Done')
				return True
			except Exception as e:
				print(f'Failed with Error: {e}')
				return False
		else:
			return True
		
	# Adds a project to the list of projects
	def add_sub_project(self, name: str, path_relative_to_solution: str, output_path_root_relative_to_parent: str, git_url: str|None = None)->'Project':
		p = Project(name, self, path_relative_to_solution, output_path_root_relative_to_parent, git_url)
		self.elements.append(p)
		return p
	
	# check if toolset exists in the project or its parents
	def find_toolset(self, name: str)->Toolset|None:
		if name in self.toolsets:
			return self.toolsets[name]
		
		return self.parent.find_toolset(name)
	
	# Add Action to the project
	def add_action(self, action: Action)->None:
		self.elements.append(action)

	def submit_action(self):
		for element in self.elements:
			if isinstance(element, Action):
				element.submit_action()
			elif isinstance(element, Project):
				element.submit_action()
			else:
				raise ValueError(f'Invalid element type: {element}')
	
	
	
	
	
	



