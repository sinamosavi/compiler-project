# Authors:
# Ainaz Eftekhar 96105564
# Sina Mousavi 95109553

from scanner import Scanner
from parser import Parser

if __name__ == '__main__':
	#Sample input from command line: "python compiler.py"
	input = "input.txt"

	# scanner = Scanner(input_path = input)
	# scanner.scan(input)

	parser = Parser(input_path=input)
	parser.parse()
	parser.print_parse_tree()
	if not parser.error:
		parser.error_file.write('There is no syntax error.') 