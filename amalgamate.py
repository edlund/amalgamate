#!/usr/bin/env python

# amalgamate.py - Amalgamate C source and header files.
# Copyright (c) 2012, Erik Edlund <erik.o.edlund@gmail.com>
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#  * Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
# 
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
# 
#  * Neither the name of Erik Edlund, nor the names of its contributors may
#  be used to endorse or promote products derived from this software without
#  specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import json
import os
import re
import sys

class Amalgamation(object):
	
	# Determine if the given file_path can be found on either
	# self.source_path or one of the include paths.
	def file_path(self, file_path, include_paths=None):
		if include_paths == None:
			include_paths = self.include_paths
		
		paths = [os.path.join(self.source_path, path)
			for path in include_paths]
		paths.insert(0, self.source_path)
		for path in paths:
			tmp_path = os.path.join(path, file_path)
			if os.path.exists(tmp_path):
				return tmp_path
		return None
	
	def __init__(self, args):
		with open(args.config, 'r') as f:
			config = json.loads(f.read())
			for key in config:
				setattr(self, key, config[key])
			
			self.verbose = args.verbose == "yes"
			self.prologue = args.prologue
			self.source_path = args.source_path
			self.included_files = []
	
	# Generate the amalgamation and write it to the target file.
	def generate(self):
		amalgamation = ""
		
		if self.prologue:
			with open(self.prologue, 'r') as f:
				amalgamation += f.read()
		
		if self.verbose:
			print("Config:")
			print(" target        = {0}".format(self.target))
			print(" working_dir   = {0}".format(os.getcwd()))
			print(" include_paths = {0}".format(self.include_paths))
		print("Creating amalgamation:")
		for file_path in self.sources:
			# Do not check the include paths while processing the source
			# list, all given source paths must be correct.
			actual_path = self.file_path(file_path, [])
			if not actual_path:
				raise IOError("File not found: \"{0}\"".format(file_path))
			print(" - processing \"{0}\"".format(actual_path))
			t = TranslationUnit(actual_path, self)
			amalgamation += t.content
		
		with open(self.target, 'w') as f:
			f.write(amalgamation)
		
		print("...done!\n")
		if self.verbose:
			print("Files processed: {0}".format(self.sources))
			print("Files included: {0}".format(self.included_files))
		print("")

class TranslationUnit(object):
	
	# // C++ comment.
	cpp_comment_pattern = re.compile(r"//.*?\n")
	
	# /* C comment. */
	c_comment_pattern = re.compile(r"/\*.*?\*/", re.S)
	
	# "complex \"stri\\\ng\" value".
	string_pattern = re.compile("[^']" r'".*?(?<=[^\\])"', re.S)
	
	# Handle simple include directives. Support for advanced
	# directives where macros and defines needs to expanded is
	# not a concern right now.
	include_pattern = re.compile(
		r'#\s*include\s+(<|")(?P<path>.*?)("|>)', re.S)
	
	# Search for pattern in self.content, add the match to
	# contexts if found and update the index accordingly.
	def _search_content(self, index, pattern, contexts):
		match = pattern.search(self.content, index)
		if match:
			contexts.append(match)
			return match.end()
		return index + 2
	
	# Include all trivial #include directives into self.content.
	def _include_files(self):
		content_len = len(self.content)
		if content_len < len("#include <x>"):
			return 0
		
		# Find contexts in the content in which a found include
		# directive should not be processed.
		skippable_contexts = []
		
		# Walk through the content char by char, and try to grab
		# skippable contexts using regular expressions when found.
		i = 1
		while i < content_len:
			j = i - 1
			current = self.content[i]
			previous = self.content[j]
			
			if current == '"':
				# String value.
				i = self._search_content(j, self.string_pattern,
					skippable_contexts)
			elif current == '*' and previous == '/':
				# C style comment.
				i = self._search_content(j, self.c_comment_pattern,
					skippable_contexts)
			elif current == '/' and previous == '/':
				# C++ style comment.
				i = self._search_content(j, self.cpp_comment_pattern,
					skippable_contexts)
			else:
				# Skip to the next char.
				i += 1
		
		# Search for include directives in the content, collect those
		# which should be included into the content.
		includes = []
		include_match = self.include_pattern.search(self.content)
		while include_match:
			should_include = True
			for context in skippable_contexts:
				if include_match.start() > context.start() and \
						include_match.end() < context.end():
					should_include = False
					break
			include_path = include_match.group("path")
			actual_path = self.amalgamation.file_path(include_path)
			if should_include and actual_path:
				includes.append((include_match, actual_path))
			
			include_match = self.include_pattern.search(self.content,
				include_match.end())
		
		# Handle all collected include directives.
		prev_end = 0
		tmp_content = ''
		for include in includes:
			include_match, actual_path = include
			tmp_content += self.content[prev_end:include_match.start()]
			tmp_content += "// {0}\n".format(include_match.group(0))
			if not actual_path in self.amalgamation.included_files:
				t = TranslationUnit(actual_path, self.amalgamation)
				tmp_content += t.content
			prev_end = include_match.end()
		tmp_content += self.content[prev_end:]
		self.content = tmp_content
		
		return len(includes)
	
	def __init__(self, file_path, amalgamation):
		self.file_path = file_path
		self.amalgamation = amalgamation
		
		self.amalgamation.included_files.append(self.file_path)
		
		with open(self.file_path, 'r') as f:
			self.content = f.read()
			self._include_files()

def main():
	description = "Amalgamate C source and header files."
	usage = " ".join([
		"amalgamate.py",
		"[-v]",
		"-c path/to/config.json",
		"-s path/to/source/dir",
		"[-p path/to/prologue.(c|h)]"
	])
	argsparser = argparse.ArgumentParser(
		description=description, usage=usage)
	
	argsparser.add_argument("-v", "--verbose", dest="verbose",
		choices=["yes", "no"], metavar="", help="be verbose")
	
	argsparser.add_argument("-c", "--config", dest="config",
		required=True, metavar="", help="path to a JSON config file")
	
	argsparser.add_argument("-s", "--source", dest="source_path",
		required=True, metavar="", help="source code path")
	
	argsparser.add_argument("-p", "--prologue", dest="prologue",
		required=False, metavar="", help="path to a C prologue file")
	
	amalgamation = Amalgamation(argsparser.parse_args())
	amalgamation.generate()

if __name__ == "__main__":
	main()

