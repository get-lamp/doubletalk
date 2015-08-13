class GrammarTree(object):
	def __init__(self, syntax={}):
		self.syntax 	= syntax
		self.route 		= [self.syntax]
		self.sentence 	= [] 

	def _up(self):
		pass

	def _down(self):
		pass

	def hint(self, sentence):
		for s in sentence:
			if s in self.syntax:
				print s

	def push(self, word):
		print word
		branch = self.route[-1]

		if word in branch:
			self.sentence.append(word)
				
			if callable(branch[word]):
				branch[word] = branch[word]()

			self.route.append(branch[word])

	def last(self):
		pass

	def get(self):
		return self.sentence;

	def __len__(self):
		return len(sentence)

	def clear(self):
		pass