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

    def get_lookahead(self):
        if self.lookahead_type == 'ID': return 'ID'
        if self.lookahead_type == 'NUM': return 'NUM'
        return self.lookahead


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
        l = self.get_lookahead()
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
        l = self.get_lookahead()
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
        l = self.get_lookahead()
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
        l = self.get_lookahead()
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
        l = self.get_lookahead()
        if l in first['Fun-declaration-prime']:
            self.fun_declaration_prime(self.add_node('Fun-declaration-prime', parent))
        elif l in first['Var-declaration-prime']:
            self.var_declaration_prime(self.add_node('Var-declaration-prime', parent))
        elif l in follow['Declaration-prime']: # Declaration-prime -/-> eps
            print(f'Missing Declaration-prime on line {self.line_number}')  
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.declaration_prime(parent)   

    def fun_declaration_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.params(self.add_node('Params', parent))
            self.match(')', parent)
            self.compound_stmt(self.add_node('Compound-stmt', parent))
        elif l in follow['Fun-declaration-prime']: # Fun-declaration-prime -/-> eps
            print(f'Missing Fun-declaration-prime on line {self.line_number}')  
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.fun_declaration_prime(parent)   


    def var_declaration_prime(self, parent):
        l = self.get_lookahead()
        if l == ';':
            self.match(';', parent)
        elif l == '[':
            self.match('[', parent)
            self.match('NUM', parent)
            self.match(']', parent) 
            self.match(';', parent)
        elif l in follow['Var-declaration-prime']: # Var-declaration-prime -/-> eps
            print(f'Missing Var-declaration-prime on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.var_declaration_prime(parent) 

    def type_specifier(self, parent):
        l = self.get_lookahead()
        if l == 'int':
            self.match('int', parent)
        elif l == 'void':
            self.match('void', parent)
        elif l in follow['Type-specifier']: # Type-specifier -/-> eps
            print(f'Missing Type-specifier on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.type_specifier(parent)  

    def params(self, parent):
        l = self.get_lookahead()
        if l == 'int':          
            self.match('int', parent)
            self.match('ID', parent)
            self.param_prime(self.add_node('Param-prime', parent)) 
            self.param_list(self.add_node('Param-list', parent)) 
        elif l == 'void':
            self.match('void', parent)
            self.param_list_void_abtar(self.add_node('Param-list-void-abtar', parent)) 
        elif l in follow['Params']: # Params -/-> eps
            print(f'Missing Params on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.params(parent) 

    def param_list_void_abtar(self, parent):
        l = self.get_lookahead()
        if l == 'ID':
            self.match('ID', parent)
            self.param_prime(self.add_node('Param-prime', parent))
            self.param_list(self.add_node('Param-list', parent)) 
        elif l in follow['Param-list-void-abtar']: # Param-list-void-abtar -> eps
            return 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.param_list_void_abtar(parent) 

    def param_list(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.param(self.add_node('Param', parent))
            self.param_list(self.add_node('Param-list', parent))
        elif l in follow['Param-list']: # Param-list -> eps
            return 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.param_list(parent) 

    def param(self, parent):
        l = self.get_lookahead()
        if l in first['Declaration-initial']:
            self.declaration_initial(self.add_node('Declaration-initial', parent))
            self.param_prime(self.add_node('Param-prime', parent))
        elif l in follow['Param']:  # Param -/-> eps
            print(f'Missing Param on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.param(parent) 

    def param_prime(self, parent):
        l = self.get_lookahead()
        if l == '[':
            self.match('[', parent)
            self.match(']', parent)
        elif l in follow['Param-prime']: # Param-prime -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.param_prime(parent)

    def compound_stmt(self, parent):
        l = self.get_lookahead()
        if l == '{':
            self.match('{', parent)
            self.declaration_list(self.add_node('Declaration-list', parent))
            self.statement_list(self.add_node('Statement-list', parent))
            self.match('}', parent)
        elif l in follow['Compound-stmt']:  # Compound-stmt -/-> eps
            print(f'Missing Compound-stmt on line {self.line_number}') 

    def statement_list(self, parent):
        l = self.get_lookahead()
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
        l = self.get_lookahead()
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

    def expression_stmt(self, parent):
        l = self.get_lookahead()
        if l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.match(';', parent)
        elif l == 'break':
            self.match('break', parent)
            self.match(';', parent)
        elif l == ';':
            self.match(';', parent)
        elif l in follow['Expression-stmt']:  # Expression-stmt -/-> eps
            print(f'Missing Expression-stmt on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.expression_stmt(parent)
    

    def selection_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'if':
            self.match('if', parent)
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
            self.statement(self.add_node('Statement', parent))
            self.match('else', parent)
            self.statement(self.add_node('Statement', parent))
        elif l in follow['Selection-stmt']: # Selection-stmt -/-> eps
            print(f'Missing Selection-stmt on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.selection_stmt(parent)


    def iteration_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'while':
            self.match('while', parent)
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
            self.statement(self.add_node('Statement', parent))
        elif l in follow['Iteration-stmt']: # Iteration-stmt -/-> eps
            print(f'Missing Iteration-stmt on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.iteration_stmt(parent)

    def return_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'return':
            self.match('return', parent)
            self.return_stmt_prime(self.add_node('Return-stmt-prime', parent))
        elif l in follow['Return-stmt']: # Return-stmt -/-> eps
            print(f'Missing Return-stmt on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.return_stmt(parent) 

    def return_stmt_prime(self, parent):
        l = self.get_lookahead()
        if l == ';':
            self.match(';', parent)
        elif l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.match(';', parent)
        elif l in follow['Return-stmt-prime']: # Return-stmt-prime -/-> eps
            print(f'Missing Return-stmt-prime on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.return_stmt_prime(parent)  

    def for_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'for':
            self.match('for', parent)
            self.match('ID', parent)
            self.match('=', parent)
            self.vars(self.add_node('Vars', parent))
            self.statement(self.add_node('Statement', parent))
        elif l in follow['For-stmt']: # For-stmt -/-> eps
            print(f'Missing For-stmt on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.for_stmt(parent) 

    def vars(self, parent):
        l = self.get_lookahead()
        if l in first['Var']:
            self.var(self.add_node('Var', parent))
            self.var_zegond(self.add_node('Var-zegond', parent))
        elif l in follow['Vars']: # Vars -/-> eps
            print(f'Missing Vars on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.vars(parent) 

    def var_zegond(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.var(self.add_node('Var', parent))
            self.var_zegond(self.add_node('Var-zegond', parent))
        elif l in follow['Var-zegond']: # Var-zegond -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.var_zegond(parent) 

    def var(self, parent):
        l = self.get_lookahead()
        if l == 'ID':
            self.match('ID', parent)
            self.var_prime(self.add_node('Var-prime', parent))
        elif l in follow['Var']: # Var -/-> eps
            print(f'Missing Var on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.var(parent) 

    def expression(self, parent):
        l = self.get_lookahead()
        if l in first['Simple-expression-zegond']:
            self.simple_expression_zegond(self.add_node('Simple-expression-zegond', parent))
        elif l == 'ID':
            self.match('ID', parent)
            self.B(self.add_node('B', parent))
        elif l in follow['Expression']: # Expression -/-> eps
            print(f'Missing Expression on line {self.line_number}')
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.expression(parent) 

    def B(self, parent):
        l = self.get_lookahead()
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
        l = self.get_lookahead()
        if l == '=':
            self.match('=', parent)
            self.expression(self.add_node('Expression', parent))
        elif l in first['G'] + first['D'] + first['C']:
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

    def simple_expression_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Additive-expression-zegond']:
            self.additive_expression_zegond(self.add_node('Additive-expression-zegond', parent))
            self.C(self.add_node('C', parent))
        elif l in follow['Simple-expression-zegond']: # Simple-expression-zegond -/-> eps
            print(f'Missing Simple-expression-zegond on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.simple_expression_zegond(parent)

    def simple_expression_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Additive-expression-prime'] + first['C']:
            self.additive_expression_prime(self.add_node('Additive-expression-prime', parent))
            self.C(self.add_node('C', parent))
        elif l in follow['Simple-expression-prime']: # Additive-expression-prime C -> eps
            self.additive_expression_prime(self.add_node('Additive-expression-prime', parent))
            self.C(self.add_node('C', parent))
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.simple_expression_prime(parent)

    def C(self, parent):
        l = self.get_lookahead()
        if l in first['Relop']:
            self.relop(self.add_node('Relop', parent))
            self.additive_expression(self.add_node('Additive-expression', parent))
        elif l in follow['C']: # C -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.C(parent)

    def relop(self, parent):
        l = self.get_lookahead()
        if l == '<':
            self.match('<', parent)
        elif l == '==':
            self.match('==', parent)
        elif l in follow['Relop']: # Relop -/-> eps
            print(f'Missing Relop on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.relop(parent)

    def additive_expression(self, parent):
        l = self.get_lookahead()
        if l in first['Term']:
            self.term(self.add_node('Term', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['Additive-expression']: # Additive-expression -/-> eps
            print(f'Missing Additive-expression on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.additive_expression(parent)

    def additive_expression_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Term-prime'] + first['D']:
            self.term_prime(self.add_node('Term-prime', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['Additive-expression-prime']: # Term-prime D -> eps
            self.term_prime(self.add_node('Term-prime', parent))
            self.D(self.add_node('D', parent))
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.additive_expression_prime(parent)

    def additive_expression_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Term-zegond']:
            self.term_zegond(self.add_node('Term-zegond', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['Additive-expression-zegond']: # Additive-expression-zegond -/-> eps
            print(f'Missing Additive-expression-zegond on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.additive_expression_zegond(parent)  

    def D(self, parent):
        l = self.get_lookahead()
        if l in first['Addop']:
            self.addop(self.add_node('Addop', parent))
            self.term(self.add_node('Term', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['D']: # D -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.D(parent)

    def addop(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.match('+', parent)
        elif l == '-':
            self.match('-', parent)
        elif l in follow['Addop']: # Addop -/-> eps
            print(f'Missing Addop on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.addop(parent)

    def term(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor']:
            self.signed_factor(self.add_node('Signed-factor', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term']: # Term -/-> eps
            print(f'Missing Term on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.term(parent)

    def term_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor-prime']:
            self.signed_factor_prime(self.add_node('Signed-factor-prime', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term-prime']: # Signed-factor-prime G -> eps
            self.signed_factor_prime(self.add_node('Signed-factor-prime', parent))
            self.G(self.add_node('G', parent))
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.term_prime(parent)

    def term_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor-zegond']:
            self.signed_factor_zegond(self.add_node('Signed-factor-zegond', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term-zegond']: # Term-zegond -/-> eps
            print(f'Missing Term-zegond on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.term_zegond(parent)
    
    def G(self, parent):
        l = self.get_lookahead()
        if l == '*':
            self.match('*', parent)
            self.signed_factor(self.add_node('Signed-factor', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['G']: # G -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.G(parent)

    def signed_factor(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.match('+', parent)
            self.factor(self.add_node('Factor', parent))
        elif l == '-':
            self.match('-', parent)
            self.factor(self.add_node('Factor', parent))
        elif l in first['Factor']:
            self.factor(self.add_node('Factor', parent))
        elif l in follow['Signed-factor']: # Signed-factor -/-> eps
            print(f'Missing Signed-factor on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.signed_factor(parent)

    def signed_factor_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Factor-prime']:
            self.factor_prime(self.add_node('Factor-prime', parent))
        elif l in follow['Signed-factor-prime']: # Factor-prime -> eps
            self.factor_prime(self.add_node('Factor-prime', parent))
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.signed_factor_prime(parent)

    def signed_factor_zegond(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.match('+', parent)
            self.factor(self.add_node('Factor', parent))
        elif l == '-':
            self.match('-', parent)
            self.factor(self.add_node('Factor', parent))
        elif l in first['Factor-zegond']:
            self.factor_zegond(self.add_node('Factor-zegond', parent))
        elif l in follow['Signed-factor-zegond']: # Signed-factor-zegond -/-> eps
            print(f'Missing Signed-factor-zegond on line {self.line_number}') 
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.signed_factor_zegond(parent)  

    def factor(self, parent): 
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
        elif l == 'ID':
            self.match('ID', parent)
            self.var_call_prime(self.add_node('Var-call-prime', parent))
        elif l == 'NUM':
            self.match('NUM', parent)
        elif l in follow['Factor']: # Factor -/-> eps
            print(f'Missing Factor on line {self.line_number}')   
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.factor(parent) 

    def var_call_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.args(self.add_node('Args', parent))
            self.match(')', parent)
        elif l first['Var-prime']:
            self.var_prime(self.add_node('Var-prime', parent))
        elif l in follow['Var-call-prime']: # Var-prime -> eps
            self.var_prime(self.add_node('Var-prime', parent))
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.var_call_prime(parent) 

    def var_prime(self, parent):
        l = self.get_lookahead()
        if l == '[':
            self.match('[', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(']', parent)
        elif l in follow['Var-prime']: # Var-prime -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.var_prime(parent) 

    def factor_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.args(self.add_node('Args', parent))
            self.match(')', parent)
        elif l in follow['Factor-prime']: # Factor-prime -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.factor_prime(parent) 

    def factor_zegond(self, parent):
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
        elif l == 'NUM':
            self.match('NUM', parent)        
        elif l in follow['Factor-zegond']: # Factor-zegond -/-> eps
            print(f'Missing Factor-zegond on line {self.line_number}')  
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.factor_zegond(parent) 

    def args(self, parent):
        l = self.get_lookahead()
        if l in first['Arg-list']:
            self.arg_list(self.add_node('Arg-list', parent))
        elif l in follow['Args']: # Args -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.args(parent) 

    def arg_list(self, parent):
        l = self.get_lookahead()
        if l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.arg_list_prime(self.add_node('Arg-list-prime'))
        elif l in follow['Arg-list']: # Arg-list -/-> eps
            print(f'Missing Arg-list on line {self.line_number}')  
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.arg_list(parent) 

    def arg_list_prime(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.expression(self.add_node('Expression', parent))
            self.arg_list_prime(self.add_node('Arg-list-prime'))
        elif l in follow['Arg-list-prime']: # Arg-list-prime -> eps
            return
        else:
            print(f'Illegal {l} on line {self.line_number}')
            self.get_next_token()
            self.arg_list_prime(parent)