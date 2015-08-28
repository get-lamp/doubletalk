import tty, termios, sys
from lang import *

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
		
		
	def unnest(self, s, stop, **kwargs):
		n = []
		while True and len(s) > 0:
			i = s.pop(-1)
			if isinstance(i, stop):
				break
			else:
				n.insert(0, i)
				
				
		return (s,n)
		

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
		
	
	def next(self):
	
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
			
			# ignore newline in an empty line
			#if isinstance(lexeme, self.lang.NewLine) and len(block) == 0 and len(statement) == 0:
			#	continue
					
			# EOL
			if isinstance(lexeme, self.lang.NewLine):
				continue

			# white space
			if isinstance(lexeme, self.lang.WhiteSpace):
				continue
			
			break
			
		return lexeme
		
	
	def statement(self):
	
		statement = self.lang.Statement()
	
		while True:
		
			lexeme = self.next()
			
			# statement
			if statement.push(lexeme):
				print 'Accepted statement %s' % (lexeme.lextype())
			elif '<expression>' in statement.hint():
			
				print 'Rejected statement %s expecting %s' % (lexeme, statement.hint())
				self.pending.append(lexeme)
				statement.push(self.expression())
				break
				
		return statement
	
					
	def expression(self):
		
		expression = self.lang.Expression()
		
		while True:
		
			lexeme = self.next()
	
			# expression
			if expression.push(lexeme):
				print 'Accepted expression %s' % (lexeme.lextype())
			elif lexeme.lextype() in self.lang.statement:
				
				print 'Rejected expression %s expecting %s' % (lexeme, expression.hint()) 
				self.pending.append(lexeme)
				
				#expression.push(self.expression())
				break
		
		return expression
	
	
	
	def parse(self):
		
		block = []
		lexeme = self.next()
				
		if isinstance(lexeme, self.lang.Keyword):
			self.pending.append(lexeme)
			return self.statement()
		elif isinstance(lexeme, (self.lang.Delimiter, self.lang.Constant, self.lang.Identifier)):
			self.pending.append(lexeme)
			return self.expression()
		
		
		
	def _parse(self, until='<newline>'):
	
		block = []
		statement = Doubletalk.Statement()
		self.delimiter = None
		
		try:
			while True:
				lexeme = self.pending.pop() if len(self.pending) > 0 else self.lexer.next()
			
				# EOF
				if lexeme is False:
					# EOF while looking for a delimiter?
					if until != '<newline>':
						raise Exception('Unexpected end of file. Missing %s' % (until))
					else:
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
			
				# ignore newline in an empty line
				if isinstance(lexeme, self.lang.NewLine) and len(block) == 0 and len(statement) == 0:
					continue
				
				# stop character
				#print 'Testing %s against %s' % (until, lexeme.lextype())
				if re.match(until, lexeme.lextype()):
					self.delimiter = lexeme
					# what is this?
					if len(statement) > 0:	
						block.append(statement)
					break
				
				# EOL
				if isinstance(lexeme, self.lang.NewLine):
					continue

				# white space
				if isinstance(lexeme, self.lang.WhiteSpace):
					continue
			
				print 'Found: %s' % (lexeme)

				# literals
				if isinstance(lexeme, (self.lang.DoubleQuote, self.lang.SingleQuote)):
					if isinstance(lexeme, self.lang.DoubleQuote):
						statement.append(''.join(self.verbatim(self.lang.DoubleQuote)))
					else:
						statement.append(''.join(self.verbatim(self.lang.SingleQuote)))
					continue
				
				# keywords
				if isinstance(lexeme, self.lang.Keyword):
					#print 'Taking keyword route'
					block.append(lexeme.parse(self, keyword=lexeme))
					break
				
				# try to push to an expression	
				if not statement.push(lexeme):
					print 'Rejected: %s' % (lexeme)
					# word may belong to next instruction
					self.pending.append(lexeme)
					statement = Doubletalk.Statement()
					if len(statement) > 0:
						# push built statement
						block.append(statement)
						continue
					# first lexeme in instruction couldn't be pushed, so there is an error
					#else:
					#	print 'Expecting %s' % ([z for z in statement.grammar.keys()])
					#	raise Exception("Unexpected '%s' in line %s" % (lexeme.lextype(), lexeme.token.line))
					#	break
			print block

		except Exception as e:
			raise
			
		return block
	
	def build(self, s=None):
		
		# if s is None, parse self. That is the root
		s = s if s is not None else self
		t = []
		n = []
		
		# get rid of superfluous nesting
		if isinstance(s, list) and len(s) == 1 and isinstance(s[0], list):
			s = s.pop()
		
		while s and len(s) > 0:
			
			i = s.pop(0)
			# grouping
			if isinstance(i, self.lang.Parentheses):
				if i.open:
					# n is the i(n)ner node while s is the remaining (i)nstruction
					n,s = self.unnest(s, self.lang.Parentheses, open=False)
					if len(n) > 0:
						n = self.build(n)						
				else:
					raise Exception('Unexpected parentheses at %s' % (i.token.line))
			
			# operator delimits terms
			elif isinstance(i, self.lang.Operator):
				return [n, i, self.build(s)]
			else:
				n.append(i)
				
		return n
