#!/usr/bin/python

import StringIO, re
from GrammarTree import *

class Doubletalk(object):

	class Lexeme(object):
		def __init__(self, token, **kwargs):
			self.token = token
			self.set(kwargs)

		def set(self, kwargs):
			for i in kwargs:
				setattr(self, i, kwargs[i])

		def handle(self, parser, **kwargs):
			pass

	# white space
	class WhiteSpace(Lexeme):
		pass

	class Space(WhiteSpace):
		pass

	class NewLine(WhiteSpace):
		pass

	class Tab(WhiteSpace):
		pass

	# block delimiters
	class Delimiter(Lexeme):
		pass

	# constants
	class Constant(Lexeme):
		def __repr__(self):
			return '<const>'

		def __str__(self):
			return "<%s:%s const %s>" % (self.token.line, self.token.char, self.token.word)

	class String(Constant):
		pass
	
	class Number(Constant):
		pass

	# operators
	class Operator(Lexeme):
		def __repr__(self):
			return '<op>'

		def __str__(self):
			return "<%s:%s op %s>" % (self.token.line, self.token.char, self.token.word)

	class Assign(Operator):
		pass

	class Equal(Operator):
		pass

	class EqualStrict(Operator):
		pass

	class Subtract(Operator):
		pass

	class Add(Operator):
		pass

	class Increment(Operator):
		pass

	class Decrement(Operator):
		pass

	class Divide(Operator):
		pass

	class Multiply(Operator):
		pass

	# keywords
	class Keyword(Lexeme):
		pass

	class Prnt(Keyword):
		def __repr__(self):
			return '<keyword>prnt'

	class If(Keyword):
		def __repr__(self):
			return '<keyword>if'

	class Then(Keyword):
		def __repr__(self):
			return '<keyword>then'

	#preprocesor
	class Preprocessor(Lexeme):
		pass
		
	class CommentBlock(Preprocessor, Delimiter):
		pass
	
	class CommentLine(Preprocessor, Delimiter):
		pass

	class Include(Preprocessor, Keyword):
		def handle(self, parser):
			print parser()
			return self
		def __repr__(self):
			return '<preprocessor><keyword>include'
		
	# identifiers
	class Identifier(Lexeme):
		def __repr__(self):
			return '<ident>'

	# entity
	class GameObject(Lexeme):
		pass

	class Character(GameObject):
		pass

	class Ego(Character):
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
	r_hash 			= r'[#]'
	r_exclamation 	= r'[!]'
	r_question		= r'[?]'
	r_number 		= r'^[0-9]+'
	r_identifier 	= r'[_a-zA-Z][_a-zA-Z0-9]*'
	r_atsign		= r'[@]'
	r_double_quote 	= r'["]'
	r_single_quote 	= r'[\']'
	
	symbols = {
		r_space: 			lambda t: Doubletalk.Space(t),
		r_newline:			lambda t: Doubletalk.NewLine(t),
		r_tab:				lambda t: Doubletalk.Tab(t),
		r_double_quote: 	lambda t: Doubletalk.String(t),
		r_single_quote: 	lambda t: Doubletalk.String(t),
		r_slash: {
			r_asterisk:		lambda t: Doubletalk.CommentBlock(t, open=True),
			r_slash: 		lambda t: Doubletalk.CommentLine(t),
			None:			lambda t: Doubletalk.Divide(t)
		},
		r_asterisk: {
			r_slash:		lambda t: Doubletalk.CommentBlock(t, open=False),
			None:			lambda t: Doubletalk.Multiply(t)
		},
		r_equal: {
			r_equal: {
				r_equal:	lambda t: Doubletalk.EqualStrict(t),
				None:		lambda t: Doubletalk.Equal(t)
			},
			None: 			lambda t: Doubletalk.Assign(t)
		},
		r_plus: {
			r_plus:			lambda t: Doubletalk.Increment(t),
			None:			lambda t: Doubletalk.Add(t)
		},
		r_dash: {
			r_dash:			lambda t: Doubletalk.Decrement(t),
			None:			lambda t: Doubletalk.Subtract(t)
		},
		r_number: 			lambda t: Doubletalk.Number(t),
		r_identifier:		lambda t: Doubletalk.keywords[t.word](t) if t.word in Doubletalk.keywords else Doubletalk.Identifier(t),
		r_atsign: {
			r_identifier:	lambda t: Doubletalk.Character(t),
			None: 			lambda t: Doubletalk.Ego(t)
		}
	}

	keywords = {
		'prnt':		lambda t: Doubletalk.Prnt(t),
		'if':		lambda t: Doubletalk.If(t),
		'then':		lambda t: Doubletalk.Then(t),
		'include':	lambda t: Doubletalk.Include(t)
	}

	grammar = {
		'<const>': {
			'<op>': lambda: Doubletalk.grammar
		},
		'<ident>': {
			'<op>':	lambda: Doubletalk.grammar,
		}
	}

	
