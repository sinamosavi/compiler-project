# Authors:
# Ainaz Eftekhar 96105564
# Sina Mousavi 95109553

s1 = {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}
s2 = {'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'}
LETTER = s1.union(s2)
DIGIT = {'7', '9', '2', '4', '3', '5', '8', '1', '0', '6'}
WHITE_SPACE = {' ', '\r', '\f', '\v', '\n', '\t'}
SYMBOL = {';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<'}
KEYWORDS = {'if', 'else', 'void', 'int', 'while', 'break', 'switch', 'default', 'case', 'return', 'for'}
KEYWORDS_list = ['if', 'else', 'void', 'int', 'while', 'break', 'switch', 'default', 'case', 'return', 'for']

VALID_CHARS = LETTER.union(DIGIT).union(WHITE_SPACE).union(SYMBOL)
EOF = '$'

class Scanner:
	def __init__(self, input_path):
		with open(input_path, 'r', encoding='utf-8-sig') as input_file:
			self.lines = input_file.readlines()

		self.pointer = 0 # Pointer in current line
		self.line_number = 0
		self.comment_start_line_number = 0
		self.line = self.lines[0] # Current line
		self.token = ''
		self.token_type = None
		self.error_msg = ''
		self.identifiers = []
		self.tokens_file = open("tokens.txt", "w")
		self.error_file = open("lexical_errors.txt", "w")
		self.symbol_file = open("symbol_table.txt", "w")


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
		elif str in [' ', '\r', '\f', '\v', '\t']:
			return 'WHITESPACE'
		else:
			return 'ERROR'

	def read_next_pointer(self):
		self.pointer += 1
		char = self.line[self.pointer]
		return char

	def number_state(self): # State 3
		self.token_type = 'NUM'
		other = SYMBOL.union(WHITE_SPACE).union('/')
		self.token = self.line[self.pointer]
		while True:
			char = self.read_next_pointer()
			if char in DIGIT:	# Stay in state 1
				self.token += char
			elif char in other:	# Valid NUM token
				return False
			else:	# Invalid number
				self.error_msg = 'Invalid number'
				self.token += char
				self.pointer += 1
				return True # Panic error

	def keyword_id_state(self): # State 1
		other = SYMBOL.union(WHITE_SPACE).union('/')
		self.token = self.line[self.pointer]
		while True:
			char = self.read_next_pointer()
			if char in DIGIT.union(LETTER):	# Stay in state 1
				self.token += char
			elif char in other:	# Valid ID/KEYWORD token
				if self.token in KEYWORDS: 
					self.token_type = 'KEYWORD'
				else: 
					self.token_type = 'ID'
					if self.token not in self.identifiers:
						self.identifiers.append(self.token)
				return False
			else: # Invalid input
				self.error_msg = 'Invalid input'
				self.token += char
				self.pointer += 1
				return True # Panic error

	def symbol_state(self): # State 5
		self.token_type = 'SYMBOL'
		self.token = self.line[self.pointer]
		self.pointer += 1
		return False

	def equal_state(self): # State 6
		self.token_type = 'SYMBOL'
		char = self.read_next_pointer()
		if char == '=': # token '=='
			self.token = '=='
			self.pointer += 1
			return False
		elif char in VALID_CHARS:	# token '='
			self.token = '='
			return False
		else:
			self.error_msg = 'Invalid input'
			self.token = '='
			self.token += char
			self.pointer += 1
			return True # Panic error


	def star_state(self):	# State 8
		self.token_type = 'SYMBOL'
		char = self.read_next_pointer()
		if char == '/': 	
			self.pointer += 1
			self.token = '*/'
			self.error_msg = 'Unmatched comment'
			return True 	# Panic error
		elif char in VALID_CHARS:
			self.token = '*'
			return False
		else:
			self.error_msg = 'Invalid input'
			self.token = '*'
			self.token += char
			self.pointer += 1
			return True # Panic error

	def comment_state(self):	# State a
		self.token_type = 'COMMENT'
		char = self.read_next_pointer()
		if char == '/':
			return self.comment_line_state()
		elif char == '*':
			return self.comment_paragraph_state()
		else:
			self.error_msg = 'Invalid input'
			self.token = '/'
			# This line created a bug with in Test 12
			#self.pointer += 1
			return True # Panic error

	def comment_line_state(self):	# State b
		char = self.read_next_pointer()
		while char != '\n':	# Read to the end of the current line
			self.pointer += 1
			if self.pointer >= len(self.line): break
			char = self.line[self.pointer]
		return False	

	def comment_paragraph_state(self):	# State d
		self.pointer += 1
		self.token = '/*'
		state = 'd'
		self.comment_start_line_number = self.line_number
		while True:
			if(self.pointer >= len(self.line)): # Go to next line
				self.line_number += 1
				if self.line_number >= len(self.lines):		# End of the code
					self.error_msg = 'Unclosed comment'
					if(len(self.token) > 7):
						self.token = f'{self.token[:7]}...'
					return True # Panic error

				self.line = self.lines[self.line_number]
				self.pointer = 0

			while state == 'd' and self.pointer < len(self.line): 
				# Stay in state d
				char = self.line[self.pointer]
				self.token += char
				self.pointer += 1
				if char == '*': state = 'e'

			while state == 'e' and self.pointer < len(self.line):

				# Stay in state e
				char = self.line[self.pointer]
				self.token += char
				self.pointer += 1
				if char not in ['*', '/']: 
					state = 'd'
				elif char == '/': 
					return False # State 'c', end of comment paragraph


	def whitespace_state(self):   # State f
		self.token_type = 'WHITESPACE'
		self.token = self.line[self.pointer]
		self.pointer += 1
		return False

	def get_next_token(self):
			
		char = self.line[self.pointer]
		#print("At character: " + char)
		if self.type(char) == 'DIGIT':
			is_error = self.number_state()
		elif self.type(char) == 'LETTER':
			is_error = self.keyword_id_state()
		elif char == '=':
			is_error = self.equal_state()
		elif char == '*':
			is_error = self.star_state()
		elif char == '/':
			is_error = self.comment_state()
		elif char in WHITE_SPACE:
			is_error = self.whitespace_state()
		elif self.type(char) == 'SYMBOL':
			is_error = self.symbol_state()
		else:
			self.pointer += 1
			self.error_msg = 'Invalid input'
			self.token = char
			is_error = True

		return is_error
		
	def scan(self, filename):
		result = []
		old_line_number_token = -1
		old_line_number_error = -1
		while True:
			if(self.pointer >= len(self.line)):
				# Go to the next line 
				self.line_number += 1
				if self.line_number >= len(self.lines):		# End of the code
					break
				self.line = self.lines[self.line_number]
				self.pointer = 0
				self.token = ''

			is_error = self.get_next_token()
			if is_error:
				if self.error_msg == 'Unclosed comment':
					line_number = self.comment_start_line_number
				else:
					line_number = self.line_number
				if(old_line_number_error != self.line_number):
					if(old_line_number_error != -1):
						self.error_file.write("\n")
					self.error_file.write(str(line_number + 1) + ".\t")
					old_line_number_error = line_number
				else:
					self.error_file.write(" ")
				# Writes the error into lexical_errors.txt
				self.error_file.write("(" + self.token + ", " + self.error_msg + ")")
			else:
				if(self.token_type not in ['WHITESPACE', 'COMMENT']):
					# Will write line number only if we recently switched lines
					if(old_line_number_token != self.line_number):
						if(old_line_number_token != -1):
							self.tokens_file.write("\n")
						self.tokens_file.write(str(self.line_number + 1) + ".\t")
						old_line_number_token = self.line_number
					else:
						self.tokens_file.write(" ")
					# Writes the token into tokens.txt
					self.tokens_file.write("(" + self.token_type + ", " + self.token + ")")

		symbol_number = 1
		for keyword in list(KEYWORDS_list):
			self.symbol_file.write(str(symbol_number) + ".\t" + keyword + "\n")
			symbol_number += 1
		for id in self.identifiers:
			self.symbol_file.write(str(symbol_number) + ".\t" + id + "\n")
			symbol_number += 1
			
		self.token = '' # New token started

		if old_line_number_error == -1:
			self.error_file.write("There is no lexical error.")	
		return result
