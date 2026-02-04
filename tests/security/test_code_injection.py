import pytest
from src.security.code_analyzer import CodeSecurityAnalyzer
from src.security.exceptions import CodeAnalysisError

def test_detect_exec():
    code = "exec('import os; os.system(\"rm -rf /\")')"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
    assert any(t['category'] == 'FORBIDDEN_FUNCTION' for t in result['threats'])

def test_detect_eval():
    code = "eval('__import__(\"os\").system(\"whoami\")')"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']

def test_detect_forbidden_import():
    code = "import subprocess\nsubprocess.run(['ls'])"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
    assert any(t['category'] == 'FORBIDDEN_IMPORT' for t in result['threats'])

def test_detect_obfuscated_import():
    code = "__import__('o' + 's').system('evil')"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']

def test_detect_attribute_injection():
    code = "getattr(os, 'system')('ls')"
    # This might be caught by FORBIDDEN_IMPORTS if os is imported,
    # but let's check if getattr is caught.
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']

def test_detect_hex_obfuscation():
    code = "x = '\\x6f\\x73\\x2e\\x73\\x79\\x73\\x74\\x65\\x6d'" # "os.system"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
    assert any(t['category'] == 'SUSPICIOUS_PATTERN' for t in result['threats'])

def test_safe_code():
    code = """
def add(a, b):
    return a + b

class MyClass:
    def __init__(self, x):
        self.x = x

    def display(self):
        print(f"Value: {self.x}")
"""
    result = CodeSecurityAnalyzer.analyze(code)
    assert result['is_safe']

def test_detect_builtin_abuse():
    # Trying to get to __builtins__ via subclasses
    code = "().__class__.__base__.__subclasses__()[59].__init__.__globals__['__builtins__']['eval']('1+1')"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
    assert any(t['category'] == 'FORBIDDEN_ATTRIBUTE' for t in result['threats'])

def test_detect_file_operations():
    code = "open('/etc/passwd').read()"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
    assert any(t['category'] == 'FORBIDDEN_FUNCTION' for t in result['threats'])

def test_detect_socket_usage():
    code = "import socket\ns = socket.socket()"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']

def test_detect_os_system_via_getattr():
    code = "getattr(__import__('os'), 'system')('ls')"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']

def test_detect_lambda_exec():
    code = "(lambda: exec('import os; os.system(\"ls\")'))()"
    result = CodeSecurityAnalyzer.analyze(code)
    assert not result['is_safe']
