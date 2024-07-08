from enum import Enum
import os
import platform
from SCons.Node import NodeList
from SCons.Environment import Environment
from .Toolset import Toolset
from .Toolset import ToolsetAction


class CPPCompiler(Enum):
	GCC = 'g++'
	CL = 'cl'
	CLANG = 'clang++'
	CLCLANG = 'cl-clang'

def get_default_compiler() -> CPPCompiler:
	if platform.system() == 'Windows':
		return CPPCompiler.CL
	else:
		return CPPCompiler.GCC

# * C++ Standard
class CPPStandard(ToolsetAction):
	class Standard(Enum):
		COMPILER_DEFAULT = 'default'
		CPP98 = 'c++98'
		CPP03 = 'c++03'
		CPP11 = 'c++11'
		CPP14 = 'c++14'
		CPP17 = 'c++17'
		CPP20 = 'c++20'

	def __init__(self, compiler: CPPCompiler, standard: 'CPPStandard.Standard') -> None:
		self.compiler = compiler
		self.standard = standard

	def get_command_line(self) -> str:
		if self.standard == self.Standard.COMPILER_DEFAULT:
			return ''
		elif self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return f'-std={self.standard.value}'
		elif self.compiler == CPPCompiler.CL:
			return f'/std:{self.standard.value}'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CXXFLAGS=self.get_command_line())

# * C Standard
class CStandard(ToolsetAction):
	class Standard(Enum):
		COMPILER_DEFAULT = 'default'
		C89 = 'c89'
		C90 = 'c90'
		C99 = 'c99'
		C11 = 'c11'
		C17 = 'c17'
		C18 = 'c18'

	def __init__(self, compiler: CPPCompiler, standard: 'CStandard.Standard') -> None:
		self.compiler = compiler
		self.standard = standard

	def get_command_line(self) -> str:
		if self.standard == self.Standard.COMPILER_DEFAULT:
			return ''
		elif self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return f'-std={self.standard.value}'
		elif self.compiler == CPPCompiler.CL:
			return f'/std:c{self.standard.value[1:]}'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			env.Append(CFLAGS=self.get_command_line())
		elif self.compiler == CPPCompiler.CL:
			env.Append(CFLAGS=self.get_command_line())
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

