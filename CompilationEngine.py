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

    # 为了防止报错，先给语句逻辑留出“空壳”
    def compile_do(self):
        self._write_tag_start("doStatement")
        # 暂时只读到分号
        while self.tk.get_token() != ';': self.tk.advance()
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("doStatement")

    def compile_let(self):
        self._write_tag_start("letStatement")
        while self.tk.get_token() != ';': self.tk.advance()
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("letStatement")

    def compile_return(self):
        self._write_tag_start("returnStatement")
        while self.tk.get_token() != ';': self.tk.advance()
        self._write_xml("symbol", ";")
        self.tk.advance()
        self._write_tag_end("returnStatement")