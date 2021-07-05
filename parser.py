from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from first_and_follows import first, follow
from scanner import Scanner
from semantics import Semantics

class Parser:
    def __init__(self, input_path):
        self.scanner = Scanner(input_path)
        self.lookahead = ''
        self.lookahead_type = ''
        self.error = False
        self.line_number = 0
        self.tree = Node('Program')
        self.tree_file = open("parse_tree.txt", "w", encoding='utf-8-sig')
        self.error_file = open("syntax_errors.txt", "w")
        self.semantics = Semantics()
        
        self.last_match = None
	
    def print_error(self, text):
        self.error = True
        # print(text)
        #t1 = re.sub(r' on line \d+$', '', text)
        t1 = text
        t2 = t1[0].lower() + t1[1:]
        self.error_file.write(f'#{self.line_number + 1} : syntax error, {t2}\n')

    def print_parse_tree(self):
        for row in RenderTree(self.tree):
            # print("%s%s" % (row.pre, row.node.name))
            self.tree_file.write("%s%s\n" % (row.pre, row.node.name))

    def terminate(self, parent):
        parent.parent = None
        self.print_parse_tree()
        self.print_error('unexpected EOF')
        exit(0)
	
    def add_node(self, token, parent, type=None):
        if type is not None:
            return Node(f'({type}, {token}) ', parent)
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
        #print(f'First Token {self.lookahead}')
        self.program(self.tree)
        if self.lookahead == '$':
            self.semantics.save_pb()
            return

    def get_lookahead(self):
        if self.lookahead_type == 'ID': return 'ID'
        if self.lookahead_type == 'NUM': return 'NUM'
        return self.lookahead


    def match(self, expected_token, parent):
        #print(f'Matching {self.lookahead} with {expected_token}')
        matched = False
        if expected_token == 'NUM':
            if self.lookahead_type == 'NUM': matched = True
        elif expected_token == 'ID':
            if self.lookahead_type == 'ID': matched = True
        elif self.lookahead == expected_token:
            matched = True

        if matched:
            if expected_token == '$':
                self.add_node(self.lookahead, parent)
            else:
                self.last_match = f'{self.lookahead}'
                self.add_node(self.lookahead, parent, self.lookahead_type)
                self.get_next_token()
        else:
            self.print_error(f'Missing {expected_token}')

    def program(self, parent):
        l = self.get_lookahead()
        if l in first['Declaration-list']:
            self.declaration_list(self.add_node('Declaration-list', parent))
            self.match('$', parent)
        elif l in follow['Program']:
            parent.parent = None
            self.print_error(f'Missing Program')  # Program -/-> eps
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.program(parent)

    def declaration_list(self, parent):
        l = self.get_lookahead()
        if l in first['Declaration']:
            self.declaration(self.add_node('Declaration', parent))
            self.declaration_list(self.add_node('Declaration-list', parent))
        elif l in follow['Declaration-list']:
            self.add_node('epsilon', parent)
            return  # Declaration-list -> eps
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.declaration_list(parent)

    def declaration(self, parent):
        l = self.get_lookahead()
        if l in first['Declaration-initial']:
            self.declaration_initial(self.add_node('Declaration-initial', parent))
            self.declaration_prime(self.add_node('Declaration-prime', parent))
        elif l in follow['Declaration']:
            parent.parent = None
            self.print_error(f'Missing Declaration')  # Declaration -/-> eps
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.declaration(parent)

    def declaration_initial(self, parent):
        l = self.get_lookahead()
        if l in first['Type-specifier']:
            self.type_specifier(self.add_node('Type-specifier', parent))
            self.semantics.code_gen("#define_id", self.lookahead)
            self.match('ID', parent)
        elif l in follow['Declaration-initial']:
            parent.parent = None
            self.print_error(f'Missing Declaration-initial')  # Declaration-initial -/-> eps
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.declaration_initial(parent)
    
    def declaration_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Fun-declaration-prime']:
            self.fun_declaration_prime(self.add_node('Fun-declaration-prime', parent))
        elif l in first['Var-declaration-prime']:
            self.var_declaration_prime(self.add_node('Var-declaration-prime', parent))
        elif l in follow['Declaration-prime']: # Declaration-prime -/-> eps
            parent.parent = None
            self.print_error(f'Missing Declaration-prime')  
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.declaration_prime(parent)   

    def fun_declaration_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            func_name = self.last_match
            self.semantics.code_gen("#func_def_start", func_name)
            self.match('(', parent)
            self.params(self.add_node('Params', parent))
            self.match(')', parent)
            self.semantics.code_gen("#label_func", func_name)
            self.compound_stmt(self.add_node('Compound-stmt', parent))
            self.semantics.code_gen("#func_def_end", func_name)
        elif l in follow['Fun-declaration-prime']: # Fun-declaration-prime -/-> eps
            parent.parent = None
            self.print_error(f'Missing Fun-declaration-prime')  
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.fun_declaration_prime(parent)   


    def var_declaration_prime(self, parent):
        l = self.get_lookahead()
        if l == ';':
            self.match(';', parent)
            self.semantics.code_gen("#pop")
        elif l == '[':
            self.match('[', parent)
            self.semantics.code_gen("#pnum", self.lookahead)
            self.match('NUM', parent)
            self.match(']', parent)
            self.semantics.code_gen("#declare_array")    
            self.match(';', parent)
        elif l in follow['Var-declaration-prime']: # Var-declaration-prime -/-> eps
            parent.parent = None
            self.print_error(f'Missing Var-declaration-prime') 
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.var_declaration_prime(parent) 

    def type_specifier(self, parent):
        l = self.get_lookahead()
        if l == 'int':
            self.match('int', parent)
        elif l == 'void':
            self.match('void', parent)
        elif l in follow['Type-specifier']: # Type-specifier -/-> eps
            parent.parent = None
            self.print_error(f'Missing Type-specifier') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.type_specifier(parent)  

    def params(self, parent):
        l = self.get_lookahead()
        if l == 'int':          
            self.match('int', parent)
            self.semantics.code_gen("#define_id", self.lookahead)
            self.match('ID', parent)
            self.param_prime(self.add_node('Param-prime', parent)) 
            self.param_list(self.add_node('Param-list', parent)) 
        elif l == 'void':
            self.match('void', parent)
            self.param_list_void_abtar(self.add_node('Param-list-void-abtar', parent)) 
        elif l in follow['Params']: # Params -/-> eps
            parent.parent = None
            self.print_error(f'Missing Params') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.params(parent) 

    def param_list_void_abtar(self, parent):
        l = self.get_lookahead()
        if l == 'ID':
            self.semantics.code_gen("#pid", self.lookahead)
            self.match('ID', parent)
            self.param_prime(self.add_node('Param-prime', parent))
            self.param_list(self.add_node('Param-list', parent)) 
        elif l in follow['Param-list-void-abtar']: # Param-list-void-abtar -> eps
            self.add_node('epsilon', parent)
            return 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.param_list_void_abtar(parent) 

    def param_list(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.param(self.add_node('Param', parent))
            self.param_list(self.add_node('Param-list', parent))
        elif l in follow['Param-list']: # Param-list -> eps
            self.add_node('epsilon', parent)
            return 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.param_list(parent) 

    def param(self, parent):
        l = self.get_lookahead()
        if l in first['Declaration-initial']:
            self.declaration_initial(self.add_node('Declaration-initial', parent))
            self.param_prime(self.add_node('Param-prime', parent))
        elif l in follow['Param']:  # Param -/-> eps
            parent.parent = None
            self.print_error(f'Missing Param') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.param(parent) 

    def param_prime(self, parent):
        l = self.get_lookahead()
        if l == '[':
            self.match('[', parent)
            self.match(']', parent)
            self.semantics.code_gen("#arr_param")
        elif l in follow['Param-prime']: # Param-prime -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
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
            parent.parent = None
            self.print_error(f'Missing Compound-stmt') 
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.param_prime(parent)

    def statement_list(self, parent):
        l = self.get_lookahead()
        if l in first['Statement']:
            self.statement(self.add_node('Statement', parent))
            self.statement_list(self.add_node('Statement-list', parent))
        elif l in follow['Statement-list']:
            self.add_node('epsilon', parent)
            return  # Statement-list -> eps
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
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
            parent.parent = None
            self.print_error(f'Missing Statement')  # Statement -/-> eps
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.statement(parent)

    def expression_stmt(self, parent):
        l = self.get_lookahead()
        if l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.match(';', parent)
            self.semantics.code_gen("#pop")
        elif l == 'break':
            self.semantics.code_gen("#break")
            self.match('break', parent)
            self.match(';', parent)
        elif l == ';':
            self.match(';', parent)
        elif l in follow['Expression-stmt']:  # Expression-stmt -/-> eps
            parent.parent = None
            self.print_error(f'Missing Expression-stmt') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.expression_stmt(parent)
    

    def selection_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'if':
            self.match('if', parent)
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
            self.semantics.code_gen("#save")
            self.statement(self.add_node('Statement', parent))
            self.match('else', parent)
            self.semantics.code_gen("#cond_jump")
            self.statement(self.add_node('Statement', parent))
            self.semantics.code_gen("#jump")
        elif l in follow['Selection-stmt']: # Selection-stmt -/-> eps
            parent.parent = None
            self.print_error(f'Missing Selection-stmt') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.selection_stmt(parent)


    def iteration_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'while':
            self.semantics.code_gen("#break_save")
            self.match('while', parent)
            self.match('(', parent)
            self.semantics.code_gen("#label")
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
            self.semantics.code_gen("#save")
            self.statement(self.add_node('Statement', parent))
            self.semantics.code_gen("#while", self.lookahead)
        elif l in follow['Iteration-stmt']: # Iteration-stmt -/-> eps
            parent.parent = None
            self.print_error(f'Missing Iteration-stmt') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.iteration_stmt(parent)

    def return_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'return':
            self.match('return', parent)
            self.return_stmt_prime(self.add_node('Return-stmt-prime', parent))
            self.semantics.code_gen("#return", self.lookahead)
        elif l in follow['Return-stmt']: # Return-stmt -/-> eps
            parent.parent = None
            self.print_error(f'Missing Return-stmt')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.return_stmt(parent) 

    def return_stmt_prime(self, parent):
        l = self.get_lookahead()
        if l == ';':
            self.match(';', parent)
            self.semantics.code_gen("#return_void")
        elif l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.match(';', parent)
        elif l in follow['Return-stmt-prime']: # Return-stmt-prime -/-> eps
            parent.parent = None
            self.print_error(f'Missing Return-stmt-prime')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.return_stmt_prime(parent)  

    def for_stmt(self, parent):
        l = self.get_lookahead()
        if l == 'for':
            self.semantics.code_gen("#break_save")
            self.match('for', parent)
            self.semantics.code_gen("#pid", self.lookahead)
            self.match('ID', parent)
            self.match('=', parent)
            self.vars(self.add_node('Vars', parent))
            self.semantics.code_gen("#label_for")
            self.semantics.code_gen("#assign_vars")
            self.statement(self.add_node('Statement', parent))
            self.semantics.code_gen("#jpf_for")

        elif l in follow['For-stmt']: # For-stmt -/-> eps
            parent.parent = None
            self.print_error(f'Missing For-stmt')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.for_stmt(parent) 

    def vars(self, parent):
        l = self.get_lookahead()
        if l in first['Var']:
            self.var(self.add_node('Var', parent))
            self.semantics.code_gen("#vars_begin")
            self.var_zegond(self.add_node('Var-zegond', parent))
        elif l in follow['Vars']: # Vars -/-> eps
            parent.parent = None
            self.print_error(f'Missing Vars')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.vars(parent) 

    def var_zegond(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.var(self.add_node('Var', parent))
            self.semantics.code_gen("#var_zegond")
            self.var_zegond(self.add_node('Var-zegond', parent))
        elif l in follow['Var-zegond']: # Var-zegond -> eps
            self.semantics.code_gen("#vars_end")
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.var_zegond(parent) 

    def var(self, parent):
        l = self.get_lookahead()
        if l == 'ID':
            self.semantics.code_gen("#pid", self.lookahead)
            self.match('ID', parent)
            self.var_prime(self.add_node('Var-prime', parent))
        elif l in follow['Var']: # Var -/-> eps
            parent.parent = None
            self.print_error(f'Missing Var')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.var(parent) 

    def expression(self, parent):
        l = self.get_lookahead()
        if l in first['Simple-expression-zegond']:
            self.simple_expression_zegond(self.add_node('Simple-expression-zegond', parent))
        elif l == 'ID':
            self.semantics.code_gen("#pid", self.lookahead)
            self.match('ID', parent)
            self.B(self.add_node('B', parent))
        elif l in follow['Expression']: # Expression -/-> eps
            parent.parent = None
            self.print_error(f'Missing Expression')
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.expression(parent) 

    def B(self, parent):
        l = self.get_lookahead()
        if l == '=':
            self.match('=', parent)
            self.expression(self.add_node('Expression', parent))
            self.semantics.code_gen("#assign")
        elif l == '[':
            self.match('[', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(']', parent)
            self.semantics.code_gen("#arr_element", self.lookahead)
            self.H(self.add_node('H', parent))
        elif l in first['Simple-expression-prime']:
            self.simple_expression_prime(self.add_node('Simple-expression-prime', parent))
        elif l in follow['B']: # Simple-expression-prime -> eps
            self.simple_expression_prime(self.add_node('Simple-expression-prime', parent))  
        elif l == '$':
            self.terminate(parent)       
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.B(parent)

    def H(self, parent):
        l = self.get_lookahead()
        if l == '=':
            self.match('=', parent)
            self.expression(self.add_node('Expression', parent))
            self.semantics.code_gen("#assign")
        elif l in first['G'] + first['D'] + first['C']:
            self.G(self.add_node('G', parent))
            self.D(self.add_node('D', parent))
            self.C(self.add_node('C', parent))
        elif l in follow['H']: # G D C -> eps
            self.G(self.add_node('G', parent))
            self.D(self.add_node('D', parent))
            self.C(self.add_node('C', parent)) 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.H(parent)

    def simple_expression_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Additive-expression-zegond']:
            self.additive_expression_zegond(self.add_node('Additive-expression-zegond', parent))
            self.C(self.add_node('C', parent))
        elif l in follow['Simple-expression-zegond']: # Simple-expression-zegond -/-> eps
            parent.parent = None
            self.print_error(f'Missing Simple-expression-zegond') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
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
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.simple_expression_prime(parent)

    def C(self, parent):
        l = self.get_lookahead()
        if l in first['Relop']:
            self.relop(self.add_node('Relop', parent))
            self.additive_expression(self.add_node('Additive-expression', parent))
            self.semantics.code_gen("#arithmetic_op")
        elif l in follow['C']: # C -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.C(parent)

    def relop(self, parent):
        l = self.get_lookahead()
        if l == '<':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('<', parent)
        elif l == '==':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('==', parent)
        elif l in follow['Relop']: # Relop -/-> eps
            parent.parent = None
            self.print_error(f'Missing Relop') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.relop(parent)

    def additive_expression(self, parent):
        l = self.get_lookahead()
        if l in first['Term']:
            self.term(self.add_node('Term', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['Additive-expression']: # Additive-expression -/-> eps
            parent.parent = None
            self.print_error(f'Missing Additive-expression') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
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
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.additive_expression_prime(parent)

    def additive_expression_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Term-zegond']:
            self.term_zegond(self.add_node('Term-zegond', parent))
            self.D(self.add_node('D', parent))
        elif l in follow['Additive-expression-zegond']: # Additive-expression-zegond -/-> eps
            parent.parent = None
            self.print_error(f'Missing Additive-expression-zegond') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.additive_expression_zegond(parent)  

    def D(self, parent):
        l = self.get_lookahead()
        if l in first['Addop']:
            self.addop(self.add_node('Addop', parent))
            self.term(self.add_node('Term', parent))
            self.semantics.code_gen("#arithmetic_op")
            self.D(self.add_node('D', parent))
        elif l in follow['D']: # D -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.D(parent)

    def addop(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('+', parent)
        elif l == '-':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('-', parent)
        elif l in follow['Addop']: # Addop -/-> eps
            parent.parent = None
            self.print_error(f'Missing Addop') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.addop(parent)

    def term(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor']:
            self.signed_num(self.add_node('Signed-factor', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term']: # Term -/-> eps
            parent.parent = None
            self.print_error(f'Missing Term') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.term(parent)

    def term_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor-prime'] + first['G']:
            self.signed_num_prime(self.add_node('Signed-factor-prime', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term-prime']: # Signed-factor-prime G -> eps
            self.signed_num_prime(self.add_node('Signed-factor-prime', parent))
            self.G(self.add_node('G', parent))
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.term_prime(parent)

    def term_zegond(self, parent):
        l = self.get_lookahead()
        if l in first['Signed-factor-zegond']:
            self.signed_num_zegond(self.add_node('Signed-factor-zegond', parent))
            self.G(self.add_node('G', parent))
        elif l in follow['Term-zegond']: # Term-zegond -/-> eps
            parent.parent = None
            self.print_error(f'Missing Term-zegond') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.term_zegond(parent)
    
    def G(self, parent):
        l = self.get_lookahead()
        if l == '*':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('*', parent)
            self.signed_num(self.add_node('Signed-factor', parent))
            self.semantics.code_gen("#arithmetic_op")
            self.G(self.add_node('G', parent))
        elif l in follow['G']: # G -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.G(parent)

    def signed_num(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('+', parent)
            self.factor(self.add_node('Factor', parent))
            self.semantics.code_gen("#signed_num")
        elif l == '-':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('-', parent)
            self.factor(self.add_node('Factor', parent))
            self.semantics.code_gen("#signed_num")
        elif l in first['Factor']:
            self.factor(self.add_node('Factor', parent))
        elif l in follow['Signed-factor']: # Signed-factor -/-> eps
            parent.parent = None
            self.print_error(f'Missing Signed-factor') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.signed_num(parent)

    def signed_num_prime(self, parent):
        l = self.get_lookahead()
        if l in first['Factor-prime']:
            self.factor_prime(self.add_node('Factor-prime', parent))
        elif l in follow['Signed-factor-prime']: # Factor-prime -> eps
            self.factor_prime(self.add_node('Factor-prime', parent))
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.signed_num_prime(parent)

    def signed_num_zegond(self, parent):
        l = self.get_lookahead()
        if l == '+':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('+', parent)
            self.factor(self.add_node('Factor', parent))
            self.semantics.code_gen("#signed_num")
        elif l == '-':
            self.semantics.code_gen("#symbol", self.lookahead)
            self.match('-', parent)
            self.factor(self.add_node('Factor', parent))
            self.semantics.code_gen("#signed_num")
        elif l in first['Factor-zegond']:
            self.factor_zegond(self.add_node('Factor-zegond', parent))
        elif l in follow['Signed-factor-zegond']: # Signed-factor-zegond -/-> eps
            parent.parent = None
            self.print_error(f'Missing Signed-factor-zegond') 
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.signed_num_zegond(parent)  

    def factor(self, parent): 
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
        elif l == 'ID':
            self.semantics.code_gen("#pid", self.lookahead)
            self.match('ID', parent)
            self.var_call_prime(self.add_node('Var-call-prime', parent))
        elif l == 'NUM':
            self.semantics.code_gen("#pnum", self.lookahead)
            self.match('NUM', parent)
        elif l in follow['Factor']: # Factor -/-> eps
            parent.parent = None
            self.print_error(f'Missing Factor')   
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.factor(parent) 

    def var_call_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            func_name = self.last_match
            self.semantics.code_gen("#func_call_start", func_name)
            self.match('(', parent)
            self.args(self.add_node('Args', parent))
            self.match(')', parent)
            self.semantics.code_gen("#func_call_end", func_name)
        elif l in first['Var-prime']:
            self.var_prime(self.add_node('Var-prime', parent))
        elif l in follow['Var-call-prime']: # Var-prime -> eps
            self.var_prime(self.add_node('Var-prime', parent))
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.var_call_prime(parent) 

    def var_prime(self, parent):
        l = self.get_lookahead()
        if l == '[':
            self.match('[', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(']', parent)
            self.semantics.code_gen("#arr_element")
        elif l in follow['Var-prime']: # Var-prime -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.var_prime(parent) 

    def factor_prime(self, parent):
        l = self.get_lookahead()
        if l == '(':
            #print(f'last: {self.last_match}')
            func_name = self.last_match
            self.semantics.code_gen("#func_call_start", func_name)
            self.match('(', parent)
            self.args(self.add_node('Args', parent))
            self.match(')', parent)
            self.semantics.code_gen("#func_call_end", func_name)
        elif l in follow['Factor-prime']: # Factor-prime -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.factor_prime(parent) 

    def factor_zegond(self, parent):
        l = self.get_lookahead()
        if l == '(':
            self.match('(', parent)
            self.expression(self.add_node('Expression', parent))
            self.match(')', parent)
        elif l == 'NUM':
            self.semantics.code_gen("#pnum", self.lookahead)
            self.match('NUM', parent)        
        elif l in follow['Factor-zegond']: # Factor-zegond -/-> eps
            parent.parent = None
            self.print_error(f'Missing Factor-zegond')  
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.factor_zegond(parent) 

    def args(self, parent):
        l = self.get_lookahead()
        if l in first['Arg-list']:
            self.arg_list(self.add_node('Arg-list', parent))
        elif l in follow['Args']: # Args -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.args(parent) 

    def arg_list(self, parent):
        l = self.get_lookahead()
        if l in first['Expression']:
            self.expression(self.add_node('Expression', parent))
            self.arg_list_prime(self.add_node('Arg-list-prime', parent))
        elif l in follow['Arg-list']: # Arg-list -/-> eps
            parent.parent = None
            self.print_error(f'Missing Arg-list')  
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.arg_list(parent) 

    def arg_list_prime(self, parent):
        l = self.get_lookahead()
        if l == ',':
            self.match(',', parent)
            self.expression(self.add_node('Expression', parent))
            self.arg_list_prime(self.add_node('Arg-list-prime', parent))
        elif l in follow['Arg-list-prime']: # Arg-list-prime -> eps
            self.add_node('epsilon', parent)
            return
        elif l == '$':
            self.terminate(parent)
        else:
            self.print_error(f'Illegal {l}')
            self.get_next_token()
            self.arg_list_prime(parent)

# if __name__ == '__main__':
# 	#Sample input from command line: "python compiler.py"
# 	input = "input.txt"

# 	# scanner = Scanner(input_path = input)
# 	# scanner.scan(input)

# 	parser = Parser(input_path=input)
# 	parser.parse()
# 	parser.print_parse_tree()
# 	#DotExporter(parser.tree).to_picture("tree.png")

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