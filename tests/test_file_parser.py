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

if __name__ == "__main__":
    # Manual run if needed
    try:
        test_parse_gitkeep_files()
        test_parse_files_without_trailing_newline()
        test_parse_fallback_gitkeep()
        test_nested_paths()
        print("✅ All file parser tests PASSED!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
