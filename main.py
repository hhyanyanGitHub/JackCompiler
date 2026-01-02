import os
import sys
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

def main():
    if len(sys.argv) != 2:
        print("用法: python main.py [文件名.jack 或 文件夹路径]")
        return

    path = sys.argv[1]
    files = []
    
    if os.path.isfile(path):
        files.append(path)
    else:
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jack')]

    for input_file in files:
        output_file = input_file.replace(".jack", ".xml")
        print(f"正在编译: {input_file} -> {output_file}")
        
        tokenizer = JackTokenizer(input_file)
        engine = CompilationEngine(tokenizer, output_file)
        engine.compile_class()

if __name__ == "__main__":
    main()