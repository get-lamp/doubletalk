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
		print self.memory.heap
		print '-' * 80
		
		print self.eval(tree)
				
		return tree
	
	def getval(self, i):
			
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
				if isinstance(i[k], list):
					i[k] = self.eval(i[k])
				else:
					i[k] = self.getval(i[k])
			
			print i
			
		else:
			return self.getval(i)
			
					
		"""				
			# operator is really an operator?
			if isinstance(i[OPERATOR], self.lang.Operator):
				if not isinstance(i[OPERATOR], self.lang.Assign):
					i[OPERAND_L] = self.getval(i[OPERAND_L])
						
				return i[OPERATOR].eval(self.eval(i[OPERAND_L]), self.eval(i[OPERAND_R]), self.memory.heap)
				
			else:
				raise Exception('Expecting operator in line %s' % (i[OPERATOR].token.line))
							
		else:
			print i
			return self.getval(i)
		"""
		"""
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
			
				for k,v in enumerate(i):
					if isinstance(i[k], list):
						i[k] = self.eval(i[k])
					elif k == OPERAND_R:
						# only values in right operand
						i[k] = self.getval(i[k])
					
				
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
		 	"""
		return i
		
