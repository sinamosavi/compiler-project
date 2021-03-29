from scanner import Scanner

if __name__ == '__main__':
	#Sample input from command line: "python compiler.py"
	input = "input.txt"
	scanner = Scanner(input_path = input)
	print("Tokens:")
	scanner.scan(input)