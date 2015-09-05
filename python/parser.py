import tty, termios, sys
from lang import *

class Lexer(object):

	class Token(object):
		def __init__(self, word, line, char):
			self.word = word
			self.line = line
			self.char = char
			
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
		
		word = ''.join(self.token) if len(self.token) > 0 else None

		if word is None:
			return None

		return self.Token(word, line=self.nline, char=self.nchar)
		

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
				
				try:
				
					if re.match(regexp, token.word):
						word.append(token.word)
						# move forward in tree
						tree = tree[regexp]
						match = token.word
						break
				
				except TypeError as err:
					print token
					print err
					exit(1)
	
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
			
			# return a typed lexeme
			return tree(token.word, (token.line, token.char))

	
class Parser(object):

	def __init__(self, lang, source, is_file=True):
		self.count		= 0
		self.lang		= lang
		self.lexer 		= Lexer(lang, source, is_file)
		self.tree 		= []
		self.pending	= []
		self.blocks		= ['<main>']
	
	def EOF(self):
		if len(self.blocks) > 1:
			pass
			#print self.blocks
			#raise Exception('Missing end statement')
	
		return False
		
	def unnest(self, s, stop):
		n = []
		while True and len(s) > 0:
			i = s.pop(-1)
			if isinstance(i, stop):
				break
			else:
				n.insert(0, i)
				
		return (s,n)
	

	def push_block(self, block):
		self.blocks.append(block)
	
	def pull_block(self):
		if len(self.blocks) <= 1:
			raise Exception('Cannot pull main block')
		return self.blocks.pop()

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
				verbatim.append(lexeme.word)

		return False
		
	
	def next(self, ignore=None):
		
		ignore = (self.lang.Space, self.lang.Tab) if ignore is None else ignore
	
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
		
			if isinstance(lexeme, ignore):
				continue
					
			break
			
		return lexeme
	
	def list(self, s):
		l = []
		e = []
		while True and len(s) > 0:
			i = s.pop(0)
			if isinstance(i, self.lang.Comma):
				l.append(e)
				e = []
				continue
			elif isinstance(i, self.lang.Bracket):
				if i.open:
					e = self.list(s)
				else:
					if len(e) > 0:
						l.append(e)
					return l
			else:
				e.append(i)
		
		l.append(e)	
	
		return l
		
	
	def block(self, until=None, leave=False):
	
		block = []
		
		while True:
		
			i = self.parse(until=until)
						
			# EOF
			if i is False:
				# EOF before expected delimiter
				if until is not None:
					raise Exception('Unexpected EOF')
				# return last statement
				elif len(block) > 0:	
					return block
				else:
					return False
			# stop at delimiter
			if isinstance(i, until):
				self.delimiter = i
				if leave is True:
					self.pending.append(i)
				return block
			# add instruction to block
			else:
				block.append(i)
				
				
	def expression(self, until=None):
		
		expression = self.lang.Expression()
		
		while True:
		
			lexeme = self.next()
				
			# EOF
			if lexeme is False:
				# return last expression
				if len(expression) > 0:
					return expression
				else:
					return False
			
			# commit expression on newline or continue if expression is empty	
			if isinstance(lexeme, self.lang.NewLine):
				if len(expression) > 0:
					return expression
				else:
					continue
					
			if until is not None and isinstance(lexeme, until):
				return expression
			
			# literals
			if isinstance(lexeme, (self.lang.DoubleQuote, self.lang.SingleQuote)):
				if isinstance(lexeme, self.lang.DoubleQuote):
					string = ''.join(self.verbatim(self.lang.DoubleQuote))
				else:
					string = ''.join(self.verbatim(self.lang.SingleQuote))
				
				l = self.lang.String(string, (lexeme.line, lexeme.char))
				expression.push(l)		
				continue
			
			if self.lang.Grammar.is_legal(expression + [lexeme], self.lang.expression):
				expression.push(lexeme)
			else:
				self.pending.append(lexeme)
				print 'Expression rejected %s' % (lexeme)
				print 'Expecting %s' % (expression.hint())
				raise Exception('Unexpected %s' % (lexeme))				
							
		return expression
	
	
	
	def parse(self, until=None):
		
		lexeme = self.next()
		
		if lexeme is False:
			return self.EOF()
			
		if until is not None and isinstance(lexeme, until):
			return lexeme
							
		if isinstance(lexeme, self.lang.Keyword):
			if isinstance(lexeme, self.lang.Block):
				self.push_block((self.count, lexeme))
			elif isinstance(lexeme, self.lang.Delimiter):
				p0, b = self.pull_block()
				lexeme.owner, b.length = (b, self.count - p0 - 1)
			
			# add to instruction counter
			self.count += 1
			return lexeme.parse(self)

		elif isinstance(lexeme, (self.lang.Delimiter, self.lang.Constant, self.lang.Identifier)):
			self.pending.append(lexeme)
			
			# add to instruction counter
			self.count += 1
			return self.expression()

		else:
			# newline, tab & beyond
			return self.parse(until=until)
		
		
	
	def build(self, s=None):
		
		# s as sentence. If s is None, parse self as the tree root
		s = s if s is not None else self
		# n as the node we are building
		n = []
		
		# get rid of superfluous nesting
		if isinstance(s, list) and len(s) == 1 and isinstance(s[0], list):
			s = s.pop()
		
		while s and len(s) > 0:
			
			i = s.pop(0)
			# parentheses grouping
			if isinstance(i, self.lang.Parentheses):
				if i.open:
					# n is the i(n)ner node while s is the remaining (i)nstruction
					n,s = self.unnest(s, self.lang.Parentheses)
					if len(n) > 0:
						n = self.build(n)						
				else:
					raise Exception('Unexpected parentheses at %s' % (i.token.line))
			
			# list without brackets. Like arguments list
			elif isinstance(i, self.lang.Comma):
				return self.lang.List(self.list(n + [i] + s))			
			
			# list with brackets	
			elif isinstance(i, self.lang.Bracket):
				if i.open:
					n.append(self.lang.List(self.list(s)))					
				# closing brackets are dispossed by self.list, so they shouldn't come up here
				else:
					raise Exception('Unexpected bracket at %s' % (i.token.line))		
			
			# operator delimits terms
			elif isinstance(i, self.lang.Operator):
				return [n, i, self.build(s)]
			else:
				n.append(i)
				
		return n
