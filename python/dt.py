#!/usr/bin/python

import StringIO, re

class Doubletalk(object):
	DELIMITERS = "[.:!,;+*^&'\"\-\\/\|=$()?<>\s]"
	
	symbols = {
		r'[\s]': 	'[space]',
		r'^\n$':	'[newline]',
		r'[\t]':	'[tab]',
		r'[/]': {
			r'[*]': '[comment_block_open]',
			r'[/]': '[comment_line]',
			None:	'[divide]'
		},
		r'[*]': {
			r'[/]':	'[comment_block_close]',
			None:	'[multiply]'
		},
		r'[=]': {
			r'[=]': {
				r'[=]': '[equal_strict]',
				None:	'[equal]'
			},
			None: '[assign]'
		},
		r'[0-9]': 						'[number]',
		r'[_a-zA-Z][_a-zA-Z0-9]*':		'[identifier]',
		r'[@][_a-zA-Z][_a-zA-Z0-9]*':	'[character]',
		r'[#][_a-zA-Z][_a-zA-Z0-9]*':	'[place]',
		r'[%][_a-zA-Z][_a-zA-Z0-9]*':	'[mobile]',
		r'[&][_a-zA-Z][_a-zA-Z0-9]*':	'[item]'
	}

	grammar = {

	}
	
class Lexer(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.src	= open(source) if is_file else StringIO.StringIO(source)
		self.syntax	= syntax
		self.token	= []

	def __exit__(self):
		self.src.close()
		
	def scan(self):
	
		if self.src.closed:
			# already at EOF
			return None

		while True:
			# read character
			char = self.src.read(1)
			if not char:
				# EOF
				self.src.close()
				break
			
			c = re.match(self.syntax.DELIMITERS, char)
			
			# no delimiter found
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
		
		return ''.join(self.token) if len(self.token) > 0 else None

	def next(self):
	
		tree = self.syntax.symbols
		word = []
		
		while True:
			# get next symbol
			symbol = self.scan()

			# EOF				
			if symbol is None:
				return False
							
			# search in syntax tree
			for regexp in tree:
				match = None
				if regexp is None:
					continue

				if re.match(regexp, symbol, re.M):
					word.append(symbol)
					# move forward in tree
					tree = tree[regexp]
					match = symbol
					break
	
			if match is not None:
				# there is a possible continuation to this symbol
				if isinstance(tree, dict):
					continue
			else:
				tree = tree.get(None)
			
			if len(word) == 0:
				# move to tree root
				tree = self.syntax.symbols
				continue

			return (''.join(word), tree)
		
class Parser(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.syntax = syntax
		self.lexer 	= Lexer(syntax, source, is_file)
		
	def verbatim(self, stop):
		verbatim = []
		while True:
			symbol = self.lexer.scan()
			if symbol == stop or symbol is None:
				break
			else:
				verbatim.append(symbol)
			
		return verbatim
		
	def parse(self):
		while True:
			n = self.lexer.next()
			if n is False:
				break
			print n


			
						
		

lex = Parser(Doubletalk(), 'test.dtk')
lex.parse()