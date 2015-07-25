#!/usr/bin/python

import StringIO, re

class Doubletalk(object):
	DELIMITERS = "[.:!,;+*^&'\"\-\\/\|=@#$%()?<>\s]"
	
	tree = {
		'[\s]': 	'space',
		'[\n]':		'newline',
		'[\t]':		'tab',
		'[/]': {
			'[*]': 	'comment_block_open',
			'[/]': 	'comment_line',
			None:	'divide'
		},
		'[*]': {
			'[/]':	'comment_block_close',
			None:	'multiply'
		},
		'[=]': {
			'[=]': {
				'[=]': 	'equal_strict',
				None:	'equal'
			}
		},
		'[0-9]': 					'number',
		'[_a-zA-Z][_a-zA-Z0-9]*':	'identifier'
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
		
	def next(self):
	
		tree = self.syntax.tree
		word = []
		
		while True:
			symbol = self.scanner.scan()
			
			"""
			# ignore spaces
			if symbol == ' ' or symbol == '\n' or symbol == '\t':
				continue
			"""
			# EOF				
			if symbol is None:
				return False
							
			# search in syntax tree
			for regexp in tree:
				match = None
				#print 'Trying %s with %s' % (regexp, symbol)
				if regexp is None:
					tree = self.syntax.tree
					continue
				elif re.match(regexp, symbol, re.M):
					word.append(symbol)
					match = symbol
					break
			
			if match is not None:
				# there is a possible continuation to this symbol
				if isinstance(tree.get(regexp, None), dict):
					# move forward in tree
					tree = tree[regexp]
					continue
				else:
					print tree[regexp]
			
			# move to tree root
			tree = self.syntax.tree
				
			if len(word) == 0:
				continue
				
			# now word is recognized
			return ''.join(word)	
			
	
	def parse(self):
		while True:
			n = self.next()
			if n is False:
				break
			print n
			
						
		

lex = Lexer(Doubletalk(), 'test.dtk')

lex.parse()

#print lex

