from dt import *

OPERAND_L	= 0
OPERATOR 	= 1
OPERAND_R	= 2

class Interpreter(object):

	class Memory(object):
		def __init__(self):
			self.stack	= []
			self.heap 	= {}	

	def __init__(self):
		self.parser = Parser(Doubletalk(), 'test.dtk')
		self.lang	= self.parser.lang
		self.memory	= Interpreter.Memory()
			
	def read(self):
		inst = self.parser.parse()
		
		if inst is False:
			return False
		
		tree = self.parser.build(inst)
		

		print tree
		print '-' * 80
		self.eval(tree)

		#print self.memory.heap
		
				
		return tree
	
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
