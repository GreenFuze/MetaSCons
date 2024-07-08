
from SCons.Environment import Environment
from .CPPToolset import CPPToolset
from .Toolset import ToolsetEnvironment
from typing import cast

class CPPEnvironment(ToolsetEnvironment):
	def __init__(self, env: Environment, toolset: CPPToolset):
		super().__init__(env, toolset)
		
	@property
	def toolset(self) -> CPPToolset:
		# cast super().toolset to CPPToolset
		return cast(CPPToolset, super().toolset)
