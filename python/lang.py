import StringIO, re

# 	TODO 
#	weird delimiter characters behavior 
#	get rid of tags. Use isinstace() instead

class Doubletalk(object):

	delimiters = "[\"\':!,;+*^&@#$%&\-\\/\|=$()?<>\s\[\]]"
	
	r_space 		= r'[ ]'
	r_newline		= r'[\n]'
	r_tab 			= r'[\t]'
	r_slash 		= r'[/]'
	r_asterisk 		= r'[*]'
	r_comma 		= r'[,]'
	r_equal 		= r'[=]'
	r_plus 			= r'[+]'
	r_dash 			= r'[-]'
	r_bracket_l 	= r'[\[]'
	r_bracket_r		= r'[\]]'
	r_parentheses_l = r'[(]'
	r_parentheses_r	= r'[)]'
	r_hash 			= r'[#]'
	r_bang 			= r'[!]'
	r_question		= r'[?]'
	r_double_quote 	= r'[\"]'
	r_single_quote 	= r"[\']"
	r_float			= r'^[0-9]*\.[0-9]+$'
	r_int	 		= r'^[0-9]+$'
	r_identifier 	= r'[_a-zA-Z][_a-zA-Z0-9]*'
	r_atsign		= r'[@]'
	
	symbols = {
		r_space: 			lambda w,t: Doubletalk.Space(w,t),
		r_newline:			lambda w,t: Doubletalk.NewLine(w,t),
		r_tab:				lambda w,t: Doubletalk.Tab(w,t),
		r_bracket_l: 		lambda w,t: Doubletalk.Bracket(w,t,open=True),
		r_bracket_r:		lambda w,t: Doubletalk.Bracket(w,t,open=False),
		r_double_quote: 	lambda w,t: Doubletalk.DoubleQuote(w,t),
		r_single_quote: 	lambda w,t: Doubletalk.SingleQuote(w,t),
		r_parentheses_l: 	lambda w,t: Doubletalk.Parentheses(w,t, open=True),
		r_parentheses_r:	lambda w,t: Doubletalk.Parentheses(w,t, open=False),
		r_slash: {
			r_asterisk:		lambda w,t: Doubletalk.CommentBlock(w,t, open=True),
			r_slash: 		lambda w,t: Doubletalk.CommentLine(w,t),
			None:			lambda w,t: Doubletalk.Divide(w,t)
		},
		r_asterisk: {
			r_slash:		lambda w,t: Doubletalk.CommentBlock(w,t, open=False),
			None:			lambda w,t: Doubletalk.Multiply(w,t)
		},
		r_comma: 			lambda w,t: Doubletalk.Comma(w,t),
		r_bang: {
			r_equal: {
				r_equal:	lambda w,t: Doubletalk.InequalStrict(w,t),
				None:		lambda w,t: Doubletalk.Inequal(w,t)
			},
			None: 			lambda w,t: Doubletalk.Assign(w,t)
		},
		r_equal: {
			r_equal: {
				r_equal:	lambda w,t: Doubletalk.EqualStrict(w,t),
				None:		lambda w,t: Doubletalk.Equal(w,t)
			},
			None: 			lambda w,t: Doubletalk.Assign(w,t)
		},
		r_plus: {
			r_plus:			lambda w,t: Doubletalk.Increment(w,t),
			None:			lambda w,t: Doubletalk.Add(w,t)
		},
		r_float: 			lambda w,t: Doubletalk.Float(w,t),
		r_int: 				lambda w,t: Doubletalk.Integer(w,t),
		r_dash: {
			r_dash:			lambda w,t: Doubletalk.Decrement(w,t),
			r_float: 		lambda w,t: Doubletalk.Float(w,t),
			r_int: 			lambda w,t: Doubletalk.Integer(w,t),
			None:			lambda w,t: Doubletalk.Subtract(w,t)
		},
		
		r_identifier:		lambda w,t: Doubletalk.keywords[w](w,t) if w in Doubletalk.keywords else Doubletalk.Identifier(w,t),
		r_atsign: {
			r_identifier:	lambda t: Doubletalk.Character(w,t),
			None: 			lambda t: Doubletalk.Ego(w,t)
		}
	}

	keywords = {
		'prnt':			lambda w,t: Doubletalk.Prnt(w,t),
		'if':			lambda w,t: Doubletalk.If(w,t),
		'then':			lambda w,t: Doubletalk.Then(w,t),
		'else':			lambda w,t: Doubletalk.Else(w,t),
		'end':			lambda w,t: Doubletalk.End(w,t),
		'procedure':	lambda w,t: Doubletalk.Procedure(w,t),
		'def':			lambda w,t: Doubletalk.Def(w,t),
		'exec':			lambda w,t: Doubletalk.Exec(w,t),
		'include':		lambda w,t: Doubletalk.Include(w,t)
	}

	expression = {
		r'<delim>|<bracket>': lambda: Doubletalk.expression,
		r'<const>|<ident>': {
			r'<bracket>|<const>|<ident>': lambda: Doubletalk.expression[r'<const>|<ident>'],
			'<op>': lambda: Doubletalk.expression,
			'</delim>|</bracket>': lambda: Doubletalk.expression[r'<const>|<ident>'],
			'<comma>': lambda: Doubletalk.expression
		}
	}
	
	class Lexeme(object):
		def __init__(self, word, pos=(None,None), **kwargs):
			self.word = word
			self.line, self.char = pos
			self.set(kwargs)
			self.length = 0
			self.owner = None

		def set(self, kwargs):
			for i in kwargs:
				setattr(self, i, kwargs[i])
		
		def type(self):
			return '<none>'

		def parse(self, parser, **kwargs):
			pass

		def __repr__(self):
			return '<%s><%s>' % (self.__class__.__name__, self.word)
		
	# white space
	class WhiteSpace(Lexeme):
		pass

	class Space(WhiteSpace):
		pass

	class NewLine(WhiteSpace):
		def type(self):
			return '<newline>'

	class Tab(WhiteSpace):
		pass

	# base types
	class Struct(Lexeme):
		def type(self):
			return '<struct>'
			
	class Constant(Lexeme):
		def type(self):
			return '<const>'
			
		def __repr__(self):
			return '<const %s>' % (self.word)

	class String(str, Constant):
		def __init__(self, string, pos=(None,None)):
			super(Doubletalk.String, self).__init__(string, pos)
		
		def __new__(cls, *args, **kw):
			string,pos = args
			return  super(Doubletalk.String, cls).__new__(cls, string)
			
		def eval(self):
			return str(self)
	

	class Float(float, Constant):
		
		def __init__(self, number, pos=(None,None)):
			super(Doubletalk.Float, self).__init__(number, pos)
		
		def __new__(cls, *args, **kw):
			number,pos = args
			return  super(Doubletalk.Float, cls).__new__(cls, number)

		def eval(self):
			return self
	
	class Integer(int, Constant):
		
		def __init__(self, number, pos=(None,None)):
			super(Doubletalk.Integer, self).__init__(number, pos)
		
		def __new__(cls, *args, **kw):
			number,pos = args
			return  super(Doubletalk.Integer, cls).__new__(cls, number)

		def eval(self):
			return self
	
	class List(list, Struct):
	
		def __init__(self, l=[]):
			list.__init__(self, l)
			
		def type(self):
			return '<list>'
			
		def __add__(self, other):
			return Doubletalk.List(list.__add__(self, other))
		
		def __getitem__(self, item):
			result = list.__getitem__(self, item)
			try:
				return Doubletalk.List(result)
			except TypeError:
				return result
        	
		def eval(self):
			return self
		
	# operators
	class Operator(Lexeme):
		def type(self):
			return '<op>'

		def __repr__(self):
			return '<op %s>' % (self.word)
		
		def eval(self, left, right):
			pass

	class Assign(Operator):
		def eval(self, left, right, heap):
			heap[left.word] = right
			return left

	class Equal(Operator):
		def eval(self, left, right, scope):
			return left == right

	class Inequal(Operator):
		def eval(self, left, right, scope):
			return left != right

	class EqualStrict(Operator):
		pass
	
	class InequalStrict(Operator):
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

	# delimiters
	class Delimiter(Lexeme):
		pass
	
	# expression delimiters	
	class Parentheses(Delimiter):
		
		def type(self):
			return '<delim>' if self.open else '</delim>'

		def __repr__(self):
			return '<delim>' if self.open else '</delim>'
			
	class Bracket(Delimiter):
		
		def type(self):
			return '<bracket>' if self.open else '</bracket>'

		def __repr__(self):
			return '<bracket>' if self.open else '</bracket>'
	
	# list delimiter
	class Comma(Delimiter):
		
		def type(self):
			return '<comma>'

		def __repr__(self):
			return '<comma>'
	
	# string delimiters
	class DoubleQuote(Delimiter):
		
		def type(self):
			return '<d-quote>'

		def __repr__(self):
			return '<d-quote>'
	
	class SingleQuote(Delimiter):
		
		def type(self):
			return '<s-quote>'

		def __repr__(self):
			return '<s-quote>'

	# keywords
	class Block(object):
		# def begin
		# def end
		# def length
		pass
			
	class Control(object):
		pass
		
	class Keyword(Lexeme):
		
		def type(self):
			return '<keyword>'
			
		def __repr__(self):
			return '<keyword %s>' % (self.word)
	
	class Procedure(Keyword,Block,Control):

		def __init__(self, word, pos=(None,None), **kwargs):
			self.address	= None
			self.identifier = None
			self.signature 	= []
			super(Doubletalk.Procedure, self).__init__(word, pos=(None,None), **kwargs)
			
		def type(self):
			return '<procedure>'
		
		def parse(self, parser, **kwargs):	
			print 'Procedure is being parsed'

			# parse identifier
			self.identifier = [parser.next()]			
			
			try:
				# get arguments
				self.signature = parser.build(parser.expression())
			except Exception as e:
				signature = []
							
			return [self, self.identifier, self.signature]
		
		def eval(self, interp, signature):
			print "Procedure is being eval'd"

			# store procedure address
			self.address = interp.pntr

			# eval procedure identifier, leaving room for dynamic procedures
			self.identifier = interp.getval(self.identifier, ref=False)
				
			# store identifier & memory address
			interp.bind(self.identifier.word, self)
			
			# skip function block. We are just declaring the function		
			interp.move(self.length+1)

	class Def(Procedure):
		def __init__(self, word, pos=(None,None), **kwargs):
			self.block = []
			super(Doubletalk.Procedure, self).__init__(word, pos=(None,None), **kwargs)

		def parse(self, parser, **kwargs):	
			# parse identifier
			self.identifier = [parser.next()]			
			
			try:
				# get arguments
				self.signature = parser.build(parser.expression())
			except Exception as e:
				signature = []

			# get function block
			self.block = parser.block(until=Doubletalk.End)

			return [self, self.identifier, self.signature]

		def eval(self, interp, signature):
			
			# store procedure address
			self.address = interp.pntr

			# eval procedure identifier, leaving room for dynamic procedures
			self.identifier = interp.getval(self.identifier, ref=False)
					
			# store identifier & memory address
			interp.bind(self.identifier.word, self)
		
		def call(self, interp, arguments):			
			return interp.call(self, arguments)
				
	
	class Exec(Keyword):
		
		def type(self):
			return '<exec>'
		
		def parse(self, parser, **kwargs):
			
			identifier = [parser.next()]			
			
			try:
				signature = parser.build(parser.expression())
			except Exception as e:
				signature = []
				
			return [self, identifier, signature]
		
		def eval(self, interp, signature):
	
			# get arguments if any
			if len(signature) > 1:
				arguments = interp.eval(signature.pop())
			
			# get identifier from instruction line
			identifier = interp.getval(signature.pop(), ref=True)
			
			# get procedure from scope
			routine = interp.fetch(identifier)
		
			return interp.call(routine, arguments)
						
			
	class Prnt(Keyword):
		
		def type(self):
			return '<prnt>'
		
		def parse(self, parser, **kwargs):
			text = parser.expression()
			return [self, text]
		
		def eval(self, interp, expression):
			print interp.getval(interp.eval(expression))

		def __repr__(self):
			return '<prnt>'
	

	class If(Keyword,Block,Control):
	
		def type(self):
			return '<if>'

		def parse(self, parser, **kwargs):
			# store condition pre-built
			condition = parser.build(parser.expression(until=Doubletalk.Then))
			return [self, condition]
		

		def eval(self, interp, expr):
			interp.push_read_enabled(bool(interp.eval(expr)))
			interp.push_block(self)
	
		
	class Then(Keyword,Control):
		
		def type(self):
			return '<then>'
			
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=(Doubletalk.Else, Doubletalk.End))
			return [self]
		
		def eval(self, interp, expr):
			interp.push_read_enabled(True if interp.stack() else False)


	class Else(Keyword,Control):
		
		def type(self):
			return '<else>'
		
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=Doubletalk.End)
			return [self]
			
		def eval(self, interp, expr):
			interp.toggle_read_enabled()

	
	class End(Keyword,Control,Delimiter):
		
		def type(self):
			return '<end>'
			
		def parse(self, parser, **kwargs):
			#block = parser.parse(until=Doubletalk.End)
			return [self]
		
		def eval(self, interp, expr):
		
			block = interp.block()
			
			if isinstance(block, Doubletalk.If):
				interp.endif()
			elif isinstance(block, Doubletalk.Procedure):
				print 'Ending procedure block'
				interp.endcall()
			elif isinstance(block, Doubletalk.Def):
				print 'Ending def block'
				interp.endcall()
			else:
				print interp.block_stack
				raise Exception('Unknown block type')


	#preprocesor
	class Preprocessor(Lexeme):
		pass
		
	class CommentBlock(Preprocessor, Delimiter):
		pass
	
	class CommentLine(Preprocessor, Delimiter):
		pass

	class Include(Preprocessor, Keyword):
		
		def type(self):
			return '<include>'
			
		def parse(self, parser):
			src = parser.expression()
			return [self, src]

		def eval(self, interp, source):
			print source
			exit(1)
		
	# identifiers
	class Identifier(Lexeme):
		
		def type(self):
			return '<ident>'
				
		def eval(self, scope, call=None, interp=None):
			v = scope.get(self.word, None)
			if call is not None:
				return v.call(interp, call)
			else:
				return v

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
				if re.match(r, i.type()):
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
					if re.match(r, i.type()):
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
				if re.match(r, i.type()):
					return r
			return False

		def push(self, i):
			# if instruction begins, legal should point to all instruction set
			if len(self) == 0:
				self.legal = self.grammar
				
			l = self.can_push(i)
			#print 'Is legal %s? %s %s %s' % (self.__class__.__name__, i.type(), self.hint(), l)
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
		
		def type(self):
			return '<statement>'
		
	class Expression(Grammar):
		def __init__(self):
			super(Doubletalk.Expression, self).__init__(Doubletalk.expression)
		
		def type(self):
			return '<expression>'
