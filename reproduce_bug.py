import json
import logging
from src.core.robust_parser import RobustJSONParser

def test_sanitization():
    bad_json = """
{
  "path": `index.html`,
  "content": `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test "Quotes"</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>`
}
"""
    print("Original bad JSON:")
    print(bad_json)

    sanitized = RobustJSONParser.sanitize_json(bad_json)
    print("\nSanitized JSON:")
    print(sanitized)

    try:
        data = json.loads(sanitized)
        print("\nSuccessfully parsed JSON!")
        print(f"Path: {data['path']}")
        print(f"Content length: {len(data['content'])}")
        assert data['path'] == "index.html"
        assert 'title>Test "Quotes"</title>' in data['content']
        assert '\n' in data['content']
    except Exception as e:
        print(f"\nFailed to parse: {e}")
        exit(1)

if __name__ == "__main__":
    test_sanitization()
