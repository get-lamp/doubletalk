#!/usr/bin/python

import StringIO, re

class Syntax(object):
	DELIMITERS 			= "[.:!,;+*^&'\"\-\\/\|=@#$%()?<>\s]"
	
class Scanner(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.src	= open(source) if is_file else StringIO.StringIO(source)
		self.syntax	= syntax
		self.token	= []
		
	def scan(self):
	
		if self.src.closed:
			return None

		while True:
			char = self.src.read(1)
			if not char:
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
			
			if token == '"':
				return ''.join(self.verbatim('"'))
		

#lex = Lexer(Syntax(), 'sample.dtk').parse()			
#print lex

grammar = {
	"[/]": {
		"[*]": {
			".": None
		}
	}
}

print grammar['[/]']





