from parser import *
from doubletalk import Doubletalk

OPERAND_L	= 0
OPERATOR 	= 1
OPERAND_R	= 2

class Interpreter(object):

	class Memory(object):
		def __init__(self):
			self.instr 	= []
			self.stack	= []
			self.scope 	= [{}]	

	def __init__(self):
		self.parser 		= Parser(Doubletalk(), 'test2.dtk')
		self.lang			= self.parser.lang
		self.memory			= Interpreter.Memory()
		self.ctrl_stack		= [True]
		self.block_stack	= ['<main>']
		self.pntr 			= 0

	def load(self):
	
		while True:
			instr = self.parser.parse()
			
			if instr is False or instr is None:
				return False

			#build grammar tree
			gtree = self.parser.build(instr)
			
			# append to instruction memory block
			self.memory.instr.append(gtree)
		
	def exec_all(self, source=[], build=True):
	
		for i in source:
			r = self.eval(i) if build is None else self.eval(self.parser.build(i))
			
		return r
	
	def exec_next(self):

		try:
			# debugging
			print 'Pntr %s %s' % ('\t'*2, self.pntr)
			print 'Block %s %s' % ('\t'*2, self.block_stack)
			print 'Scope %s %s' % ('\t'*2, self.memory.scope)
			
			#print 'Heap %s %s' % ('\t'*2, self.memory.heap)
			print 'Stack %s %s' % ('\t'*2, self.memory.stack)
			print 'Read %s %s' % ('\t'*2, self.ctrl_stack)
			print 'Instruction is %s %s' % ('\t'*1, self.memory.instr[self.pntr])
			
			print '-'*80
			# eval the instructions	
			r = self.eval(self.memory.instr[self.pntr])
		

		except IndexError as ie:
			return False
		self.pntr += 1
		return r
		
	def scope(self):
		return self.memory.scope[-1]
	
	def bind(self, i, v):
		if isinstance(i, self.lang.Identifier):
			i = i.word
		self.scope()[i] = v
	
	def fetch(self, i):
		if isinstance(i, self.lang.Identifier):
			i = i.word
		return self.scope().get(i, None)
	
	def push_scope(self, namespace={}):
		scp = namespace.copy()
		scp.update(self.scope())
		self.memory.scope.append(scp)
	
	def pull_scope(self):
		return self.memory.scope.pop()

	# absolute addressing
	def goto(self, n):
		self.pntr = n;
	
	# relative addressing
	def move(self, i):
		self.pntr += i
	
	def call(self, routine, arguments):
		print 'Calling routine %s' % (routine.identifier)

		# push block
		self.push_block(routine)
		
		# address & get signarure
		address = routine.address
		signature = routine.signature
	
		# check signature match with arguments		
		if len(signature) != len(arguments):
			raise Exception('Function expects %s arguments. Given %s' % (len(signature), len(arguments)))
		
		self.push_scope()
		
		if len(signature) > 0:
			# assign calling args to routine signature
			for k,v in enumerate(self.getval(signature)):
				self.bind(signature[k][0], arguments[k])
		
		# is function. Return last statement eval
		if isinstance(routine, self.lang.Def):
			ret = self.exec_all(routine.block)
			print ret
			self.endcall()
			return ret
		# is procedure. Return nothing. Move instruction pointer
		else:
			# push return address to stack
			self.stack_push({'ret_addr': self.pntr})
			self.goto(address)
		
	
	def endcall(self):
		
		ret_addr = None
		
		if len(self.memory.stack) > 0:
			stack = self.stack_pull()
			ret_addr = stack.get('ret_addr', None)
		
		self.endblock()
		self.pull_scope()
				
		if ret_addr is None:
			return
		
		self.goto(ret_addr)	
	
	
	def endblock(self):
		self.pull_block()
		
	def endif(self):
		self.pull_read_enabled()
		self.endblock()
		
	def block(self):
		return self.block_stack[-1]
	
	def push_block(self, block):
		if not isinstance(block, self.lang.Block):
			raise Exception('Tried to push a non-block statement')
		self.block_stack.append(block)
	
	def pull_block(self):
		return self.block_stack.pop()
	
	def stack(self):
		return self.memory.stack[-1]
	
	def stack_push(self, v):
		self.memory.stack.append(v)
	
	def stack_pull(self):
		return self.memory.stack.pop()
	
	def is_read_enabled(self):
		return self.ctrl_stack[-1]
	
	def toggle_read_enabled(self):
		# if parent block isn't executable, child blocks aren't neither
		if not self.ctrl_stack[-2:-1][0]: 
			self.ctrl_stack[-1] = False
		else:
			self.ctrl_stack[-1] = not self.ctrl_stack[-1]
		
	def push_read_enabled(self, boolean):
		# if parent block isn't executable, child blocks aren't neither
		if not self.is_read_enabled():
			self.ctrl_stack.append(False)
		else:
			self.ctrl_stack.append(boolean)
	
	def pull_read_enabled(self):
		return self.ctrl_stack.pop()
	
	def getval(self, i, **kwargs):
		
		# it's nested
		if isinstance(i, list) and not isinstance(i, self.lang.List):	
			return self.getval(i.pop(), **kwargs)
		# identifiers
		if isinstance(i, self.lang.Identifier):
			
			# return memory address identifier
			if kwargs.get('ref', None) is not None:
				return i
			# return value in memory
			else:
				return i.eval(self.scope())
		
		# structs
		elif isinstance(i, self.lang.Struct):
			return i
		
		# constants
		elif isinstance(i, self.lang.Constant):
			return i.eval()
		# a value
		else:
			return i
	
	def eval(self, i, ref=False):
	
		if isinstance(i, self.lang.List):
			for k,v in enumerate(i):
				i[k] = self.eval(v) if ref is True else self.getval(self.eval(v))
			return i
			
		if isinstance(i, list) and len(i) > 0:
		
			# a control struct
			if isinstance(i[OPERAND_L], self.lang.Control):
				return i[OPERAND_L].eval(self, i[1:])
			
			# ignore is read is not enabled
			if not self.is_read_enabled():
				return None
			
			# a keyword
			if isinstance(i[OPERAND_L], self.lang.Keyword):
				return i[OPERAND_L].eval(self, i[1:])
	
			# expressions
			for k,v in enumerate(i):
				if isinstance(v, list):
					i[k] = self.eval(v)
										
			# a value
			if len(i) < 2:
				return i.pop()
			
			# unary operation
			if len(i) < 3:
				return i.pop(0).eval(self.scope(), arguments=i.pop(0), interp=self)
			
			# assign operations
			if isinstance(i[OPERATOR], self.lang.Assign):
				return i[OPERATOR].eval(i[OPERAND_L], self.getval(i[OPERAND_R]), self.scope())
			# any other binary operation
			else:
				return i[OPERATOR].eval(self.getval(i[OPERAND_L]), self.getval(i[OPERAND_R]), self.scope())
				
		else:
			return i
