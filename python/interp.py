from dt import *

class Interpreter(object):
	def __init__(self):
		self.parser = Parser(Doubletalk(), 'test.dtk')
		self.lang = self.parser.lang
		self.stack = []
		self.scope = {}
			
	def read(self):
		instr = self.parser.parse()
		
		if instr is False:
			return False
		
		for i in instr:
			self.eval(i)

		return instr
	
	def eval(self, i):
		
		if len(i) > 1:
			print i
		# unary operation
		else:
			pass
		 
		return i
		
