import fnmatch
from json import tool
import re
import subprocess
from sys import platform
import sys
from SCons.Environment import Environment
from SCons.Node import NodeList
from enum import Enum
from typing import List, Union, cast

from .CustomBuilder import CustomBuildAction
from .Action import Action
from .CPPEnvironment import CPPEnvironment
from .CPPToolset import CPPCompiler, CPPToolset
from .Project import Project
from abc import ABC, abstractmethod
import os
import glob
import os



# =================================================================================================
# * Abstract class for C++ actions
# =================================================================================================

class CPPAction(Action):
	def __init__(self, project: Project, toolset: CPPToolset, add_action_to_project: bool = True):
		super().__init__(project, add_action_to_project)
		self.cpp_env = CPPEnvironment(self.env, toolset)
	
	@property
	def toolset(self) -> CPPToolset:
		return cast(CPPToolset, self.cpp_env._toolset)
	
	@abstractmethod
	def submit_action(self):
		self.cpp_env.add_to_environment()

	def add_sources(self, sources: list[str]):
		self.toolset.add_source(sources)

	def add_sources_in_directory(self, root_dir: str,
									recursive: bool = False,
									include_patterns: list[str] = ['*.cpp', '*.c', '*.cc', '*.cxx'],
									exclude_patterns: list[str] = ['*_test.cpp', '*_test.c', '*_test.cc', '*_test.cxx']):
		# Generate file patterns to search for
		file_patterns = include_patterns
		exclude_patterns = exclude_patterns

		# If recursive flag is set, search for files in subdirectories as well
		if recursive:
			file_patterns = [os.path.join(root, pattern) for pattern in include_patterns for root, _, _ in os.walk(root_dir)]

		# Get a list of source files matching the file patterns
		sources = [source for pattern in file_patterns for source in glob.glob(os.path.join(root_dir, pattern), recursive=recursive)]

		# Exclude files matching the exclude patterns
		sources = [source for source in sources if not any(fnmatch.fnmatch(source, pattern) for pattern in exclude_patterns)]

		# Add the sources to the toolset
		self.toolset.add_source(sources)

	def include_directories(self, include_paths: list[str]):
		include_paths = [os.path.join(self.project.absolute_path, path) for path in include_paths]
		self.toolset.add_include_path(include_paths)


# =================================================================================================
# * C++ Object Files
# =================================================================================================

class CPPObjFiles(CPPAction):
	def __init__(self, toolset: CPPToolset|str, project: Project, output_path_relative_to_parent: str, sources: list[str]|NodeList=[], include_paths: list[str]|NodeList=[], libraries: list[str]|NodeList=[], library_paths: list[str]|NodeList=[], add_action_to_project: bool = True):
		if isinstance(toolset, str):
			found_toolset = project.find_toolset(toolset)
			if found_toolset is None:
				raise Exception(f'Toolset with name {toolset} not found in the the project {project.name} or its parents. Exiting...')
			if not isinstance(found_toolset, CPPToolset):
				raise Exception('toolset must be an instance of CPPToolset')
			else:
				toolset = found_toolset

		if not isinstance(toolset, CPPToolset):
			raise Exception('toolset must be an instance of CPPToolset')

		super().__init__(project, toolset, add_action_to_project)
		
		self.output_path_relative_to_parent = output_path_relative_to_parent
		self.toolset.add_source(sources)
		self.toolset.add_include_path(include_paths)
		self.toolset.add_library_path(library_paths)
		self.toolset.add_library(libraries)

	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.project.absolute_output_path, self.output_path_relative_to_parent)
		
	def submit_action(self):
		super().submit_action() # adds toolset to environment
		
		action: NodeList = self.env.Object(self.toolset.sources.sources) # type: ignore
		self._set_submitted_action(action)

# =================================================================================================
# * C++ DEF File (Windows only)
# =================================================================================================

