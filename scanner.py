import re
import sys
import string

LETTER = set(string.ascii_letters)
DIGIT = set(string.digits)
WHITE_SPACE = set(string.whitespace)
SYMBOL = {';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<'}
KEYWORDS = {'if', 'else', 'void', 'int', 'while', 'break', 'continue', 'switch', 'default', 'case', 'return'}
VALID_CHARS = LETTER.union(DIGIT).union(WHITE_SPACE).union(SYMBOL)
EOF = '$'

class Scanner:
	def __init__(self, input_path):
		with open(input_path, 'r') as input_file:
			self.lines = input_file.readlines(input_file)

		self.inside_comment = False # Are we inside comment?
		self.pointer = 0	# pointer in current line
		self.line_number = 1
		self.line = self.lines[0] # current line
		self.token = ''
		self.token_type = None
		self.error_msg = ''
		

	def type(self, str):
		if str.isdigit():
			return 'DIGIT'
		elif str == '*':
			return 'STAR'
		elif str in [',', ';', ':', '+', '-', ']', '[', '{', '}', '<', '(', ')']:
			return 'SYMBOL'
		elif str == '=':
			return 'EQUAL'
		elif str.isalpha():
			return 'LETTER'
		elif str == '/':
			return 'COMMENT'
		elif re.match('[ \t]+', str):
			return 'SKIP'
		elif re.match('\n', str):
			return 'NEWLINE'
		elif str in ['', '\r', '\f', '\v']:
			return 'WHITESPACE'
		else:
			return 'ERROR'
		

	def number_state(self): # state 3
		self.token_type = 'NUM'
		other = SYMBOL.union(WHITE_SPACE).union('/')
		self.token = self.line[self.pointer]
		while True:
			self.pointer += 1
			char = self.line[self.pointer]
			if char in DIGIT:	# stay in state 1
				self.token += char
			elif char in other:	# valid NUM token
				return False
			else:	# Invalid number
				self.error_msg = 'Invalid number'
				self.token += char
				self.pointer += 1
				return True # Panic error

	def keyword_id_state(self): # state 1
		other = SYMBOL.union(WHITE_SPACE).union('/')
		self.token = self.line[self.pointer]
		while True:
			self.pointer += 1
			char = self.line[self.pointer]
			if char in DIGIT.union(LETTER):	# stay in state 1
				self.token += char
			elif char in other:	# valid ID/KEYWORD token
				if self.token in KEYWORDS: self.token_type = 'KEYWORD'
				else: self.token_type = 'ID'
				return False
			else: # Invalid input
				self.error_msg = 'Invalid input'
				self.token += char
				self.pointer += 1
				return True # Panic error

	def symbol_state(self): # state 5
		self.token_type = 'SYMBOL'
		self.token = self.line[self.pointer]
		self.pointer += 1
		return False

	def equal_state(self): # state 6
		self.token_type = 'SYMBOL'
		self.pointer += 1
		char = self.line[self.pointer]
		if char == '=': # token '=='
			self.token = '=='
			self.pointer += 1
			return False
		else:	# token '='
			self.token = '='
			return False

	def star_state(self):	# state 8
		self.token_type = 'SYMBOL'
		self.pointer += 1
		char = self.line[self.pointer]
		if char == '/': 	# Unmatched comment
			self.pointer += 1
			self.token = '*/'
			return True 	# Panic error
		else:
			self.token = '*'
			return False

	def comment_state(self):
		return False		

	def whitespace_state(self):   # state f
		self.token_type = 'WHITESPACE'
		self.token = self.line[self.pointer]
		self.pointer += 1
		return False



	def get_next_token(self):
		char = self.line[self.pointer]
		if self.type(char) == 'DIGIT':
			is_error = self.number_state()
		elif self.type(char) == 'LETTER':
			is_error = self.keyword_id_state()
		elif self.type(char) == 'SYMBOL':
			is_error = self.symbol_state()
		elif char == '=':
			is_error = self.equal_state()
		elif char == '*':
			is_error = self.star_state()
		elif char == '/':
			is_error = self.comment_state()
		elif char in WHITE_SPACE:
			is_error = self.whitespace_state()

		return is_error
		
	def scan(self, filename):
		result = []
		out_file = open("tokens.txt", "w")
		while True:
			is_error = self.get_next_token()
			if is_error:
				pass # write (self.line_number, self.token, self.error_msg) in lexical_errors.txt
			else:
				pass # write (self.line_number, self.token, self.token_type)

			self.token = '' # new token started

		# with open(filename) as file:
		# 	for line in file:
		# 		line = ''.join(line + ' ')
		# 		str = []
		# 		for i in range(len(line)):
		# 			letter = line[i]

		# 			letter_type = self.type(letter)

		# 			print(letter + ": " + letter_type)
		# 			old_state = state
		# 			#Go to the new state
		# 			state = old_next_state(old_state, letter)
					
		# 			if(state == old_state):
		# 				pass
		# 			#Write the previous token
		# 			else:
		# 				if(str):
		# 					result.append(''.join(str))
		# 					out_file.write("(" + ''.join(str) + ")")
		# 				str.clear()
		# 			str.append(letter)
				
		# 		#Add endline
		# 		out_file.write('\n')
					
		return result
		
	
	


if __name__ == '__main__':

	#Sample input from command line: "python scanner.py input.txt"
	input = sys.argv[1]	
	scanner = Scanner(input_path=input)
	scanner.scan(input)
	print("\n" + "Tokens:" + "\n")
