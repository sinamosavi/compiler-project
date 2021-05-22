class Codegen:
    def __init__(self):
        self.semantic_stack = []
        self.program_block = []
        self.pb_index = 0
        self.cur_data_addr = 500
        self.cur_temp_addr = 1000
        self.temporaries = {}
        self.data = {}
        self.action_symbols = {
            'pid': self.pid,
            'pnum': self.pnum,
            'array_address': self.array_address,
            'assign': self.assign,
            'relop': self.relop,
            'addop': self.addop,
            'mult': self.mult,
            'symbol': self.symbol,
            'signed_factor': self.signed_factor,
            'save': self.save,
            'jp': self.jp,
            'jpf': self.jpf,
            'label': self.label,
            'while': self._while,
            'pop': self.pop,
            'output': self.output,
            'declare_array': self.declare_array
        }

    def pb_write(self, statement):
        self.program_block.append(statement)
        self.pb_index += 1

    def find_addr(self):
        addr = self.cur_data_addr
        self.cur_data_addr += 4
        return addr

    def get_temp(self):
        addr = self.cur_temp_addr
        self.cur_temp_addr += 4
        return addr

    def code_gen(self, action_symbol, arg=None):
        action_symbol = action_symbol[1:]
        self.action_symbols[action_symbol](arg)
        print(f'{action_symbol}({arg})\r\t\t-> {str(self.semantic_stack)[:-1]}')

    def pid(self, arg):
        for id, addr in self.data.items(): 
            if id == arg:
                self.semantic_stack.append(addr)
                return
        addr = self.find_addr()
        self.data.update({arg: addr})
        self.pb_write(f'(ASSIGN, #0, {addr}, )')
        self.semantic_stack.append(addr)

    def pnum(self, arg):
        tmp_addr = self.get_temp()
        self.pb_write(f'(ASSIGN, #{arg}, {tmp_addr}, )')
        self.temporaries.update({tmp_addr: arg})
        self.semantic_stack.append(tmp_addr)

    def pop(self, arg=None):
        self.semantic_stack.pop()

    def declare_array(self, arg=None):
        array_len_addr = self.semantic_stack.pop()
        for i in range(1, int(self.temporaries[array_len_addr])): # why start from 1 ?
            self.pb_write(f'(ASSIGN, #0, {self.cur_data_addr}, )')
            self.cur_data_addr += 4

    def save(self, arg=None): 
        self.semantic_stack.append(self.pb_index) # idx of empty statement
        self.pb_write('') # reserve a place for jpf

    def label(self, arg=None): 
        self.semantic_stack.append(self.pb_index - 1) # idx of last added statement (target of jp)

    def jpf(self, arg=None):
        jpf_pb_index = self.semantic_stack.pop() # empty idx reserved in save for jpf
        if_exp = self.semantic_stack.pop()
        # pb_index: '' -> reserved for JP
        # pb_index + 1: target of JPF
        self.program_block[jpf_pb_index] = f'(JPF, {if_exp}, {self.pb_index + 1},)'
        self.semantic_stack.append(self.pb_index)
        self.pb_write('')

    def jp(self, arg=None):
        jp_pb_index = self.semantic_stack.pop() # empty idx reserved in jpf for jp
        self.program_block[jp_pb_index] = f'(JP, {self.pb_index}, ,)'

    def _while(self, arg=None):
        jpf_pb_index = self.semantic_stack[-1] # empty idx reserved in save for jpf
        while_exp = self.semantic_stack[-2]
        label = self.semantic_stack[-3]
        # pb_index: (Jp, label+1, ,)
        # pb_index + 1: target of JPF
        self.program_block[jpf_pb_index] = f'(JPF, {while_exp}, {self.pb_index + 1}, )'
        self.pb_write(f'(JP, {label + 1}, , )')
        self.semantic_stack.pop()
        self.semantic_stack.pop()
        self.semantic_stack.pop()

    def assign(self, arg=None):
        op2 = self.semantic_stack.pop()
        op1 = self.semantic_stack.pop()
        self.pb_write(f'(ASSIGN, {op2}, {op1}, )')
        self.semantic_stack.append(op1)

    def array_address(self, arg=None):
        arr_index = self.semantic_stack.pop()
        arr_addr = self.semantic_stack.pop()
        t = self.get_temp()
        self.pb_write(f'(MULT, {arr_index}, #4, {t})')
        self.pb_write(f'(ADD, #{arr_addr}, {t}, {t})')
        self.semantic_stack.append('@' + str(t))  

    def relop(self, arg=None):
        op_2 = self.semantic_stack.pop()
        operand = self.semantic_stack.pop()
        op_1 = self.semantic_stack.pop()
        t = self.get_temp()
        if operand == '==':
            self.pb_write(f'(EQ, {op_1}, {op_2}, {t})')
        elif operand == '<':
            self.pb_write(f'(LT, {op_1}, {op_2}, {t})')
        self.semantic_stack.append(t)  

    def addop(self, arg=None):
        op1 = self.semantic_stack.pop()
        operation = self.semantic_stack.pop()
        op2 = self.semantic_stack.pop()
        t = self.get_temp()
        if operation == '+':
            self.pb_write(f'(ADD, {op1}, {op2}, {t})')
        else:
            self.pb_write(f'(SUB, {op2}, {op1}, {t})')
        self.semantic_stack.append(t)

    def mult(self, arg=None):
        op1 = self.semantic_stack.pop()
        op2 = self.semantic_stack.pop()
        t = self.get_temp()
        self.pb_write(f'(MULT, {op1}, {op2}, {t})')
        self.semantic_stack.append(t)

    def symbol(self, arg):
        self.semantic_stack.append(arg)
        
    def signed_factor(self, arg=None):
        factor_addr = self.semantic_stack.pop()
        sign = self.semantic_stack.pop()
        if self.temporaries.__contains__(factor_addr):
            factor = int(self.temporaries[factor_addr])
            if sign == '-':
                self.pnum(-factor)
            else:
                self.pnum(factor)
        else:
            for id, addr in self.data.items():
                if addr == factor_addr:
                    t = self.get_temp()
                    if sign == '-':
                        self.pb_write(f'(MULT, {addr}, #-1, {t})')
                    else:
                        self.pb_write(f'(MULT, {addr}, #1, {t})')
                    self.semantic_stack.append(t)
                    
    def output(self, arg=None):
        to_print = self.semantic_stack.pop()
        self.pb_write(f'(PRINT, {to_print}, , )')

    def save_program_block(self):
        with open('output.txt', 'w') as output:
            for i, block in enumerate(self.program_block):
                output.write(f'{i}\t{block}\n')

    