# * C++ Architecture
class CPPArchitecture(ToolsetAction):
	class Architecture(Enum):
		COMPILER_DEFAULT = 'default'
		x86 = 'x86'
		x64 = 'x64'
		ARM = 'ARM'
		ARM64 = 'ARM64'

	def __init__(self, compiler: CPPCompiler, architecture: 'CPPArchitecture.Architecture') -> None:
		self.compiler = compiler
		self.architecture = architecture

	def get_command_line(self) -> str:
		if self.architecture == self.Architecture.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.architecture == self.Architecture.x86:
				return '-m32'
			elif self.architecture == self.Architecture.x64:
				return '-m64'
			elif self.architecture in [self.Architecture.ARM, self.Architecture.ARM64]:
				return f'-march={self.architecture.value.lower()}'
			else:
				raise Exception(f'Unsupported architecture {self.architecture}')
		elif self.compiler == CPPCompiler.CL:
			if self.architecture == self.Architecture.x86:
				return '/arch:IA32'
			elif self.architecture == self.Architecture.x64:
				return '/arch:x64'
			elif self.architecture == self.Architecture.ARM:
				return '/arch:ARM'
			elif self.architecture == self.Architecture.ARM64:
				return '/arch:ARM64'
			else:
				raise Exception(f'Unsupported architecture {self.architecture}')
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPWarningLevels(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, level: 'CPPWarningLevels.WarningLevels'):
		self.compiler = compiler
		self.level = level

	class WarningLevels(Enum):
		COMPILER_DEFAULT = 'default'
		Off = 'Off'
		W1 = 'W1'
		W2 = 'W2'
		W3 = 'W3'
		W4 = 'W4'
		All = 'All'

	def get_command_line(self) -> str:
		if self.level == self.WarningLevels.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.level == self.WarningLevels.Off:
				return '-w'
			elif self.level == self.WarningLevels.All:
				return '-Wall'
			else:
				return f'-W{self.level.value}'
		elif self.compiler == CPPCompiler.CL:
			if self.level == self.WarningLevels.Off:
				return '/W0'
			elif self.level == self.WarningLevels.All:
				return '/Wall'
			else:
				return f'/W{self.level.value[1:]}'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPWarningAsError(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, enabled: bool):
		self.compiler = compiler
		self.enabled = enabled

	def get_command_line(self):
		if self.enabled:
			if self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
				return '-Werror'
			elif self.compiler == CPPCompiler.CL:
				return '/WX'
		return ''

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPPositionalIndependentCode(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, enabled: bool):
		self.compiler = compiler
		self.enabled = enabled

	def get_command_line(self):
		if self.enabled:
			if self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
				return '-fPIC'
			elif self.compiler == CPPCompiler.CL:
				# Note: Visual Studio does not have a direct equivalent flag for PIC as in GCC/Clang.
				# Position-independent code is generally the default behavior for DLLs.
				return ''
		return ''

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPOptimizationLevel(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, level: 'CPPOptimizationLevel.OptimizationLevel'):
		self.compiler = compiler
		self.level = level

	class OptimizationLevel(Enum):
		COMPILER_DEFAULT = 'default'
		O0 = 'O0'
		O1 = 'O1'
		O2 = 'O2'
		O3 = 'O3'
		Os = 'Os'
		Oz = 'Oz'

	def get_command_line(self) -> str:
		if self.level == self.OptimizationLevel.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			return f'-{self.level.value}'
		elif self.compiler == CPPCompiler.CL:
			if self.level in [self.OptimizationLevel.O2, self.OptimizationLevel.O3]:
				return '/O2'
			elif self.level == self.OptimizationLevel.O1:
				return '/O1'
			elif self.level == self.OptimizationLevel.Os:
				return '/Os'
			elif self.level == self.OptimizationLevel.Oz:
				# Visual Studio does not have a direct equivalent for Oz, using /Os as closest match.
				return '/Os'
			elif self.level == self.OptimizationLevel.O0:
				return '/Od'
			else:
				raise Exception(f'Unknown optimization level {self.level}')
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPDebugInformation(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, level: 'CPPDebugInformation.DebugInformation'):
		self.compiler = compiler
		self.level = level

	class DebugInformation(Enum):
		COMPILER_DEFAULT = 'default'
		Off = 'Off'
		Default = 'Default'
		Full = 'Full'

	def get_command_line(self) -> str:
		if self.level == self.DebugInformation.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.level == self.DebugInformation.Full:
				return '-g'
			elif self.level == self.DebugInformation.Default:
				return '-g'
			elif self.level == self.DebugInformation.Off:
				return ''
			else:
				raise Exception(f'Unknown debug information level {self.level}')
		elif self.compiler == CPPCompiler.CL:
			if self.level == self.DebugInformation.Full:
				return '/Zi'
			elif self.level == self.DebugInformation.Default:
				return '/Zi'
			elif self.level == self.DebugInformation.Off:
				return '/Z7'
			else:
				raise Exception(f'Unknown debug information level {self.level}')
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

class CPPRuntimeLinking(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, linking: 'CPPRuntimeLinking.RuntimeLinking'):
		self.compiler = compiler
		self.linking = linking

	class RuntimeLinking(Enum):
		COMPILER_DEFAULT = 'default'
		Static = 'Static'
		Dynamic = 'Dynamic'

	def get_command_line(self):
		if self.linking == self.RuntimeLinking.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.linking == self.RuntimeLinking.Static:
				return '-static'
			elif self.linking == self.RuntimeLinking.Dynamic:
				return '-shared'
		elif self.compiler == CPPCompiler.CL:
			if self.linking == self.RuntimeLinking.Static:
				return '/MT'
			elif self.linking == self.RuntimeLinking.Dynamic:
				return '/MD'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LINKFLAGS=self.get_command_line())

