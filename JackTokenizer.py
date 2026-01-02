import re

class JackTokenizer:
    def __init__(self, input_file):
        """打开文件并进行预处理（去除注释和空行）"""
        with open(input_file, 'r') as f:
            self.content = f.read()
        # TODO: 编写正则或逻辑去除 // 和 /* */ 注释
        self.tokens = self._tokenize(self.content)
        self.current_token = None
        self.index = -1

    def _tokenize(self, source):
        """这是核心逻辑：利用正则表达式将字符串切分成 token 列表"""
        # 提示：可以使用 re.findall

        pass

    def has_more_tokens(self):
        return self.index + 1 < len(self.tokens)

    def advance(self):
        self.index += 1
        self.current_token = self.tokens[self.index]

    def token_type(self):
        """返回当前 token 的类型"""
        pass