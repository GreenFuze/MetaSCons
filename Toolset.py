from SCons.Environment import Environment
from abc import ABC, abstractmethod

class ToolsetAction(ABC):
	@abstractmethod
	def add_to_environment(self, env: Environment):
		pass

class Toolset:
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def __iter__(self):
		pass

	@abstractmethod
	def __next__(self) -> ToolsetAction|StopIteration:
		pass

class ToolsetEnvironment:
	def __init__(self, env: Environment, toolset: Toolset):
		self._env = env
		self._toolset = toolset

	def add_to_environment(self):
		for action in self._toolset: # type: ignore
			if action is not None:
				action.add_to_environment(self._env)

	@property
	def toolset(self) -> Toolset:
		return self._toolset
		
	@property
	def env(self) -> Environment:
		return self._env