class CPPOutputType(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, output_type: 'CPPOutputType.OutputType'):
		self.compiler = compiler
		self.output_type = output_type

	class OutputType(Enum):
		COMPIER_DEFAULT = 'default'
		Executable = 'Executable'
		StaticLibrary = 'StaticLibrary'
		DynamicLibrary = 'DynamicLibrary'

	def get_command_line(self):
		if self.output_type == self.OutputType.COMPIER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.output_type == self.OutputType.Executable:
				return ''
			elif self.output_type == self.OutputType.StaticLibrary:
				return '-static'
			elif self.output_type == self.OutputType.DynamicLibrary:
				return '-shared'
		elif self.compiler == CPPCompiler.CL:
			if self.output_type == self.OutputType.Executable:
				return '/link'
			elif self.output_type == self.OutputType.StaticLibrary:
				return '/LD'
			elif self.output_type == self.OutputType.DynamicLibrary:
				return '/DLL'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LINKFLAGS=self.get_command_line())

class CPPBuildType(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, build_type: 'CPPBuildType.BuildType'):
		self.compiler = compiler
		self.build_type = build_type

	class BuildType(Enum):
		COMPILER_DEFAULT = 'default'
		Debug = 'Debug'
		Release = 'Release'
		RelWithDebInfo = 'RelWithDebInfo'

	def get_command_line(self):
		if self.build_type == self.BuildType.COMPILER_DEFAULT:
			return ''
		elif self.compiler in [CPPCompiler.GCC, CPPCompiler.CLANG, CPPCompiler.CLCLANG]:
			if self.build_type == self.BuildType.Debug:
				return '-g'
			elif self.build_type == self.BuildType.Release:
				return '-O3'
			elif self.build_type == self.BuildType.RelWithDebInfo:
				return '-O2 -g'
		elif self.compiler == CPPCompiler.CL:
			if self.build_type == self.BuildType.Debug:
				return '/Zi /Od'
			elif self.build_type == self.BuildType.Release:
				return '/O2 /DNDEBUG'
			elif self.build_type == self.BuildType.RelWithDebInfo:
				return '/Zi /O2 /DNDEBUG'
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CFLAGS=self.get_command_line())

# * CPP Includes paths
class CPPIncludesPath(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, paths: str | list[str] | None) -> None:
		self.compiler = compiler
		if paths is None:
			self.paths = []
		elif isinstance(paths, str):
			self.paths = [paths]
		elif isinstance(paths, list):
			self.paths = paths
		else:
			raise ValueError("Invalid paths argument")

	def add_include_path(self, paths: 'str | list[str] | CPPIncludesPath | NodeList'):
		if isinstance(paths, str):
			self.paths.append(paths)
		elif isinstance(paths, list):
			self.paths.extend(paths)
		elif isinstance(paths, CPPIncludesPath):
			self.paths.extend(paths.paths)
		else:
			raise ValueError("Invalid paths argument")

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return ' '.join(['-I' + path for path in self.paths])
		elif self.compiler == CPPCompiler.CL:
			return ' '.join(['/I' + path for path in self.paths])
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CPPPATH=self.paths)
		

# * CPP Sources
class CPPSources(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, sources: 'str|list[str]|CPPSources|NodeList') -> None:
		self.compiler = compiler
		if sources is None:
			self.sources = []
		elif isinstance(sources, str):
			self.sources = [sources]
		elif isinstance(sources, list):
			self.sources = sources
		elif isinstance(sources, NodeList):
			self.sources = sources
		else:
			raise ValueError("Invalid sources argument")

	def add_source(self, sources: 'str|list[str]|CPPSources|NodeList'):
		if isinstance(sources, str):
			self.sources.append(sources)
		elif isinstance(sources, list):
			self.sources.extend(sources)
		elif isinstance(sources, CPPSources):
			self.sources.extend(sources.sources)
		elif isinstance(sources, NodeList):
			self.sources = sources
		else:
			raise ValueError("Invalid sources argument")

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return ' '.join(self.sources)
		elif self.compiler == CPPCompiler.CL:
			return ' '.join(self.sources)
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CPPSOURCES=self.sources)
		