class Lexer(object):

	class Token(object):
		def __init__(self, line, char, word, func=None):
			self.line = line
			self.char = char
			self.word = word
			self.func = func

		def __repr__(self):
			return "Token(line=(%s)%s, char=(%s)%s, word=(%s)'%s'" % (type(self.line), self.line, type(self.char), self.char, type(self.word), self.word)

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
			else:
				char = char.lower()
			
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

		return self.Token(self.nline, self.nchar, ''.join(self.token)) if len(self.token) > 0 else None
		

	def next(self):
	
		tree = self.syntax.symbols
		word = []
		
		while True:
			# get next symbol
			token = self.scan()
			#info,symbol = self.scan()

			# EOF				
			if token is None:
				return False
							
			# search in syntax tree
			for regexp in tree:
				match = None
				if regexp is None:
					continue

				if re.match(regexp, token.word):
					word.append(token.word)
					# move forward in tree
					tree = tree[regexp]
					match = token.word
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

			token.word = ''.join(word)

			return tree(token)
		
class Parser(object):

	class Expression(object):
		pass

	class Statement(object):
		pass

	def __init__(self, lang, source, is_file=True):
		self.lang	= lang
		self.lexer 	= Lexer(lang, source, is_file)
		self.tree 	= []

	def verbatim(self, stop, **kwargs):
		verbatim = []

		while True:
			lexeme = self.lexer.next()
		
			# EOF
			if not lexeme or lexeme is None:
				break

			# is lexeme the stop token?
			if isinstance(lexeme, stop):
				found = True
				# has lexeme the properties we are looking for?
				for p in kwargs:
					# it doesn't
					if not p in lexeme.__dict__:
						found = False	
					# has property but different value?
					elif kwargs[p] != lexeme.__dict__[p]:
						found = False
						# reject lexeme as the stop mark
						break
				if found:
					return verbatim
			else:
				verbatim.append(lexeme.token.word)

		return False
		
	def parse(self, tree=[]):

		legal = self.lang.grammar;
		sentences = []

		while True:
			lexeme = self.lexer.next()
			if lexeme is False:
				break

			if isinstance(lexeme, self.lang.WhiteSpace):
				continue

			# catch preprocessor directives
			if isinstance(lexeme, self.lang.Preprocessor):

				if isinstance(lexeme, self.lang.CommentBlock):
					if not self.verbatim(self.lang.CommentBlock, open=False):
						raise Exception('Comment block missing closure')
					else:
						continue

				if isinstance(lexeme, self.lang.CommentLine):
					self.verbatim(self.lang.NewLine)
					continue

				# catch variables, functions, keywords
				if isinstance(lexeme, self.lang.Keyword):
					#tree.append(lexeme.handle(self.parse))
					continue
			# end of block --- catch preprocessor directives

			sentence = (len(sentence) == 0) ? Sentence() : sentences.pop()

			if isinstance(lexeme, self.lang.ident) or isinstance(lexeme, self.lang.ident):
				sentence.push(lexeme)


			"""
			t = lexeme.__repr__()

			print t

			if isinstance(legal, list):
				legal = legal.pop(0)
				
			if callable(legal):
				legal = legal()
			
			if t in legal:
				if callable(t):
					legal = legal[t]()
				else:
					legal = legal[t]
				
				tree.append(lexeme)

			else:
				print 'Unexpected token "%s" in line %s, char %s.\nExpecting %s' % (lexeme.token.word, lexeme.token.line, lexeme.token.char, ' | '.join(legal.keys()))
				break
			"""
		
			
			
lex = Parser(Doubletalk(), 'test.dtk')
tree = lex.parse()

#print tree

