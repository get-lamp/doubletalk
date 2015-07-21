#!/usr/bin/python

import StringIO, re

class Doubletalk(object):
	DELIMITERS 			= "[.:!,;+*^&'\"\-\\/\|=@#$%()?<>\s]"
	tree = {
		'[/]': {
			'[*]': 'comment_block_open',
			'[/]': 'comment_line',
		},
		'[*]': {
			'[/]': 'comment_block_close'
		},
		'[=]': {
			'[=]': {
				'[=]': 'equal_strict'
			}
		}
	}
	
class Scanner(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.src	= open(source) if is_file else StringIO.StringIO(source)
		self.syntax	= syntax
		self.token	= []
		
	def scan(self):
	
		if self.src.closed:
			# already at EOF
			return None

		while True:
			char = self.src.read(1)
			if not char:
				# EOF
				self.src.close()
				break
			
			c = re.match(self.syntax.DELIMITERS, char)
			
			if c is None:
				self.token.append(char)
			else:
				if len(self.token) == 0:
					return char
				else:
					self.src.seek(-1, 1)
					tkn = ''.join(self.token)
					self.token = []
					return tkn
		
		return self.token if len(self.token) > 0 else None
		
class Lexer(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.syntax 	= syntax
		self.scanner 	= Scanner(syntax, source, is_file)
		
	def verbatim(self, stop):
		verbatim = []
		while True:
			symbol = self.scanner.scan()
			if symbol == stop or symbol is None:
				break
			else:
				verbatim.append(symbol)
			
		return verbatim
		
	def parse(self):
		while True:
			token = self.scanner.scan()
						
			for regexp in self.syntax.tree:
				if re.match(regexp, token):
					print token
			
			if token == '"':
				return ''.join(self.verbatim('"'))
		

lex = Lexer(Doubletalk(), 'sample.dtk').parse()			
#print lex

"""
def scan(self):
	
		if self.src.closed:
			# already at EOF
			return None
			
		branch = self.syntax.tree
		self.token = []

		while True:
			char = self.src.read(1)
			
			if not char:
				# EOF reached
				self.src.close()
				break
				
			for regexp in branch:
				c = re.match(regexp, char)
				if c is not None:
					self.token.append(char)
				
					if isinstance(branch[regexp], dict):
						branch = branch[regexp]
					elif branch[regexp] == 0:
						return ''.join(self.token) if len(self.token) > 0 else None
					else:
						p = len(branch) - branch[regexp]
						while len(branch) > p:
  							branch.pop()
  				else:
  					break
  						
  							
		return ''.join(self.token) if len(self.token) > 0 else None	
					

"""