# * CPP Link Libraries Paths
class CPPLinkLibrariesPaths(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, paths: str | list[str] | None) -> None:
		self.compiler = compiler
		if paths is None:
			self.paths = []
		elif isinstance(paths, str):
			self.paths = [paths]
		elif isinstance(paths, list):
			self.paths = paths
		else:
			raise ValueError("Invalid paths argument")

	def add_library_path(self, paths: 'str | list[str] | CPPLinkLibrariesPaths | NodeList'):
		if isinstance(paths, str):
			self.paths.append(paths)
		elif isinstance(paths, list):
			self.paths.extend(paths)
		elif isinstance(paths, CPPLinkLibrariesPaths):
			self.paths.extend(paths.paths)
		else:
			raise ValueError("Invalid paths argument")

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return ' '.join(['-L' + path for path in self.paths])
		elif self.compiler == CPPCompiler.CL:
			return ' '.join(['/LIBPATH:' + path for path in self.paths])
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LIBPATH=self.paths)


# * CPP Link Libraries
class CPPLinkLibraries(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, libraries: str | list[str] | None) -> None:
		self.compiler = compiler
		if libraries is None:
			self.libraries = []
		elif isinstance(libraries, str):
			self.libraries = [libraries]
		elif isinstance(libraries, list):
			self.libraries = libraries
		else:
			raise ValueError("Invalid libraries argument")

	def add_library(self, libraries: 'str | list[str] | CPPLinkLibraries | NodeList'):
		if isinstance(libraries, str):
			self.libraries.append(libraries)
		elif isinstance(libraries, list):
			self.libraries.extend(libraries)
		elif isinstance(libraries, CPPLinkLibraries):
			self.libraries.extend(libraries.libraries)
		else:
			raise ValueError("Invalid libraries argument")

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			library_flags = []
			for lib in self.libraries:
				if os.path.isabs(lib):
					library_flags.append('-L' + os.path.dirname(lib))
					library_flags.append('-l' + os.path.basename(lib))
				else:
					library_flags.append('-l' + lib)
			return ' '.join(library_flags)
		elif self.compiler == CPPCompiler.CL:
			return ' '.join(self.libraries)
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			for lib in self.libraries:
				if os.path.isabs(lib):
					env.Append(LIBPATH=os.path.dirname(lib))
					env.Append(LIBS=[os.path.basename(lib)])
				else:
					env.Append(LIBS=[lib])
		elif self.compiler == CPPCompiler.CL:
			env.Append(LIBS=self.libraries)
		else:
			raise Exception(f'Unknown compiler {self.compiler}')



# * Set output bin directory
class CPPOutputBinDirectory(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, output_directory: str) -> None:
		self.compiler = compiler
		self.output_directory = output_directory

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return '-o ' + self.output_directory
		elif self.compiler == CPPCompiler.CL:
			return '/OUT:' + self.output_directory
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LINKFLAGS=self.output_directory)


# * Set output obj directory
class CPPOutputObjDirectory(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, output_directory: str) -> None:
		self.compiler = compiler
		self.output_directory = output_directory

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return '-o ' + self.output_directory
		elif self.compiler == CPPCompiler.CL:
			return '/Fo' + self.output_directory
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(CXXFLAGS=self.output_directory)

# * Set output lib directory
class CPPOutputLibDirectory(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, output_directory: str) -> None:
		self.compiler = compiler
		self.output_directory = output_directory

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return '-o ' + self.output_directory
		elif self.compiler == CPPCompiler.CL:
			return '/OUT:' + self.output_directory
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LINKFLAGS=self.output_directory)

