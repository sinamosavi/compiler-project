class Semantics:
    def __init__(self):
        self.action_symbols = {
            'pop': self.pop,
            'declare_array': self.declare_array,
            'label': self.label,
            'save': self.save,
            'while': self._while,
            'jump': self.jump,
            'cond_jump': self.cond_jump,
            'pid': self.pid,
            'pnum': self.pnum,
            'assign': self.assign,
            'arithmetic_op': self.arithmetic_op,
            'arr_element': self.arr_element,
            'symbol': self.symbol,
            'signed_num': self.signed_num,
            'print': self.print_message,
            # for loop
            'assign_vars': self.assign_vars,
            'jpf_for': self.jpf_for,
            'label_for': self.label_for,
            'vars_begin': self.vars_begin,
            'var_zegond': self.var_zegond,
            'vars_end': self.vars_end
        }
        self.pb_index = 0
        self.cur_data_address = 200
        self.cur_temp_address = 800
        self.sem_stack = [] # Semantic stack
        self.pb = [] # Program block
        self.temporaries = {}
        self.data = {}

    def code_gen(self, action_symbol, arg = None):
        action_symbol = action_symbol[1:] # Remove the '#' character at the start
        routine = self.action_symbols[action_symbol]
        routine(arg)
    
    def pb_write(self, statement):
        self.pb.append(statement)
        self.pb_index += 1

    def find_address(self):
        address = self.cur_data_address
        self.cur_data_address += 4
        # Need to prevent overlapping between permanent and temporary addresses
        self.cur_temp_address += 4
        return address

    def new_temp(self):
        addr = self.cur_temp_address
        self.cur_temp_address += 4
        return addr

    def save_pb(self):
        output = open('output.txt', 'w')
        for i, b in enumerate(self.pb):
                output.write(f'{i}\t{b}\n')
    
    def pop(self, arg):
        self.sem_stack.pop()

    def declare_array(self, arg):
        array_len_address = self.sem_stack.pop()
        # Dedicate addresses for non-zero array indices 
        array_len = int(self.temporaries[array_len_address])
        for i in range(1, array_len):
            address = self.find_address()
            self.pb_write(f'(ASSIGN, #0, {address}, )')
    
    def label(self, arg):
        self.sem_stack.append(self.pb_index - 1) # idx of last added statement (target of jp)

    def save(self, arg): 
        self.sem_stack.append(self.pb_index) # idx of empty statement
        self.pb_write('') # reserve a place for jpf
    
    def _while(self, arg):
        jpf_pb_index = self.sem_stack.pop() # empty idx reserved in save for jpf
        while_exp = self.sem_stack.pop()
        label = self.sem_stack.pop()
        # pb_index: (Jp, label+1, ,)
        # pb_index + 1: target of JPF
        self.pb[jpf_pb_index] = f'(JPF, {while_exp}, {self.pb_index + 1}, )'
        self.pb_write(f'(JP, {label + 1}, , )')
    
    def jump(self, arg):
        jp_pb_index = self.sem_stack.pop() # empty idx reserved in jpf for jp
        self.pb[jp_pb_index] = f'(JP, {self.pb_index}, ,)'
    
    def cond_jump(self, arg):
        jpf_pb_index = self.sem_stack.pop() # empty idx reserved in save for jpf
        if_exp = self.sem_stack.pop()
        # pb_index: '' -> reserved for JP
        # pb_index + 1: target of JPF
        self.pb[jpf_pb_index] = f'(JPF, {if_exp}, {self.pb_index + 1},)'
        self.sem_stack.append(self.pb_index)
        self.pb_write('')

    
    def pid(self, arg):
        if self.data.__contains__(arg): # Check if the variable has already been defined
            address = self.data[arg]
            self.sem_stack.append(address)
        else: # If not, do it
            address = self.find_address()
            self.data.update({arg: address})
            self.sem_stack.append(address)
            self.pb_write(f'(ASSIGN, #0, {address}, )')

    def pnum(self, arg):
        t = self.new_temp()
        self.temporaries.update({t: arg})
        self.sem_stack.append(t)
        self.pb_write(f'(ASSIGN, #{arg}, {t}, )')

    def assign(self, arg):
        content_address = self.sem_stack.pop()
        id_address = self.sem_stack.pop()
        self.sem_stack.append(id_address)
        self.pb_write(f'(ASSIGN, {content_address}, {id_address}, )')

    def arithmetic_op(self, arg):
        op2 = self.sem_stack.pop()
        operand = self.sem_stack.pop()
        op1 = self.sem_stack.pop()
        t = self.new_temp()
        if operand == '==':
            self.pb_write(f'(EQ, {op1}, {op2}, {t})')
        elif operand == '<':
            self.pb_write(f'(LT, {op1}, {op2}, {t})')
        elif operand == '+':
            self.pb_write(f'(ADD, {op2}, {op1}, {t})')
        elif operand == '-':
            self.pb_write(f'(SUB, {op1}, {op2}, {t})')
        elif operand == '*':
            self.pb_write(f'(MULT, {op2}, {op1}, {t})')
        self.sem_stack.append(t)
    
    def arr_element(self, arg):
        arr_index = self.sem_stack.pop()
        arr_addr = self.sem_stack.pop()
        t = self.new_temp()
        self.sem_stack.append('@' + str(t))  
        self.pb_write(f'(MULT, {arr_index}, #4, {t})')
        self.pb_write(f'(ADD, #{arr_addr}, {t}, {t})')

    def symbol(self, arg):
        self.sem_stack.append(arg)
        
    def signed_num(self, arg):                    
        num_address = self.sem_stack.pop()
        sign = self.sem_stack.pop()
        if self.temporaries.__contains__(num_address):
            val = int(self.temporaries[num_address])
            if sign == '+':
                self.pnum(val)
            elif sign == '-':
                self.pnum(val * -1)
        else:
            #address = list(self.data.keys())[list(self.data.values()).index(num_address)]
            t = self.new_temp()
            self.sem_stack.append(t)
            if sign == '+':
                self.pb_write(f'(MULT, {num_address}, #1, {t})')
            elif sign == '-':
                self.pb_write(f'(MULT, {num_address}, #-1, {t})')
                    
    def print_message(self, arg):
        # For now we assume that every function call is output()
        message = self.sem_stack.pop()
        self.pb_write(f'(PRINT, {message}, , )')

    #######################
    # FOR LOOP
    #######################
    def vars_begin(self, arg):
        t = self.new_temp()
        addr_first_var = self.sem_stack.pop()
        self.pb_write(f'(ASSIGN, #{addr_first_var}, {t}, )')
        self.sem_stack.append(t)    # addr of first var
        self.sem_stack.append(1)    # counter

    def var_zegond(self, arg):
        t = self.new_temp()
        addr_next_var = self.sem_stack.pop()
        counter = self.sem_stack.pop()
        self.pb_write(f'(ASSIGN, #{addr_next_var}, {t}, )')
        self.sem_stack.append(counter + 1)

    def vars_end(self, arg):
        counter = self.sem_stack.pop()
        addr_first_var = self.sem_stack.pop()
        temp_counter = self.new_temp()
        temp_addr_first_var = self.new_temp()
        self.pb_write(f'(ASSIGN, #{counter}, {temp_counter}, )')
        self.pb_write(f'(ASSIGN, #{addr_first_var}, {temp_addr_first_var}, )')
        self.sem_stack.append(temp_counter)
        self.sem_stack.append(temp_addr_first_var)

    def label_for(self, arg):
        self.sem_stack.append(self.pb_index) # target of jpf_for

    def assign_vars(self, arg):
        # idx saved by label            (top)
        # addr of addr of current var   (top-1)
        # current counter               (top-2)
        # addr of pid                   (top-3)
        addr_addr_cur_var = self.sem_stack[-2]
        addr_pid = self.sem_stack[-4]
        self.pb_write(f'(ASSIGN, @{addr_addr_cur_var}, {addr_pid}, )')
        self.pb_write(f'(ASSIGN, @{addr_pid}, {addr_pid}, )')


    def jpf_for(self, arg):
        # idx saved by label            (top)
        # addr of addr of current var   (top-1)
        # current counter               (top-2)
        # addr of pid                   (top-3)
        label_index = self.sem_stack.pop()
        addr_addr_cur_var = self.sem_stack.pop()
        counter = self.sem_stack.pop()
        addr_pid = self.sem_stack.pop()
        self.pb_write(f'(ADD, {addr_addr_cur_var}, #4, {addr_addr_cur_var})')
        self.pb_write(f'(SUB, {counter}, #1, {counter})')
        t = self.new_temp()
        self.pb_write(f'(EQ, {counter}, #0, {t})')
        self.pb_write(f'(JPF, {t}, {label_index},)')

    

    



    