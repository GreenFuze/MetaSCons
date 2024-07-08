from typing import Any, Callable
import SCons
from SCons.Environment import Environment
from .Action import Action
from .Project import Project

class CustomBuildAction(Action):
	
	def __init__(self, project: Project, func: Callable[..., Any], target: Any = None, source: Any = None):
		super().__init__(project)
		
		self.func_name = func.__name__

		self.env.Append(BUILDERS = {
			self.func_name: self.env.Builder(action = func)
		})

		self._target = None
		self._source = None

	@property
	def target(self):
		return self._target
	
	@target.setter
	def target(self, value):
		self._target = value

	@property
	def source(self):
		return self._source
	
	@source.setter
	def source(self, value):
		self._source = value

	def submit_action(self):
		action = getattr(self.env, self.func_name)(self._target, self._source)
		self._set_submitted_action(action)
		


