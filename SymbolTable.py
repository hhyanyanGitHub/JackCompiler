class SymbolTable:
    def __init__(self):
        """初始化类级和子程序级符号表"""
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {"STATIC": 0, "FIELD": 0, "ARG": 0, "VAR": 0}

    def start_subroutine(self):
        """开启一个新函数，清空子程序级符号表"""
        self.subroutine_scope.clear()
        self.counts["ARG"] = 0
        self.counts["VAR"] = 0

    def define(self, name, var_type, kind):
        """
        向表里添加新变量
        kind: 'STATIC', 'FIELD', 'ARG', 'VAR'
        """
        index = self.counts[kind]
        # 根据种类选择存储在哪个作用域
        if kind in ["STATIC", "FIELD"]:
            self.class_scope[name] = (var_type, kind, index)
        else:
            self.subroutine_scope[name] = (var_type, kind, index)
        self.counts[kind] += 1

    def var_count(self, kind):
        """返回当前种类的变量计数"""
        return self.counts[kind]

    def _get_entry(self, name):
        """辅助方法：先找子程序作用域，再找类作用域"""
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]
        return self.class_scope.get(name)

    def kind_of(self, name):
        entry = self._get_entry(name)
        return entry[1] if entry else "NONE"

    def type_of(self, name):
        entry = self._get_entry(name)
        return entry[0] if entry else None

    def index_of(self, name):
        entry = self._get_entry(name)
        return entry[2] if entry else None