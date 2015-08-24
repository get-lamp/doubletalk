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
		instr = self.parser.parse()
		
		if instr is False:
			return False
		
		print instr
		print self.memory.heap
		print '-' * 80
		
		for i in instr:
			try:
		
				print self.eval(i)
			
			except Exception as e:
				print e

		return instr
	
	def getval(self, i):
			
		if isinstance(i, self.lang.Identifier):
			return i.eval(self.memory.heap)
		
		return i.eval()
	
	def eval(self, i):
		
		# remove unneded nesting
		# TODO: tiddy up. It shouldn't be necessary to do this
		if len(i) == 1 and isinstance(i, list):
			i = i.pop()
		
		if isinstance(i, list):
		
			if isinstance(i[OPERAND_L], self.lang.Keyword):
				args = self.eval(i[1:].pop())
				return i[OPERAND_L].eval(args)
			# unary operation
			elif len(i) < 3:
				print 'Unary: %s' % (i)
			# ternary operation
			elif not len(i) > 3:
								
				# right operand is an expression? Eval it
				if isinstance(i[OPERAND_R], list):
					i[OPERAND_R] = self.eval(i[OPERAND_R])
				else:
					# only values in right operand
					i[OPERAND_R] = self.getval(i[OPERAND_R])
					
				# operator is really an operator?
				if isinstance(i[OPERATOR], self.lang.Operator):
					if not isinstance(i[OPERATOR], self.lang.Assign):
						i[OPERAND_L] = self.getval(i[OPERAND_L])
						
					return i[OPERATOR].eval(i[OPERAND_L], i[OPERAND_R], self.memory.heap)
				
				#else:
					#raise Exception('Expecting operator in line %s' % (i[OPERATOR].token.line))
				
			# ilegal
			else:
				raise Exception('Illegal statement in line %s' % (i[0].token.line))
		 
		return i
		
