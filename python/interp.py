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
		self.parser = Parser(Doubletalk(), 'test.dtk')
		self.lang	= self.parser.lang
		self.memory	= Interpreter.Memory()
		self.pntr 	= 0

	def load(self):
		while True:
			instr = self.parser.parse()
		
			if instr is False:
				return False

			gtree = self.parser.build(instr)
			
			# append to instruction memory block
			self.memory.instr.append(gtree)
			
	def read(self):

		try:
			print '%s: %s' % (self.pntr, self.memory.instr[self.pntr])
			

			#r = self.eval(self.memory.instr[self.pntr])
		

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
	
	def eval(self, i):
	
		if isinstance(i, list):
			
			if len(i) > 3:
				raise Exception('Illegal statement in line %s' % (i[0].token.line))
				
			for k,v in enumerate(i):
				if isinstance(v, list):
					i[k] = self.eval(v)
					
			# a keyword
			if isinstance(i[OPERAND_L], self.lang.Keyword):
				i[OPERAND_L].eval(self)
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
