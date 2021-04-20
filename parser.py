from anytree import Node, RenderTree
from first_and_follows import first, follow
from scanner import Scanner

class Parser:
    def __init__(self, input_path):
        self.scanner = Scanner(input_path)
        self.lookahead = ''
        self.lookahead_type = ''
        self.line_number = 0
        self.tree = Node('Program')
        self.tree_file = open("parse_tree.txt", "w")
        self.error_file = open("syntax_errors.txt", "w")

    def add_node(self, token, parent, type=None):
        if type is not None:
            return Node(f'({type}, {token})', parent)
        else:
            return Node(token, parent)

    def get_next_token(self):
        is_error = True
        while True:
            is_error = self.scanner.get_next_token()
            if not is_error and self.scanner.token_type not in ['WHITESPACE', 'COMMENT']:
                self.lookahead = self.scanner.token
                self.lookahead_type = self.scanner.token_type
                self.line_number = self.scanner.line_number
                break

    def parse(self):
        self.get_next_token()
        if self.lookahead == '$': return


    def match(self, expected_token, parent):
        matched = False
        if expected_token == 'NUM':
            if self.lookahead_type == 'NUM': matched = True
        elif expected_token == 'ID':
            if self.lookahead_type == 'ID': matched = True
        elif self.lookahead == expected_token:
            matched = True

        if matched:
            self.add_node(self.lookahead, parent, self.lookahead_type)
            self.get_next_token()
        else:
            print(f'Missing {expected_token} on line {self.line_number}')

    def program(self, parent):
        l = self.lookahead
        if l in first['Declaration-list']:
            self.declaration_list(self.add_node('Declaration-list', parent))
            self.match('$', parent)
        elif l in follow['Program']:
            print(f'Missing Statement on line {self.line_number}')  # Program -/-> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.program(parent)

    def declaration_list(self, parent):
        l = self.lookahead
        if l in first['Declaration']:
            self.declaration(self.add_node('Declaration', parent))
            self.declaration_list(self.add_node('Declaration-list', parent))
        elif l in follow['Declaration-list']:
            return  # Declaration-list -> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.declaration_list(parent)

    def declaration(self, parent):
        l = self.lookahead
        if l in first['Declaration-initial']:
            self.declaration_initial(self.add_node('Declaration-initial', parent))
            self.declaration_prime(self.add_node('Declaration-prime', parent))
        elif l in follow['Declaration']:
            print(f'Missing Declaration on line {self.line_number}')  # Declaration -/-> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.declaration(parent)

    def declaration_initial(self, parent):
        l = self.lookahead
        if l in first['Type-specifier']:
            self.type_specifier(self.add_node('Type-specifier', parent))
            self.match('ID', parent)
        elif l in follow['Declaration-initial']:
            print(f'Missing Declaration-initial on line {self.line_number}')  # Declaration-initial -/-> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.declaration_initial(parent)
    
    def declaration_prime(self, parent):
        l = self.lookahead
        if l in first['Fun-declaration-prime']:
            self.fun_declaration_prime(self.add_node('Fun-declaration-prime', parent))
        elif l in first['Var-declaration-prime']:
            self.var_declaration_prime(self.add_node('Var-declaration-prime', parent))
        elif l in follow['Declaration-prime']:
            print(f'Missing Declaration-prime on line {self.line_number}')  # Declaration-prime -/-> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.declaration_prime(parent)   

    def fun_declaration_prime(self, parent):
        pass

    def var_declaration_prime(self, parent):
        pass        

    def type_specifier(self, parent):
        pass

    def statement_list(self, parent):
        l = self.lookahead
        if l in first['Statement']:
            self.statement(self.add_node('Statement', parent))
            self.statement_list(self.add_node('Statement-list', parent))
        elif l in follow['Statement-list']:
            return  # Statement-list -> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.statement_list(parent)
        

    def statement(self, parent):
        l = self.lookahead
        if l in first['Expression-stmt']:
            self.expression_stmt(self.add_node('Expression-stmt', parent))
        elif l in first['Compound-stmt']:
            self.compound_stmt(self.add_node('Compound-stmt', parent))
        elif l in first['Selection-stmt']:
            self.selection_stmt(self.add_node('Selection-stmt', parent))
        elif l in first['Iteration-stmt']:
            self.iteration_stmt(self.add_node('Iteration-stmt', parent))
        elif l in first['Return-stmt']:
            self.return_stmt(self.add_node('Return-stmt', parent))
        elif l in first['For-stmt']:
            self.for_stmt(self.add_node('For-stmt', parent))
        elif l in follow['Statement']:
            print(f'Missing Statement on line {self.line_number}')  # Statement -/-> eps
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.statement(parent)

    def B(self, parent):
        l = self.lookahead
        if l == '=':
            self.match('=', parent)
            self.expression(self.add_node('Expression', parent))
        elif l == '[':
            self.match('[', parent)
            self.expression(self.add_node('Expression', parent))
            self.match('[', parent)
            self.H(self.add_node('H', parent))
        elif l in first['Simple-expression-prime']:
            self.simple_expression_prime(self.add_node('Simple-expression-prime', parent))
        elif l in follow['B']: # Simple-expression-prime -> eps
            self.simple_expression_prime(self.add_node('Simple-expression-prime', parent))  
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.B(parent)

    def H(self, parent):
        l = self.lookahead
        if l == '=':
            self.match('=', parent)
            self.expression(self.add_node('Expression', parent))
        elif l in first['G']:
            self.G(self.add_node('G', parent))
            self.D(self.add_node('D', parent))
            self.C(self.add_node('C', parent))
        elif l in follow['H']: # G D C -> eps
            self.G(self.add_node('G', parent))
            self.D(self.add_node('D', parent))
            self.C(self.add_node('C', parent)) 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.H(parent)


    def G(self, parent):
        pass

    def D(self, parent):
        pass

    def C(self, parent):
        pass

    def expression_stmt(self, parent):
        pass

    def compound_stmt(self, parent):
        pass

    def selection_stmt(self, parent):
        pass

    def iteration_stmt(self, parent):
        pass

    def return_stmt(self, parent):
        pass

    def for_stmt(self, parent):
        pass

    def expression(self, parent):
        pass

    def simple_expression_prime(self, parent):
        pass
