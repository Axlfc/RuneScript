import pytest
from src.core.nia_claude_client import nIAResponse

def test_parse_gitkeep_files():
    """Verifica que los archivos .gitkeep se detecten correctamente."""
    llm_response = """
Hola, aquí tienes la estructura del proyecto:

File: assets/img/.gitkeep
```text
```

File: css/style.css
```css
body { margin: 0; }
```

También incluí un archivo JS:
File: js/app.js
```javascript
console.log("hello");
```
"""

    response = nIAResponse(llm_response)
    files = response.files

    assert len(files) == 3, f"Expected 3 files, got {len(files)}"

    assert 'assets/img/.gitkeep' in files, ".gitkeep file not detected"
    assert files['assets/img/.gitkeep'] == '', ".gitkeep should be empty"

    assert 'css/style.css' in files, "CSS file not detected"
    assert 'margin' in files['css/style.css'], "CSS content incorrect"

    assert 'js/app.js' in files, "JS file not detected"
    assert 'hello' in files['js/app.js'], "JS content incorrect"

def test_parse_files_without_trailing_newline():
    """Verifica que los bloques sin salto de línea final se detecten."""
    llm_response = """
File: test.txt
```text
hello world```
"""
    response = nIAResponse(llm_response)
    assert 'test.txt' in response.files
    assert response.files['test.txt'] == 'hello world'

def test_parse_fallback_gitkeep():
    """Verifica el modo fallback para .gitkeep."""
    llm_response = """
assets/img/.gitkeep
```text
```
"""
    response = nIAResponse(llm_response)
    assert 'assets/img/.gitkeep' in response.files
    assert response.files['assets/img/.gitkeep'] == ''

def test_nested_paths():
    """Verifica que las rutas anidadas se procesen correctamente."""
    llm_response = "File: deep/nested/path/to/file.txt\n```\ncontent\n```"
    response = nIAResponse(llm_response)
    assert 'deep/nested/path/to/file.txt' in response.files
    assert response.files['deep/nested/path/to/file.txt'] == 'content'

def test_parse_xml_tags():
    """Verifica la detección de archivos mediante etiquetas XML."""
    llm_response = """
    Aquí tienes el código:
    <file path="src/main.py">
    print("hello xml")
    </file>
    <file path='css/style.css'>
    body { color: blue; }
    </file>
    """
    response = nIAResponse(llm_response)
    assert 'src/main.py' in response.files
    assert 'print("hello xml")' in response.files['src/main.py'].strip()
    assert 'css/style.css' in response.files
    assert 'blue' in response.files['css/style.css']

def test_system_file_filtering():
    """Verifica que los archivos protegidos por el sistema sean filtrados."""
    llm_response = """
File: src/main.py
```python
print("hello")
```

File: IMPLEMENTATION_PLAN.md
```markdown
# Corrupted Plan
...
```

File: .nia_config.json
```json
{}
```
"""
    response = nIAResponse(llm_response)
    assert 'src/main.py' in response.files
    assert 'IMPLEMENTATION_PLAN.md' not in response.files
    assert '.nia_config.json' not in response.files
    assert len(response.files) == 1

def test_strict_json_parsing():
    """Verifica que el parsing de JSON estricto funcione."""
    import json
    data = {
        "files": [
            {"path": "src/app.py", "content": "print('json')"},
            {"path": "css/style.css", "content": "body {}"}
        ]
    }
    llm_response = json.dumps(data)
    response = nIAResponse(llm_response)
    assert response.parsing_method == "strict_json"
    assert 'src/app.py' in response.files
    assert response.files['src/app.py'] == "print('json')"

def test_manual_json_parsing_with_garbage():
    """Verifica que se puedan extraer archivos de un JSON 'sucio'."""
    llm_response = """
Aquí tienes los archivos en formato JSON:
{
  "files": [
    {
      "path": "test.py",
      "content": "print('hello')
with a literal newline that breaks JSON"
    }
  ]
}
Espero que te sirva.
"""
    response = nIAResponse(llm_response)
    assert response.parsing_method == "manual_json"
    assert 'test.py' in response.files
    assert "print('hello')" in response.files['test.py']
    assert "literal newline" in response.files['test.py']

if __name__ == "__main__":
    # Manual run if needed
    try:
        test_parse_gitkeep_files()
        test_parse_files_without_trailing_newline()
        test_parse_fallback_gitkeep()
        test_nested_paths()
        test_parse_xml_tags()
        print("✅ All file parser tests PASSED!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