# * Set output pdb directory
class CPPOutputPDBDirectory(ToolsetAction):
	def __init__(self, compiler: CPPCompiler, output_directory: str) -> None:
		self.compiler = compiler
		self.output_directory = output_directory

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return '-o ' + self.output_directory
		elif self.compiler == CPPCompiler.CL:
			return '/PDB:' + self.output_directory
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		env.Append(LINKFLAGS=self.output_directory)


# * CPP Preprocessor Definitions
class CPPPreprocessorDefinitions:
	def __init__(self, compiler: CPPCompiler, definitions: str | list[str] | None) -> None:
		self.compiler = compiler
		if definitions is None:
			self.definitions = []
		elif isinstance(definitions, str):
			self.definitions = [definitions]
		elif isinstance(definitions, list):
			self.definitions = definitions
		else:
			raise ValueError("Invalid definitions argument")

	def add_definition(self, definitions: 'str | list[str] | CPPPreprocessorDefinitions'):
		if isinstance(definitions, str):
			self.definitions.append(definitions)
		elif isinstance(definitions, list):
			self.definitions.extend(definitions)
		elif isinstance(definitions, CPPPreprocessorDefinitions):
			self.definitions.extend(definitions.definitions)
		else:
			raise ValueError("Invalid definitions argument")

	def __str__(self):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			return ' '.join(['-D' + definition for definition in self.definitions])
		elif self.compiler == CPPCompiler.CL:
			return ' '.join(['/D' + definition for definition in self.definitions])
		else:
			raise Exception(f'Unknown compiler {self.compiler}')

	def add_to_environment(self, env: Environment):
		if self.compiler == CPPCompiler.GCC or self.compiler == CPPCompiler.CLANG or self.compiler == CPPCompiler.CLCLANG:
			env.Append(CPPDEFINES=self.definitions)
		elif self.compiler == CPPCompiler.CL:
			env.Append(CPPDEFINES=self.definitions)
		else:
			raise Exception(f'Unknown compiler {self.compiler}')
		

