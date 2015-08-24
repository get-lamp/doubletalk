import StringIO, re
import tty, termios, sys

class Doubletalk(object):

	class Lexeme(object):
		def __init__(self, token, **kwargs):
			self.token = token
			self.set(kwargs)

		def set(self, kwargs):
			for i in kwargs:
				setattr(self, i, kwargs[i])
			
		def __eq__(self, other):
			return self.token.word == other
		
		def __ne__(self, other):
			return self.token.word != other
		
		def lextype(self):
			return '<none>'

		def parse(self, parser, **kwargs):
			pass
		
	# white space
	class WhiteSpace(Lexeme):
		pass

	class Space(WhiteSpace):
		pass

	class NewLine(WhiteSpace):
		def lextype(self):
			return '<newline>'

	class Tab(WhiteSpace):
		pass

	# constants
	class Constant(Lexeme):
		def lextype(self):
			return '<const>'
			
		def __repr__(self):
			return '<const %s>' % (self.token.word)

	class String(Constant):
		pass
	
	class Number(Constant):
		def __int__(self):
			return int(self.token.word)
			
		def __add__(self, other):
			return int(self) + int(other)
		
		def __sub__(self, other):
			return int(self) - int(other)
		
		def __mul__(self, other):
			return int(self) * int(other)
		
		def __div__(self, other):
			return int(self) / int(other)
		
		def eval(self):
			return int(self.token.word)
		
	# operators
	class Operator(Lexeme):
		def lextype(self):
			return '<op>'

		def __repr__(self):
			return '<op %s>' % (self.token.word)
		
		def eval(self, left, right):
			pass

	class Assign(Operator):
		def eval(self, left, right, heap):
			heap[left.label] = right
			return right

	class Equal(Operator):
		def eval(self, left, right, scope):
			return left == right

	class EqualStrict(Operator):
		pass

	class Subtract(Operator):
		def eval(self, left, right, scope):
			return left - right

	class Add(Operator):
		def eval(self, left, right, scope):
			return left + right

	class Increment(Operator):
		def eval(self, left):
			pass

	class Decrement(Operator):
		def eval(self, left):
			pass

	class Divide(Operator):
		def eval(self, left, right, scope):
			return left / right

	class Multiply(Operator):
		def eval(self, left, right, scope):
			return left * right

	# keywords
	class Keyword(Lexeme):
		def lextype(self):
			return '<keyword>'
		def __repr__(self):
			return '<keyword %s>' % (self.token.word)

	# block delimiters
	class Delimiter(Lexeme):
		pass
	
	class End(Delimiter):
		
		def lextype(self):
			return '<end>'

		def __repr__(self):
			return '<end>'
	
	class Then(Delimiter):
		
		def lextype(self):
			return '<then>'

		def __repr__(self):
			return '<then>'

	class Else(Delimiter):
		
		def lextype(self):
			return '<else>'

		def __repr__(self):
			return '<else>'
	
	class Parentheses(Delimiter):
		
		def lextype(self):
			return '<delim>' if self.open else '</delim>'

		def __repr__(self):
			return '<delim>' if self.open else '</delim>'

	# keywords
	class Prnt(Keyword):
		
		def lextype(self):
			return '<prnt>'
		
		def parse(self, parser, **kwargs):
			args = parser.parse();
			return [self, args]
		
		def eval(self, i):
			print i

		def __repr__(self):
			return '<prnt>'

	class If(Keyword):
	
		def __init__(self, token, **kwargs):
			self.condition = None
			self.yay_block = None
			self.nay_block = None
			super(Doubletalk.If, self).__init__(token)

		def lextype(self):
			return '<if>'

		def parse(self, parser, **kwargs):
			
			self.condition 	= parser.parse(until=r'<then>')
			self.yay_block	= parser.parse(until=r'<else>|<end>')
			
			try:
				if parser.delimiter.lextype() == '<else>':
					self.nay_block 	= parser.parse(until=r'<end>')
				elif parser.delimiter.lextype() != '<end>':
					raise Exception('<end> missing')
			except Exception as e:
				print e
				print 'Last delimiter:'
				print parser.delimiter
				print 'Last block parsed: '
				print self.yay_block
				exit(1)
		
			return self #[self.condition, self.yay_block, self.nay_block]
		
		def __repr__(self):
			return '<if>'

	#preprocesor
	class Preprocessor(Lexeme):
		pass
		
	class CommentBlock(Preprocessor, Delimiter):
		pass
	
	class CommentLine(Preprocessor, Delimiter):
		pass

	class Include(Preprocessor, Keyword):
		def parse(self, parser):
			pass
		def lextype(self):
			return '<preprocessor><keyword>include'
		
	# identifiers
	class Identifier(Lexeme):
		
		def __init__(self, token, **kwargs):
			self.label = token.word
			super(Doubletalk.Identifier, self).__init__(token)
		
		def lextype(self):
			return '<ident>'
		
		def __repr__(self):
			return '<ident %s>' % (self.token.word)
		
		def eval(self, heap):
			return heap.get(self.label, None)

	# entity
	class GameObject(Lexeme):
		pass

	class Character(GameObject):
		pass

	class Ego(Character):
		pass

	keywords = {
		'prnt':		lambda t: Doubletalk.Prnt(t),
		'if':		lambda t: Doubletalk.If(t),
		'then':		lambda t: Doubletalk.Then(t),
		'else':		lambda t: Doubletalk.Else(t),
		'end':		lambda t: Doubletalk.End(t),
		'include':	lambda t: Doubletalk.Include(t)
	}

	statement = {
		r'<delim>': lambda: Doubletalk.statement,
		r'<const>|<ident>': {
			'<op>': lambda: Doubletalk.statement,
			'</delim>': lambda: Doubletalk.statement[r'<const>|<ident>'],
		}
	}
		
	class Statement(list):
		def __init__(self):
			self.grammar = Doubletalk.statement
			super(Doubletalk.Statement, self).__init__()
		
		def is_legal(self, i):
	
			for r in self.grammar:
						
				if re.match(r, i.lextype()):
					return r
					
			return False

		def push(self, i):
			if len(self) == 0:
				self.grammar = Doubletalk.statement
				
			l = self.is_legal(i)
			# push term
			if l:
				self.grammar = self.grammar[l] if not callable(self.grammar[l]) else self.grammar[l]()
				super(Doubletalk.Statement, self).append(i)	
				return self	
								
			# close statement
			return False
			
		def build(self, s=None):
			# if s is None, parse self. That is the root
			s = s if s is not None else self
			t = []
			while len(s) > 0:
				# catch parentheses
				if isinstance(s[0], Doubletalk.Parentheses):
					p = s.pop(0)
					if p.open:
						g = []
						while not isinstance(s[0], Doubletalk.Parentheses) and len(s) > 1
							g.append(s.pop(0))
						t.append(self.build(g))
					
					return t
				
				# second operand its an expression
				if len(t) >= 2 and len(s) > 1:
					t.append(self.build(s))
				elif len(s) > 0:
					# do not push delimiters
					if isinstance(s[0], Doubletalk.Delimiter):
						s.pop(0)
					else:
						# a constant or identifier
						t.append(s.pop(0))
			
			return t
	
		
	delimiters = "[.:!,;+*^&@#$%&'\"\-\\/\|=$()?<>\s]"
	
	r_space 		= r'[ ]'
	r_newline		= r'[\n]'
	r_tab 			= r'[\t]'
	r_slash 		= r'[/]'
	r_asterisk 		= r'[*]'
	r_equal 		= r'[=]'
	r_plus 			= r'[+]'
	r_dash 			= r'[-]'
	r_parentheses_l = r'[(]'
	r_parentheses_r	= r'[)]'
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
		r_parentheses_l: 	lambda t: Doubletalk.Parentheses(t, open=True),
		r_parentheses_r:	lambda t: Doubletalk.Parentheses(t, open=False),
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

	def backtrack(self, n=1):
		self.src.seek(-n, 1)
		return self
		
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
					self.backtrack(1)
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
					self.backtrack(1)
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

	def __init__(self, lang, source, is_file=True):
		self.lang	= lang
		self.lexer 	= Lexer(lang, source, is_file)
		self.tree 	= []
		self.pending = []

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
		
	def parse(self, until='<newline>'):
	
		block = []
		statement = Doubletalk.Statement()
		self.delimiter = None
		
		try:
			while True:
				lexeme = self.pending.pop() if len(self.pending) > 0 else self.lexer.next()
			
				# EOF
				if lexeme is False:
					return False
			
				# preprocessor directives
				if isinstance(lexeme, self.lang.Preprocessor):
					if isinstance(lexeme, self.lang.CommentLine):
						# skips until newline
						self.verbatim(self.lang.NewLine)
						continue
					if isinstance(lexeme, self.lang.CommentBlock):
						# skips until closed comment block
						self.verbatim(self.lang.CommentBlock, open=False)
						continue
			
				# newline in an empty line
				if isinstance(lexeme, self.lang.NewLine) and len(block) == 0 and len(statement) == 0:
					continue
				
				# stop character
				#print 'Testing %s against %s' % (until, lexeme.lextype())
				if re.match(until, lexeme.lextype()):
					self.delimiter = lexeme
					# what is this?
					if len(statement) > 0:	
						block.append(statement.build())
					break
				
				# EOL
				if isinstance(lexeme, self.lang.NewLine):
					continue

				# white space
				if isinstance(lexeme, self.lang.WhiteSpace):
					continue
			
				#print 'Found: %s' % (lexeme)
				
				# keywords
				if isinstance(lexeme, self.lang.Keyword):
					#print 'Taking keyword route'
					block.append(lexeme.parse(self, keyword=lexeme))
					continue
			
				# try to push to an expression	
				if not statement.push(lexeme):
					#print 'Rejected: %s' % (lexeme)
					self.pending.append(lexeme)
					if len(statement) > 0:
						# push built statement
						block.append(statement.build())
						continue
					else:
						raise Exception("Unexpected '%s' in line %s" % (lexeme.token.word, lexeme.token.line))
						break
		except Exception as e:
			print e
			exit(1)
			
		return block

