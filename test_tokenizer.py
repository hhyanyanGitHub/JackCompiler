from JackTokenizer import JackTokenizer

# 模拟一个简单的 Jack 代码片段
test_code = """
/** 这是一个测试类 */
class Main {
    function void main() {
        var String s;
        let s = "Hello World"; // 打印
        do Output.printString(s);
    }
}
"""

# 将其写入临时文件进行测试
with open("Test.jack","w", encoding= 'utf-8' ) as f:
    f.write(test_code)

tokenizer = JackTokenizer("Test.jack")
print(f"{'Token':<15} | {'Type':<15}")
print("-" * 35)

while tokenizer.has_more_tokens():
    tokenizer.advance()
    print(f"{tokenizer.get_token():<15} | {tokenizer.token_type():<15}")