class CPPToolset(Toolset):
	def __init__(self, compiler: CPPCompiler):
		self.compiler = compiler
		self.includes_path = CPPIncludesPath(compiler, None)
		self.sources = CPPSources(compiler, [])
		self.link_libraries_paths = CPPLinkLibrariesPaths(compiler, None)
		self.link_libraries = CPPLinkLibraries(compiler, None)
		self.output_bin_directory = CPPOutputBinDirectory(compiler, '')
		self.output_obj_directory = CPPOutputObjDirectory(compiler, '')
		self.output_lib_directory = CPPOutputLibDirectory(compiler, '')
		self.output_pdb_directory = CPPOutputPDBDirectory(compiler, '')
		self.preprocessor_definitions = CPPPreprocessorDefinitions(compiler, None)
		self.cpp_standard = CPPStandard(compiler, CPPStandard.Standard.COMPILER_DEFAULT)
		self.c_standard = CStandard(compiler, CStandard.Standard.COMPILER_DEFAULT)
		self.architecture = CPPArchitecture(compiler, CPPArchitecture.Architecture.COMPILER_DEFAULT)
		self.warning_levels = CPPWarningLevels(compiler, CPPWarningLevels.WarningLevels.COMPILER_DEFAULT)
		self.warning_as_error = CPPWarningAsError(compiler, False)
		self.positional_independent_code = CPPPositionalIndependentCode(compiler, False)
		self.optimization_level = CPPOptimizationLevel(compiler, CPPOptimizationLevel.OptimizationLevel.COMPILER_DEFAULT)
		self.debug_information = CPPDebugInformation(compiler, CPPDebugInformation.DebugInformation.COMPILER_DEFAULT)
		self.runtime_linking = CPPRuntimeLinking(compiler, CPPRuntimeLinking.RuntimeLinking.COMPILER_DEFAULT)
		self.output_type = CPPOutputType(compiler, CPPOutputType.OutputType.COMPIER_DEFAULT)
		self.build_type = CPPBuildType(compiler, CPPBuildType.BuildType.COMPILER_DEFAULT)

		# prepare for iteration
		self._iterable_attributes = [
			self.includes_path,
			self.sources,
			self.link_libraries_paths,
			self.link_libraries,
			self.output_bin_directory,
			self.output_obj_directory,
			self.output_lib_directory,
			self.output_pdb_directory,
			self.preprocessor_definitions,
			self.cpp_standard,
			self.c_standard,
			self.architecture,
			self.warning_levels,
			self.warning_as_error,
			self.positional_independent_code,
			self.optimization_level,
			self.debug_information,
			self.runtime_linking,
			self.output_type,
			self.build_type
		]
		self._current_index = 0

	def __iter__(self):
		self._current_index = 0
		return self
	
	def __next__(self):
		if self._current_index < len(self._iterable_attributes):
			self._current_index += 1
			return self._iterable_attributes[self._current_index - 1]
		else:
			raise StopIteration	

	def add_include_path(self, paths: 'str | list[str] | CPPIncludesPath | NodeList'):
		self.includes_path.add_include_path(paths)

	def add_source(self, sources):
		self.sources.add_source(sources)

	def add_library_path(self, paths: 'str | list[str] | CPPLinkLibrariesPaths | NodeList'):
		self.link_libraries_paths.add_library_path(paths)

	def add_library(self, libraries: 'str | list[str] | CPPLinkLibraries | NodeList'):
		self.link_libraries.add_library(libraries)

	def set_output_bin_directory(self, output_directory: str):
		self.output_bin_directory.output_directory = output_directory

	def set_output_obj_directory(self, output_directory: str):
		self.output_obj_directory.output_directory = output_directory

	def set_output_lib_directory(self, output_directory: str):
		self.output_lib_directory.output_directory = output_directory

	def set_output_pdb_directory(self, output_directory: str):
		self.output_pdb_directory.output_directory = output_directory

	def add_preprocessor_definition(self, definitions: 'str | list[str] | CPPPreprocessorDefinitions'):
		self.preprocessor_definitions.add_definition(definitions)

	def set_cpp_standard(self, standard: CPPStandard.Standard):
		self.cpp_standard = CPPStandard(self.compiler, standard)

	def set_c_standard(self, standard: CStandard.Standard):
		self.c_standard = CStandard(self.compiler, standard)

	def set_architecture(self, architecture: CPPArchitecture.Architecture):
		self.architecture = CPPArchitecture(self.compiler, architecture)

	def set_warninglevels(self, level: CPPWarningLevels.WarningLevels):
		self.warning_levels = CPPWarningLevels(self.compiler, level)

	def set_warningaserror(self, as_error: bool):
		self.warning_as_error = CPPWarningAsError(self.compiler, as_error)

	def set_positional_independent_code(self, pic: bool):
		self.positional_independent_code = CPPPositionalIndependentCode(self.compiler, pic)

	def set_optimization_level(self, level: CPPOptimizationLevel.OptimizationLevel):
		self.optimization_level = CPPOptimizationLevel(self.compiler, level)

	def set_debug_information(self, debug_info: CPPDebugInformation.DebugInformation):
		self.debug_information = CPPDebugInformation(self.compiler, debug_info)

	def set_runtime_linking(self, linking: CPPRuntimeLinking.RuntimeLinking):
		self.runtime_linking = CPPRuntimeLinking(self.compiler, linking)

	def set_outputtype(self, output_type: CPPOutputType.OutputType):
		self.output_type = CPPOutputType(self.compiler, output_type)

	def set_build_type(self, build_type: CPPBuildType.BuildType):
		self.build_type = CPPBuildType(self.compiler, build_type)
		