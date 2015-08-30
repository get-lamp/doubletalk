import StringIO, re

class Doubletalk(object):

	delimiters = "[\"\'.:!,;+*^&@#$%&\-\\/\|=$()?<>\s]"
	
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
	r_double_quote 	= r'[\"]'
	r_single_quote 	= r"[\']"
	r_number 		= r'^[0-9]+'
	r_identifier 	= r'[_a-zA-Z][_a-zA-Z0-9]*'
	r_atsign		= r'[@]'
	
	symbols = {
		r_space: 			lambda t: Doubletalk.Space(t),
		r_newline:			lambda t: Doubletalk.NewLine(t),
		r_tab:				lambda t: Doubletalk.Tab(t),
		r_double_quote: 	lambda t: Doubletalk.DoubleQuote(t),
		r_single_quote: 	lambda t: Doubletalk.SingleQuote(t),
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

	keywords = {
		'prnt':		lambda t: Doubletalk.Prnt(t),
		'if':		lambda t: Doubletalk.If(t),
		'then':		lambda t: Doubletalk.Then(t),
		'else':		lambda t: Doubletalk.Else(t),
		'end':		lambda t: Doubletalk.End(t),
		'include':	lambda t: Doubletalk.Include(t)
	}

	expression = {
		r'<delim>': lambda: Doubletalk.expression,
		r'<const>|<ident>': {
			'<op>': lambda: Doubletalk.expression,
			'</delim>': lambda: Doubletalk.expression[r'<const>|<ident>']
		}
	}
	
	statement = {
		r'<prnt>': lambda: Doubletalk.expression,
		r'<if>': {
			r'<expression>': {
				r'<then>': {
					r'<statement>': lambda: Doubletalk.statement[r'<if>'][r'<expression>'][r'<then>'],
					r'<else>': {
						r'<statement>': lambda: Doubletalk.statement[r'<if>'][r'<expression>'][r'<then>'][r'<else>'],
						r'<end>': None
					},
					r'<end>': None
				}
			}
		}
	}

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
		def eval(self):
			return str(self.token.word)
	
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
		
	class Parentheses(Delimiter):
		
		def lextype(self):
			return '<delim>' if self.open else '</delim>'

		def __repr__(self):
			return '<delim>' if self.open else '</delim>'
	
	class DoubleQuote(Delimiter):
		
		def lextype(self):
			return '<d-quote>'

		def __repr__(self):
			return '<d-quote>'
	
	class SingleQuote(Delimiter):
		
		def lextype(self):
			return '<s-quote>'

		def __repr__(self):
			return '<s-quote>'

	# keywords
	class Prnt(Keyword):
		
		def lextype(self):
			return '<prnt>'
		
		def parse(self, parser, **kwargs):
			text = parser.expression();
			return [self, text]
		
		def eval(self, interp, expression):
			print interp.getval(interp.eval(expression))

		def __repr__(self):
			return '<prnt>'
	
	class Control(object):
		pass
	
	class If(Keyword,Control):
	
		def __init__(self, token, **kwargs):
			super(Doubletalk.If, self).__init__(token)

		def lextype(self):
			return '<if>'

		def parse(self, parser, **kwargs):
			# store condition pre-built
			condition = parser.build(parser.expression(until=Doubletalk.Then))
			return [self, condition]
		

		def eval(self, interp, expr):
			interp.push_read_enabled(bool(interp.eval(expr)))
	
		def __repr__(self):
			return '<if>'
	
	class Then(Keyword,Control):
		
		def lextype(self):
			return '<then>'
			
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=(Doubletalk.Else, Doubletalk.End))
			return [self]
		
		def eval(self, interp, expr):
			interp.push_read_enabled(True if interp.stack() else False)

		def __repr__(self):
			return '<then>'

	class Else(Keyword,Control):
		
		def lextype(self):
			return '<else>'
		
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=Doubletalk.End)
			return [self]
			
		def eval(self, interp, expr):
			interp.toggle_read_enabled()

		def __repr__(self):
			return '<else>'
	
	class End(Keyword,Control):
		
		def lextype(self):
			return '<end>'
			
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=Doubletalk.End)
			return [self]
		
		def eval(self, interp, expr):
			interp.pull_read_enabled()

		def __repr__(self):
			return '<end>'

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

	class Grammar(list):
		def __init__(self, rules):
			self.grammar	= rules
			self.legal 		= rules
			super(Doubletalk.Grammar, self).__init__()
		
		# does lexeme belong to this grammar
		@staticmethod
		def belongs(i, grammar):
			branch = grammar
			# iterate through currently legal words	
			for r in branch:	
				if re.match(r, i.lextype()):
					return True
				elif branch.get(r, None) is not None:
					branch = branch[r] if not callable(branch[r]) else branch[r]()
					
			return False
		
		@staticmethod
		def is_legal(s, grammar):
			rules = grammar
			# iterate through words in sentence
			for i in s:
				# iterate through currently legal words	
				found = False
				for r in rules:
					if re.match(r, i.lextype()):
						rules = rules[r] if not callable(rules[r]) else rules[r]()
						found = True
						break
						
				if not found:
					return False
			return True
		
		
			
		def hint(self):
			if self.legal is None:
				return None
			else:
				return self.legal.keys()
		
		def can_push(self, i):
			# iterate through currently legal words	
			for r in self.legal:	
				if re.match(r, i.lextype()):
					return r
			return False

		def push(self, i):
			# if instruction begins, legal should point to all instruction set
			if len(self) == 0:
				self.legal = self.grammar
				
			l = self.can_push(i)
			#print 'Is legal %s? %s %s %s' % (self.__class__.__name__, i.lextype(), self.hint(), l)
			# push term
			if l:
				# climb up in grammar tree
				self.legal = self.legal[l] if not callable(self.legal[l]) else self.legal[l]()
				super(Doubletalk.Grammar, self).append(i)	
				return self
				
			# close
			return False
		
	class Statement(Grammar):
		def __init__(self):
			super(Doubletalk.Statement, self).__init__(Doubletalk.statement)
		
		def lextype(self):
			return '<statement>'
		
	class Expression(Grammar):
		def __init__(self):
			super(Doubletalk.Expression, self).__init__(Doubletalk.expression)
		
		def lextype(self):
			return '<expression>'
