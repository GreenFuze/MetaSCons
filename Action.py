from typing import Any, List
from typing import TYPE_CHECKING
import SCons
from SCons.Node import NodeList
from SCons.Environment import Environment
from abc import ABC, abstractmethod
from .Toolset import Toolset

if TYPE_CHECKING:
	from .Project import Project

class Action(ABC):
	def __init__(self, project: 'Project', add_action_to_project: bool = True) -> None:
		from .Project import Project
		super().__init__()
		self._project = project

		# clone project's environment for this specific action
		self._env = project.environment.Clone()

		if add_action_to_project:
			project.add_action(self)

		self._submitted_action = None

	@property
	def project(self) -> 'Project':
		from .Project import Project
		return self._project
		
	@property
	def env(self) -> Environment:
		return self._env
	
	@property
	def submitted_action(self) -> NodeList|None:
		return self._submitted_action
	
	def depends_on(self, other: 'Action|List[str]|NodeList'):
		if self._submitted_action is None:
			raise RuntimeError('The action is yet to be submitted, Cannot set dependency on an action that has not been submitted yet')
		
		if isinstance(other, Action) and other._submitted_action is None:
			raise RuntimeError('The other action is yet to be submitted, Cannot set dependency on an action that has not been submitted yet')

		if isinstance(other, list):
			self.env.Depends(self._submitted_action, other)
		elif isinstance(other, Action):
			self.env.Depends(self._submitted_action, other.submitted_action)
		elif isinstance(other, str):
			self.env.Depends(self._submitted_action, other)
		elif isinstance(other, NodeList):
			self.env.Depends(self._submitted_action, other)
		else:
			raise ValueError(f'Invalid type for other during "depends_on": {other}')

	def _set_submitted_action(self, action: NodeList):
		self._submitted_action = action

	@abstractmethod
	def submit_action(self) -> NodeList|None:
		pass