def def_from_windows_objs(target, source, env):
	# make sure that dumpbin is found
	if not env.WhereIs('dumpbin'):
		print('dumpbin.exe is not found. Exiting...', file=sys.stderr)
		env.Exit(1)
	
	# use dumpbin to extract symbols from object files
	object_files = [str(s.abspath) for s in source]
	symbols = []
	for object_file in object_files:
		try:
			process = subprocess.run([env.WhereIs('dumpbin'), '/SYMBOLS', object_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			if process.returncode != 0:
				print(f'Failed to extract symbols from {object_file}. Exiting...', file=sys.stderr)
				env.Exit(1)
			# parse output and append to symbols list - make sure to append only the symbol name
			output = process.stdout.decode()
			# Adjust the regex pattern based on the actual format of the dumpbin output
			pattern = r'[0-9A-Fa-f]{3} [0-9A-Fa-f]{8} (.{5}) .*(External|Public).*\| ([^\s]+)'
			matches = re.finditer(pattern, output, re.MULTILINE)
			for match in matches:
				if 'UNDEF' not in match.group(0):
					symbol = match.group(3).strip()
					symbols.append(symbol)
		except Exception as e:
			print(f'Failed to extract symbols from {object_file}.\nError {e}.\nExiting...', file=sys.stderr)
			env.Exit(1)

	# make sure all symbols are unique by converting to set and back to list
	symbols = list(set(symbols))
	new_content = 'EXPORTS\n' + '\n'.join(['\t' + symbol for symbol in symbols])

	def_file_path = target
	try:
		# Read the existing DEF file content
		with open(def_file_path, 'r', encoding='utf-8') as f:
			existing_content = f.read()
	except FileNotFoundError:
		existing_content = ""

	# Write to the DEF file only if the content has changed
	if new_content != existing_content:
		with open(def_file_path, 'w', encoding='utf-8') as f:
			f.write(new_content)


class CPPDefFile(CPPAction):
	def __init__(self, toolset: CPPToolset|str, project: Project, target: str, output_path_relative_to_parent: str, sources: list[str]|NodeList =[], include_paths: list[str]=[], libraries: list[str]=[], library_paths: list[str]=[], add_action_to_project: bool = True):
		if isinstance(toolset, str):
			found_toolset = project.find_toolset(toolset)
			if found_toolset is None:
				raise Exception(f'Toolset with name {toolset} not found in the the project {project.name} or its parents. Exiting...')
			if not isinstance(found_toolset, CPPToolset):
				raise Exception('toolset must be an instance of CPPToolset')
			else:
				toolset = found_toolset

		if not isinstance(toolset, CPPToolset):
			raise Exception('toolset must be an instance of CPPToolset')

		super().__init__(project, toolset, add_action_to_project)
		
		self.target = target
		self.output_path_relative_to_parent = output_path_relative_to_parent
		if isinstance(sources, NodeList) or isinstance(sources, list):
			self.toolset.add_source(sources)
			
		self.toolset.add_include_path(include_paths)
		self.toolset.add_library_path(library_paths)
		self.toolset.add_library(libraries)

	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.project.absolute_output_path, self.output_path_relative_to_parent)
		
	def submit_action(self):
		super().submit_action() # adds toolset to environment

		# add custom build action to create DEF file from object files
		
		action = CustomBuildAction(self.project, def_from_windows_objs, self.target, self.toolset.sources.sources)
		action.submit_action()

		if action.submitted_action is None:
			raise Exception('Failed creating DEF file custom builder. Exiting...')

		self._set_submitted_action(action.submitted_action)


# =================================================================================================
# * C++ Program
# =================================================================================================

class CPPProgram(CPPAction):
	def __init__(self, toolset: CPPToolset|str, project: Project, target_file_name: str, output_path_relative_to_parent: str, sources: list[str]|NodeList=[], include_paths: list[str]|NodeList=[], libraries: list[str]|NodeList=[], library_paths: list[str]|NodeList=[], add_action_to_project: bool = True):
		if isinstance(toolset, str):
			found_toolset = project.find_toolset(toolset)
			if found_toolset is None:
				raise Exception(f'Toolset with name {toolset} not found in the the project {project.name} or its parents. Exiting...')
			if not isinstance(found_toolset, CPPToolset):
				raise Exception('toolset must be an instance of CPPToolset')
			else:
				toolset = found_toolset

		if not isinstance(toolset, CPPToolset):
			raise Exception('toolset must be an instance of CPPToolset')

		super().__init__(project, toolset, add_action_to_project)
		
		self.target = target_file_name
		self.output_path_relative_to_parent = output_path_relative_to_parent
		self.toolset.add_source(sources)
		self.toolset.add_include_path(include_paths)
		self.toolset.add_library_path(library_paths)
		self.toolset.add_library(libraries)

	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.project.absolute_output_path, self.output_path_relative_to_parent)

	def submit_action(self):
		super().submit_action() # adds toolset to environment

		self.cpp_env.add_to_environment()
		action = self.env.Program(target=self.target) # type: ignore
		self._set_submitted_action(action)


# =================================================================================================
# * C++ Shared Library
# =================================================================================================

