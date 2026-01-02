class CompilationEngine:
    def __init__(self, tokenizer, output_file):
        self.tk = tokenizer
        self.output = open(output_file, 'w', encoding='utf-8')
        self.indent_level = 0

    def _write_xml(self, tag, content):
        """辅助：写入带缩进的 XML 标签"""
        space = "  " * self.indent_level
        # 转义 XML 特殊字符
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        self.output.write(f"{space}<{tag}> {content} </{tag}>\n")

    def _write_tag_start(self, tag):
        self.output.write("  " * self.indent_level + f"<{tag}>\n")
        self.indent_level += 1

    def _write_tag_end(self, tag):
        self.indent_level -= 1
        self.output.write("  " * self.indent_level + f"</{tag}>\n")
    def _get_type_tag(self):
        """
        辅助方法：判断当前 Token 是关键字类型（如 int）还是自定义类名（标识符）
        """
        if self.tk.token_type() == "KEYWORD":
            return "keyword"
        else:
            return "identifier"

    def compile_class(self):
        """解析整个类结构"""
        self._write_tag_start("class")
        
        self.tk.advance() # 读入 'class'
        self._write_xml("keyword", self.tk.get_token())
        
        self.tk.advance() # 读入 类名
        self._write_xml("identifier", self.tk.get_token())
        
        self.tk.advance() # 读入 '{'
        self._write_xml("symbol", self.tk.get_token())

        self.tk.advance() # 为循环预读一个 Token
        while self.tk.has_more_tokens():
            token = self.tk.get_token()
            
            if token in ['static', 'field']:
                self.compile_class_var_dec()
                # 注意：compile_class_var_dec 内部最后会执行 advance()
                # 所以这里不需要再写一次 advance
            elif token in ['constructor', 'function', 'method']:
                self.compile_subroutine()
            elif token == '}':
                self._write_xml("symbol", "}")
                break
            else:
                # 容错处理：如果没匹配到，往下读一个，防止死循环
                if self.tk.has_more_tokens():
                    self.tk.advance()
        
        self._write_tag_end("class")
        self.output.close()

    def compile_class_var_dec(self):
        """解析类变量定义：static/field 类型 变量名;"""
        self._write_tag_start("classVarDec")
        
        # 写入 static 或 field
        self._write_xml("keyword", self.tk.get_token()) 
        
        # 读入并写入类型 (int, char, boolean 或 类名)
        self.tk.advance() 
        self._write_xml(self._get_type_tag(), self.tk.get_token())
        
        # 读入并写入变量名
        self.tk.advance()
        self._write_xml("identifier", self.tk.get_token())
        
        # 处理逗号分隔的多个变量
        while True:
            self.tk.advance()
            if self.tk.get_token() == ',':
                self._write_xml("symbol", ",")
                self.tk.advance()
                self._write_xml("identifier", self.tk.get_token())
            else:
                break
        
        # 此时 token 应该是 ';'
        self._write_xml("symbol", ";")
        
        # 为下一轮循环读取新 Token
        self.tk.advance() 
        
        self._write_tag_end("classVarDec")
    def compile_subroutine(self):
        """解析函数声明：function/method/constructor 类型 函数名 (参数列表) { 局部变量 语句 }"""
        self._write_tag_start("subroutineDec")
        
        # 此时当前 token 是 function/method/constructor
        self._write_xml("keyword", self.tk.get_token())
        
        # 返回类型
        self.tk.advance()
        self._write_xml(self._get_type_tag(), self.tk.get_token())
        
        # 函数名
        self.tk.advance()
        self._write_xml("identifier", self.tk.get_token())
        
        # 左括号 '('
        self.tk.advance()
        self._write_xml("symbol", "(")
        
        # 解析参数列表 (可能为空)
        self.tk.advance()
        self.compile_parameter_list()
        
        # 右括号 ')' - 注意：compile_parameter_list 结束后当前 token 应该是 ')'
        self._write_xml("symbol", ")")
        
        # 函数体
        self._write_tag_start("subroutineBody")
        self.tk.advance() # 读入 '{'
        self._write_xml("symbol", "{")
        
        # 循环处理函数体内的局部变量声明 (var...)
        self.tk.advance()
        while self.tk.get_token() == 'var':
            self.compile_var_dec()
            
        # 处理语句 (let, do, if, while, return)
        self.compile_statements()
        
        # 此时当前 token 应该是 '}'
        self._write_xml("symbol", "}")
        self._write_tag_end("subroutineBody")
        self._write_tag_end("subroutineDec")
        
        # 为 class 层的下一轮循环准备 Token
        self.tk.advance()

    def compile_parameter_list(self):
        """解析参数列表：((type varName) (',' type varName)*)?"""
        self._write_tag_start("parameterList")
        
        # 如果不是 ')'，说明有参数
        if self.tk.get_token() != ')':
            while True:
                self._write_xml(self._get_type_tag(), self.tk.get_token()) # 类型
                self.tk.advance()
                self._write_xml("identifier", self.tk.get_token())      # 变量名
                self.tk.advance()
                if self.tk.get_token() == ',':
                    self._write_xml("symbol", ",")
                    self.tk.advance()
                else:
                    break
        
        self._write_tag_end("parameterList")

    def compile_var_dec(self):
        """解析局部变量声明：var type varName (',' varName)* ;"""
        self._write_tag_start("varDec")
        self._write_xml("keyword", "var")
        
        self.tk.advance() # 类型
        self._write_xml(self._get_type_tag(), self.tk.get_token())
        
        self.tk.advance() # 变量名
        self._write_xml("identifier", self.tk.get_token())
        
        while True:
            self.tk.advance()
            if self.tk.get_token() == ',':
                self._write_xml("symbol", ",")
                self.tk.advance()
                self._write_xml("identifier", self.tk.get_token())
            else:
                break
        
        self._write_xml("symbol", ";")
        self.tk.advance() # 为下一行准备
        self._write_tag_end("varDec")

    def compile_statements(self):
        """解析一系列语句"""
        self._write_tag_start("statements")
        
        while self.tk.get_token() in ['let', 'if', 'while', 'do', 'return']:
            token = self.tk.get_token()
            if token == 'let': self.compile_let()
            elif token == 'if': self.compile_if()
            elif token == 'while': self.compile_while()
            elif token == 'do': self.compile_do()
            elif token == 'return': self.compile_return()
            
        self._write_tag_end("statements")

    def compile_let(self):
        """解析 let 语句：let varName ([expression])? = expression;"""
        self._write_tag_start("letStatement")
        self._write_xml("keyword", "let")
        
        self.tk.advance() # 变量名
        self._write_xml("identifier", self.tk.get_token())
        
        self.tk.advance()
        if self.tk.get_token() == '[':
            self._write_xml("symbol", "[")
            self.tk.advance()
            self.compile_expression()
            self._write_xml("symbol", "]")
            self.tk.advance()
            
        self._write_xml("symbol", "=") # 等号
        self.tk.advance()
        self.compile_expression()
        
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("letStatement")

    def compile_do(self):
        """解析 do 语句：do subroutineCall;"""
        self._write_tag_start("doStatement")
        self._write_xml("keyword", "do")
        self.tk.advance()
        self.compile_subroutine_call()
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("doStatement")

    def compile_subroutine_call(self):
        """辅助解析：函数调用 (例如 Main.run(x, y))"""
        # 这里逻辑稍微复杂，需处理 'f(x)' 和 'Obj.f(x)' 两种情况
        self._write_xml("identifier", self.tk.get_token())
        self.tk.advance()
        if self.tk.get_token() == '.':
            self._write_xml("symbol", ".")
            self.tk.advance()
            self._write_xml("identifier", self.tk.get_token())
            self.tk.advance()
        
        self._write_xml("symbol", "(")
        self.tk.advance()
        self.compile_expression_list() # 解析参数列表
        self._write_xml("symbol", ")")
        self.tk.advance()

    def compile_expression_list(self):
        """解析参数列表：(expression (',' expression)*)?"""
        self._write_tag_start("expressionList")
        if self.tk.get_token() != ')':
            self.compile_expression()
            while self.tk.get_token() == ',':
                self._write_xml("symbol", ",")
                self.tk.advance()
                self.compile_expression()
        self._write_tag_end("expressionList")

    def compile_return(self):
        self._write_tag_start("returnStatement")
        while self.tk.get_token() != ';': self.tk.advance()
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("returnStatement")
    #
    '''

    Expression：由一个 Term 以及零个或多个 (op Term) 组成（例如 x + y）。

    Term：表达式的最小单元。可以是：数字、字符串、变量、函数调用、数组索引、或者括号里的另一个表达式。

    ExpressionList：函数调用时括号里的参数列表（例如 Math.multiply(a, b) 中的 a, b）

    '''
    def compile_expression(self):
        """解析表达式：term (op term)*"""
        self._write_tag_start("expression")
        
        # 解析第一个 Term
        self.compile_term()
        
        # 看看后面有没有运算符 (op)
        ops = '+-*/&|<>='
        while self.tk.get_token() in ops:
            self._write_xml("symbol", self.tk.get_token()) # 写入运算符
            self.tk.advance()
            self.compile_term() # 解析下一个 Term
            
        self._write_tag_end("expression")

    def compile_term(self):
        """解析项：数字、变量、括号表达式、一元运算等"""
        self._write_tag_start("term")
        
        token_type = self.tk.token_type()
        token = self.tk.get_token()

        if token_type == "INT_CONST":
            self._write_xml("integerConstant", token)
            self.tk.advance()
        elif token_type == "STRING_CONST":
            self._write_xml("stringConstant", token)
            self.tk.advance()
        elif token in ['true', 'false', 'null', 'this']:
            self._write_xml("keyword", token)
            self.tk.advance()
        elif token == '(':
            # 括号表达式: '(' expression ')'
            self._write_xml("symbol", "(")
            self.tk.advance()
            self.compile_expression()
            self._write_xml("symbol", ")")
            self.tk.advance()
        elif token in ['-', '~']:
            # 一元运算: '-' term 或 '~' term
            self._write_xml("symbol", token)
            self.tk.advance()
            self.compile_term()
        elif token_type == "IDENTIFIER":
            # 可能是变量名、数组 a[i] 或函数调用 f(x)
            next_token = self._peek_next_token()
            if next_token == '[':
                # 数组处理
                self._write_xml("identifier", token)
                self.tk.advance() # [
                self._write_xml("symbol", "[")
                self.tk.advance()
                self.compile_expression()
                self._write_xml("symbol", "]")
                self.tk.advance()
            elif next_token in ['(', '.']:
                # 子程序调用
                self.compile_subroutine_call()
            else:
                # 普通变量
                self._write_xml("identifier", token)
                self.tk.advance()
        
        self._write_tag_end("term")

    def _peek_next_token(self):
        """辅助方法：偷看下一个 Token，但不移动指针"""
        if self.tk.has_more_tokens():
            return self.tk.tokens[self.tk.current_index + 1]
        return None