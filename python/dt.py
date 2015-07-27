#!/usr/bin/python

import StringIO, re

class Doubletalk(object):

	class Lexeme(object):
		def __init__(self, word, **kwargs):
			self.word = word

	class PreprocessorDirective(Lexeme):
		pass
		
	class CommentBlock(PreprocessorDirective):
		pass
	
	class CommentLine(PreprocessorDirective):
		pass
	
	class Identifier(Lexeme):
		pass
		
	class String(Lexeme):
		pass
	
	class Number(Lexeme):
		pass
	
	class Operator(Lexeme):
		pass
	
	class Keyword(Lexeme):
		pass
	
	delimiters = "[.:!,;+*^&@#$%&'\"\-\\/\|=$()?<>\s]"
	
	r_space 		= r'[ ]'
	r_newline		= r'[\n]'
	r_tab 			= r'[\t]'
	r_slash 		= r'[/]'
	r_asterisk 		= r'[*]'
	r_equal 		= r'[=]'
	r_plus 			= r'[+]'
	r_dash 			= r'[-]'
	r_number 		= r'^[0-9]+'
	r_identifier 	= r'[_a-zA-Z][_a-zA-Z0-9]*'
	r_atsign		= r'[@]'
	r_double_quote 	= r'["]'
	r_single_quote 	= r'[\']'
	
	symbols = {
		r_space: 		'[space]',
		r_newline:		'[newline]',
		r_tab:			'[tab]',
		r_double_quote: '[string]',
		r_single_quote: '[string]',
		r_slash: {
			r_asterisk:	lambda s: Doubletalk.CommentBlock(s, open=True),
			r_slash: 	'[comment_line]',
			None:		'[divide]'
		},
		r_asterisk: {
			r_slash:	lambda s: Doubletalk.CommentBlock(s, open=False),
			None:		'[multiply]'
		},
		r_equal: {
			r_equal: {
				r_equal:	'[equal_strict]',
				None:		'[equal]'
			},
			None: 			'[assign]'
		},
		r_plus: {
			r_plus:	'[increment]',
			None:	'[add]'
		},
		r_dash: {
			r_dash:		'[decrement]',
			None:		'[subtract]'
		},
		r_number: 			'[number]',
		r_identifier:		lambda i: Doubletalk.Identifier(i),
		r_atsign: {
			r_identifier:	'[character]',
			None: '[ego]'
		}
	}

	
class Lexer(object):
	
	def __init__(self, syntax, source, is_file=True):
		self.src	= open(source) if is_file else StringIO.StringIO(source)
		self.syntax	= syntax
		self.token	= []
		self.nline	= 0
		self.nchar 	= 0

	def __exit__(self):
		self.src.close()
		
	def scan(self):
	
		if self.src.closed:
			# already at EOF
			return None
		
		self.token = []

		while True:
			# read character
			char = self.src.read(1)
			
			if not char:
				# EOF
				self.src.close()
				break
			
			c = re.match(self.syntax.delimiters, char)
			
			# no delimiter found. Keep reading
			if c is None:
				self.token.append(char)
			else:
				# a delimiter found. A single char to return
				if len(self.token) == 0:
					self.token = char
					break
				# a multichar token to return. 
				# backtrack 1 to leave pointer in position for next reading
				else:
					self.src.seek(-1, 1)
					break
		
		# char is newline
		# TODO: fix newlines getting tangled with numbers
		if re.match(self.syntax.r_newline, char):
			self.nchar = 0
			self.nline = self.nline + 1
		else:
			self.nchar 	= self.nchar + 1
			
		token 		= ''.join(self.token)
		info 		= '%s:%s' % (self.nline,self.nchar)
				
		return (info,token) if len(token) > 0 else (info,None)

	def next(self):
	
		tree = self.syntax.symbols
		word = []
		
		while True:
			# get next symbol
			info,symbol = self.scan()

			# EOF				
			if symbol is None:
				return False
							
			# search in syntax tree
			for regexp in tree:
				match = None
				if regexp is None:
					continue

				if re.match(regexp, symbol):
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

			return (info,''.join(word), tree)
		
class Parser(object):
	
	def __init__(self, lang, source, is_file=True):
		self.lang	= lang
		self.lexer 	= Lexer(lang, source, is_file)
		self.tree 	= []
		
	def verbatim(self, stop):
		verbatim = []
		while True:
			symbol = self.lexer.next()
			
			# stop capturing verbatim on stop character
			# or EOF
			if not symbol or symbol[1] == stop or symbol[1] is None:
				break
			else:
				verbatim.append(symbol[1])
			
		return verbatim
	
	def statement(self, token):
		term = token[2](token[0])
		print isinstance(term, self.lang.Identifier)
		
	def parse(self):
		while True:
			n = self.lexer.next()
			if n is False:
				break
			
			# fast forward through comment blocks
			if n[2] == '[comment_block_open]':
				self.verbatim('*/')
			elif n[2] == '[comment_line]':
				self.verbatim('\n')
			elif n[2] == '[newline]':
				pass
			elif n[2] == '[space]':
				pass
			elif n[2] == '[tab]':
				pass
			elif n[2] == '[keyword]':
				pass
			else:	
				self.statement(n)
			
			
			
lex = Parser(Doubletalk(), 'test.dtk')
lex.parse()
