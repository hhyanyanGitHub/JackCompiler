import re

class JackTokenizer:
    def __init__(self, input_file):
        """初始化：读取并清洗数据"""
        with open(input_file, 'r',encoding='utf-8') as f:
            self.source = f.read()
        
        # 1. 预处理：去除注释和多余空白
        self._clean_source()
        # 2. 词法分析：切分成 tokens
        self._tokenize()
        
        self.current_index = -1
        self.current_token = None

    def _clean_source(self):
        """利用正则移除所有注释"""
        # 移除多行注释 /* ... */
        self.source = re.sub(r'/\*.*?\*/', '', self.source, flags=re.DOTALL)
        # 移除单行注释 // ...
        self.source = re.sub(r'//.*', '', self.source)

    def _tokenize(self):
        """将清洗后的源码切分为 Token 列表"""
        # 定义各类 Token 的组合正则
        keywords = r'(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)'
        symbols = r'([\{\}\(\)\[\]\.,;+\-*/&|<>=~])'
        integer = r'(\d+)'
        string = r'"([^"\n]*)"'
        identifier = r'([A-Za-z_][\w]*)'

        # 合并所有正则
        pattern = f'{keywords}|{symbols}|{integer}|{string}|{identifier}'
        
        self.tokens = []
        for match in re.finditer(pattern, self.source):
            # 过滤掉正则匹配中的空值
            token = match.group(0)
            if token:
                # 如果是字符串，去掉引号存入列表（Jack规范要求）
                if token.startswith('"'):
                    self.tokens.append(token) 
                else:
                    self.tokens.append(token)

    def has_more_tokens(self):
        return self.current_index + 1 < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_index += 1
            self.current_token = self.tokens[self.current_index]

    def token_type(self):
        """识别当前 token 的类型"""
        token = self.current_token
        if token in ['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return']:
            return "KEYWORD"
        if token in '{}()[].,;+-*/&|<>=~':
            return "SYMBOL"
        if token.isdigit():
            return "INT_CONST"
        if token.startswith('"'):
            return "STRING_CONST"
        return "IDENTIFIER"

    def get_token(self):
        """获取当前 token 内容（如果是字符串则去除引号）"""
        if self.token_type() == "STRING_CONST":
            return self.current_token[1:-1]
        return self.current_token