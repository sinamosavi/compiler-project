import re
import sys

keywords = {'if', 'else', 'void', 'int', 'while', 'break', 'continue', 'switch', 'default', 'case', 'return'}
dfa = {('start', 'DIGIT'): 'number',
	   ('start', 'LETTER'): 'letter',
	   ('start', 'NEWLINE'): 'start',
	   ('start', 'SKIP'): 'start',
	   ('number', 'DIGIT'): 'number',
	   ('number', 'LETTER'): 'letter',
	   ('number', 'NEWLINE'): 'start',
	   ('number', 'SKIP'): 'start',
	   ('letter', 'DIGIT'): 'number',
	   ('letter', 'LETTER'): 'letter',
	   ('letter', 'NEWLINE'): 'start',
	   ('letter', 'SKIP'): 'start'
	  }

def type(str):
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
		
def old_next_state(state, char):
	return dfa[state, type(char)]
	
def next_state(state, char):
	#Todo
	pass
	
		
def scan(filename):
	result = []
	state = 'start'
	out_file = open("tokens.txt", "w")
	with open(filename) as file:
		for line in file:
			line = ''.join(line + ' ')
			str = []
			for i in range(len(line)):
				letter = line[i]
				letter_type = type(letter)
				print(letter + ": " + letter_type)
				old_state = state
				#Go to the new state
				state = old_next_state(old_state, letter)
				
				if(state == old_state):
					pass
				#Write the previous token
				else:
					if(str):
						result.append(''.join(str))
						out_file.write("(" + ''.join(str) + ")")
					str.clear()
				str.append(letter)
			
			#Add endline
			out_file.write('\n')
				
	return result
	
#Sample input from command line: "python scanner.py input.txt"
input = sys.argv[1]	
list_scan = iter(scan(input))
	
def get_next_token():
    try:
        return next(list_scan)
    except StopIteration:
        return None

print("\n" + "Tokens:" + "\n")
while(True):
	s = get_next_token()
	if(s != None):
		print(s)
	else:
		exit()