class CPPSharedLibrary(CPPAction):
	def __init__(self, toolset: CPPToolset|str,
			  project: Project,
			  target_file_name: str,
			  source_code_path_relative_to_parent: str,
			  output_path_relative_to_parent: str,
			  is_add_all_sources: bool = True,
			  is_include_header_directory: bool = True,
			  add_action_to_project: bool = True):
		
		if isinstance(toolset, str):
			found_toolset = project.find_toolset(toolset)
			if found_toolset is None:
				raise Exception(f'Toolset with name {toolset} not found in the the project {project.name} or its parents. Exiting...')
			if not isinstance(found_toolset, CPPToolset):
				raise Exception('toolset must be an instance of CPPToolset')
			else:
				toolset = found_toolset

		if not isinstance(toolset, CPPToolset):
			raise Exception('toolset must be an instance of CPPToolset')

		super().__init__(project, toolset, add_action_to_project)
		
		self.target = target_file_name
		self.output_path_relative_to_parent = output_path_relative_to_parent
		self.source_code_path_relative_to_parent = source_code_path_relative_to_parent
		self.is_export_all_symbols = False

		if is_add_all_sources:
			self.add_all_sources()

		if is_include_header_directory:
			self.include_source_directory()

	@property
	def absolute_source_code_path(self) -> str:
		return os.path.join(self.project.absolute_path, self.source_code_path_relative_to_parent)

	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.project.absolute_output_path, self.output_path_relative_to_parent)

	# in windows, it mimics CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS
	def set_export_all_symbols(self):
		self.toolset.add_preprocessor_definition('EXPORT_ALL_SYMBOLS')
		self.is_export_all_symbols = True

	def add_all_sources(self, recursive: bool = True,
										include_patterns: list[str] = ['*.cpp', '*.c', '*.cc', '*.cxx'],
										exclude_patterns: list[str] = ['*_test.cpp', '*_test.c', '*_test.cc', '*_test.cxx']):
		self.add_sources_in_directory(self.absolute_source_code_path, recursive, include_patterns, exclude_patterns)

	def include_source_directory(self):
		self.toolset.add_include_path([self.absolute_source_code_path])

	def submit_action(self):
		super().submit_action() # adds toolset to environment

		# if windows and self.is_export_all_symbos:
		# 	compile source to object files
		# 	create DEF file from objects
		# 	link object files and DEF file to create DLL
		if self.is_export_all_symbols and self.toolset.compiler == CPPCompiler.CL:
			objects = CPPObjFiles(self.toolset, self.project, self.output_path_relative_to_parent, self.toolset.sources.sources, add_action_to_project=False)
			objects.submit_action()
			objects.depends_on(self.toolset.sources.sources)

			if objects.submitted_action is None:
				raise Exception('Object files are not submitted. Exiting...')

			def_file = CPPDefFile(self.toolset, self.project, self.target+'.def', self.output_path_relative_to_parent, sources=objects.submitted_action, add_action_to_project=False)
			def_file.submit_action()
			def_file.depends_on(objects)

			action: NodeList = self.env.SharedLibrary(target=self.target) # type: ignore
			self._set_submitted_action(action)			
		else:
			self.cpp_env.add_to_environment()
			action: NodeList = self.env.SharedLibrary(target=self.target) # type: ignore
			self._set_submitted_action(action)

# =================================================================================================
# * C++ Static Library
# =================================================================================================

class CPPStaticLibrary(CPPAction):
	def __init__(self, toolset: CPPToolset|str, project: Project, target_file_name: str, output_path_relative_to_parent: str, sources: list[str]=[], include_paths: list[str]=[], libraries: list[str]=[], library_paths: list[str]=[], add_action_to_project: bool = True):
		if isinstance(toolset, str):
			found_toolset = project.find_toolset(toolset)
			if found_toolset is None:
				raise Exception(f'Toolset with name {toolset} not found in the the project {project.name} or its parents. Exiting...')
			if not isinstance(found_toolset, CPPToolset):
				raise Exception('toolset must be an instance of CPPToolset')
			else:
				toolset = found_toolset

		if not isinstance(toolset, CPPToolset):
			raise Exception('toolset must be an instance of CPPToolset')

		super().__init__(project, toolset, add_action_to_project)
		
		self.target = target_file_name
		self.output_path_relative_to_parent = output_path_relative_to_parent
		self.toolset.add_source(sources)
		self.toolset.add_include_path(include_paths)
		self.toolset.add_library_path(library_paths)
		self.toolset.add_library(libraries)

	@property
	def absolute_output_path(self) -> str:
		return os.path.join(self.project.absolute_output_path, self.output_path_relative_to_parent)
		
	def submit_action(self):
		super().submit_action() # adds toolset to environment
		
		action = self.env.StaticLibrary(target=self.target) # type: ignore
		self._set_submitted_action(action)

