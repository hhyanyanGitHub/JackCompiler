class VMWriter:
    def __init__(self, output_file):
        self.output = open(output_file, 'w', encoding='utf-8')

    def write_push(self, segment, index):
        # segment: CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
        seg = segment.lower()
        if seg == "var": seg = "local"
        if seg == "field": seg = "this"
        self.output.write(f"push {seg} {index}\n")

    def write_pop(self, segment, index):
        seg = segment.lower()
        if seg == "var": seg = "local"
        if seg == "field": seg = "this"
        self.output.write(f"pop {seg} {index}\n")

    def write_arithmetic(self, command):
        # command: ADD, SUB, NEG, EQ, GT, LT, AND, OR, NOT
        self.output.write(f"{command.lower()}\n")

    def write_label(self, label):
        self.output.write(f"label {label}\n")

    def write_goto(self, label):
        self.output.write(f"goto {label}\n")

    def write_if(self, label):
        self.output.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.output.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.output.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.output.write("return\n")

    def close(self):
        self.output.close()