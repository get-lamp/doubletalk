from parser import *

OPERAND_L	= 0
OPERATOR 	= 1
OPERAND_R	= 2

class Interpreter(object):

	class Memory(object):
		def __init__(self):
			self.instr 	= []
			self.stack	= []
			self.heap 	= {}	

	def __init__(self):
		self.parser 	= Parser(Doubletalk(), 'test.dtk')
		self.lang		= self.parser.lang
		self.memory		= Interpreter.Memory()
		self.ctrl_stack	= [True]
		self.pntr 		= 0

	def load(self):
	
		while True:
			instr = self.parser.parse()
			
			if instr is False or instr is None:
				return False

			#build grammar tree
			gtree = self.parser.build(instr)
			
			# append to instruction memory block
			self.memory.instr.append(gtree)
		
	def execute(self):

		try:
			# debugging
			print 'Heap %s %s' % ('\t'*2, self.memory.heap)
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

	def getval(self, i, **kwargs):

		if isinstance(i, self.lang.Identifier):
			return i.eval(self.memory.heap)
		elif isinstance(i, self.lang.Constant):
			return i.eval()
		else:
			return i
	
	def goto(self, n):
		self.pntr = n;
		
	def stack(self):
		return self.memory.stack[-1]
	
	def stack_push(self, v):
		self.memory.stack.append(v)
	
	def stack_pull(self):
		return self.memory.stack.pop()
	
	def is_read_enabled(self):
		return self.ctrl_stack[-1]
	
	def toggle_read_enabled(self):
		self.ctrl_stack[-1] = not self.ctrl_stack[-1]
		
	def push_read_enabled(self, boolean):
		self.ctrl_stack.append(boolean)
	
	def pull_read_enabled(self):
		return self.ctrl_stack.pop()
	
	def eval(self, i):
	
		if isinstance(i, list):
			
			
			# a control struct
			if isinstance(i[OPERAND_L], self.lang.Control):
				return i[OPERAND_L].eval(self, i[1:])
		
			if not self.is_read_enabled():
				return None
			
			# a keyword
			if isinstance(i[OPERAND_L], self.lang.Keyword):
				return i[OPERAND_L].eval(self, i[1:])
	
			for k,v in enumerate(i):
				if isinstance(v, list):
					i[k] = self.eval(v)
										
			# a value
			if len(i) < 2:
				return i.pop()
			
			# a binary operation
			if isinstance(i[OPERATOR], self.lang.Assign):
				return i[OPERATOR].eval(i[OPERAND_L], self.getval(i[OPERAND_R]), self.memory.heap)
			else:
				return i[OPERATOR].eval(self.getval(i[OPERAND_L]), self.getval(i[OPERAND_R]), self.memory.heap)
				
		else:
			return i
