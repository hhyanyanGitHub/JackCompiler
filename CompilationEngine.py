from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:
    def __init__(self, tokenizer, output_file):
        self.tk = tokenizer
        self.vm_writer = VMWriter(output_file)
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.label_count = 0 # 用于生成唯一的 if/while 标签

    def compile_class(self):
        """解析 Class 并记录类名"""
        self.tk.advance() # 'class'
        self.tk.advance() # className
        self.class_name = self.tk.get_token()
        self.tk.advance() # '{'

        self.tk.advance()
        while self.tk.has_more_tokens():
            token = self.tk.get_token()
            if token in ['static', 'field']:
                self.compile_class_var_dec()
            elif token in ['constructor', 'function', 'method']:
                self.compile_subroutine()
            elif token == '}':
                break
        self.vm_writer.close()

    def compile_class_var_dec(self):
        """将类变量存入符号表"""
        kind = self.tk.get_token().upper() # STATIC 或 FIELD
        self.tk.advance()
        v_type = self.tk.get_token() # int, char...
        self.tk.advance()
        v_name = self.tk.get_token() # 变量名
        
        self.symbol_table.define(v_name, v_type, kind)
        
        while True:
            self.tk.advance()
            if self.tk.get_token() == ',':
                self.tk.advance()
                v_name = self.tk.get_token()
                self.symbol_table.define(v_name, v_type, kind)
            else:
                break
        self.tk.advance() # 跳过 ';'
    
    def compile_subroutine(self):
        """处理函数入口，特别是 method 的 this 指针绑定"""
        self.symbol_table.start_subroutine()
        keyword = self.tk.get_token() # constructor/function/method
        
        # 如果是 method，ARG 0 自动分配给 'this'
        if keyword == 'method':
            self.symbol_table.define('this', self.class_name, 'ARG')
            
        self.tk.advance() # 返回类型
        self.tk.advance() 
        subroutine_name = self.tk.get_token() # 函数名
        full_name = f"{self.class_name}.{subroutine_name}"
        
        self.tk.advance() # '('
        self.tk.advance()
        self.compile_parameter_list()
        self.tk.advance() # '{'
        
        # 先解析完所有 var 声明，填充符号表
        self.tk.advance()
        while self.tk.get_token() == 'var':
            self.compile_var_dec()

        # 此时已知局部变量个数，输出 function 声明
        n_locals = self.symbol_table.var_count('VAR')
        self.vm_writer.write_function(full_name, n_locals)

        # 特殊处理：constructor 需要分配内存
        if keyword == 'constructor':
            n_fields = self.symbol_table.var_count('FIELD')
            self.vm_writer.write_push('constant', n_fields)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('pointer', 0) # 将新地址设为 THIS
        
        # 特殊处理：method 需要重定向 THIS 到 ARG 0
        elif keyword == 'method':
            self.vm_writer.write_push('argument', 0)
            self.vm_writer.write_pop('pointer', 0)

        self.compile_statements()
        # 跳过最后的分号或括号
        if self.tk.has_more_tokens(): self.tk.advance() 

    def compile_var_dec(self):
        """将局部变量存入符号表"""
        # 逻辑与 compile_class_var_dec 类似，kind 固定为 'VAR'
        self.tk.advance() # 跳过 'var'
        v_type = self.tk.get_token()
        self.tk.advance()
        v_name = self.tk.get_token()
        self.symbol_table.define(v_name, v_type, 'VAR')
        
        while True:
            self.tk.advance()
            if self.tk.get_token() == ',':
                self.tk.advance()
                v_name = self.tk.get_token()
                self.symbol_table.define(v_name, v_type, 'VAR')
            else:
                break
        self.tk.advance() # 跳过 ';'
    def compile_parameter_list(self):
        """解析参数列表并存入符号表：(type varName (',' type varName)*)?"""
        # 注意：此时当前 token 已经是参数列表的第一个词，或者是一个 ')'
        if self.tk.get_token() != ')':
            v_type = self.tk.get_token()
            self.tk.advance()
            v_name = self.tk.get_token()
            self.symbol_table.define(v_name, v_type, 'ARG')
            
            while True:
                self.tk.advance()
                if self.tk.get_token() == ',':
                    self.tk.advance()
                    v_type = self.tk.get_token()
                    self.tk.advance()
                    v_name = self.tk.get_token()
                    self.symbol_table.define(v_name, v_type, 'ARG')
                else:
                    break
    
    def compile_expression(self):
        """解析表达式：term (op term)*"""
        # 解析第一个 Term
        self.compile_term()
        
        # 运算符映射表：Jack 符号 -> VM 指令或系统调用
        ops = {
            '+': 'add', '-': 'sub', '*': 'Math.multiply', '/': 'Math.divide',
            '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'
        }
        
        while self.tk.get_token() in ops:
            op = self.tk.get_token()
            self.tk.advance()
            
            # 解析下一个 Term
            self.compile_term()
            
            # 生成运算指令
            if op in ['*', '/']:
                # 乘除法在 VM 层级是通过系统调用实现的
                self.vm_writer.write_call(ops[op], 2)
            else:
                self.vm_writer.write_arithmetic(ops[op])

    def compile_term(self):
        """解析项：处理数字、变量、括号、一元运算等"""
        token_type = self.tk.token_type()
        token = self.tk.get_token()

        if token_type == "INT_CONST":
            self.vm_writer.write_push('constant', token)
            self.tk.advance()
            
        elif token_type == "STRING_CONST":
            # 字符串处理：申请内存并逐个 appendChar
            s = token
            self.vm_writer.write_push('constant', len(s))
            self.vm_writer.write_call('String.new', 1)
            for char in s:
                self.vm_writer.write_push('constant', ord(char))
                self.vm_writer.write_call('String.appendChar', 2)
            self.tk.advance()

        elif token in ['true', 'false', 'null', 'this']:
            if token == 'this':
                self.vm_writer.write_push('pointer', 0)
            else:
                self.vm_writer.write_push('constant', 0)
                if token == 'true':
                    self.vm_writer.write_arithmetic('not') # true 是 0 取反
            self.tk.advance()

        elif token == '(':
            self.tk.advance() # (
            self.compile_expression()
            self.tk.advance() # )

        elif token in ['-', '~']:
            op = token
            self.tk.advance()
            self.compile_term()
            if op == '-': self.vm_writer.write_arithmetic('neg')
            else: self.vm_writer.write_arithmetic('not')

        elif token_type == "IDENTIFIER":
            name = token
            next_token = self._peek_next_token()
            
            if next_token == '[': # 数组访问
                self.tk.advance() # 变量名
                self.tk.advance() # [
                self.compile_expression()
                self.tk.advance() # ]
                # 将数组基地址和偏移量相加
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.write_push(kind, idx)
                self.vm_writer.write_arithmetic('add')
                self.vm_writer.write_pop('pointer', 1) # 锚定 THAT
                self.vm_writer.write_push('that', 0)
                
            elif next_token in ['(', '.']: # 函数调用
                self.compile_subroutine_call()
            else: # 普通变量
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.write_push(kind, idx)
                self.tk.advance()
    
    def compile_let(self):
        """解析 let 语句"""
        self.tk.advance() # let
        var_name = self.tk.get_token()
        self.tk.advance()
        
        is_array = False
        if self.tk.get_token() == '[':
            is_array = True
            # ... 数组逻辑稍复杂，先处理普通变量 ...
            pass

        self.tk.advance() # =
        self.compile_expression()
        self.tk.advance() # ;
        
        # 将结果存入变量
        kind = self.symbol_table.kind_of(var_name)
        idx = self.symbol_table.index_of(var_name)
        self.vm_writer.write_pop(kind, idx)

    def compile_do(self):
        """解析 do 语句"""
        self.tk.advance() # do
        self.compile_subroutine_call()
        # do 语句会调用函数，Jack 规定所有函数都有返回值
        # 但 do 语句不关心返回值，所以必须将其从栈顶弹出并丢弃
        self.vm_writer.write_pop('temp', 0) 
        self.tk.advance() # ;