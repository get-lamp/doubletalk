from dt import *

class Interpreter(object):
	def __init__(self):
		self.parser = Parser(Doubletalk(), 'test.dtk')
			
	def read(self):
		instr = self.parser.parse()
		return instr
