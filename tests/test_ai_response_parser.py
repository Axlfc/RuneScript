import json

from src.utils.parser_utils import AIResponseParser


def test_parse_pure_project_metadata_json():
    response = json.dumps({
        "project_name": "HAIS",
        "project_description": "Autonomous multi-agent system",
        "project_tasks": ["Inspect current state", "Build autonomous kernel"],
        "initial_files": {},
    })

    parsed = AIResponseParser.parse_ai_response(response)

    assert parsed["project_name"] == "HAIS"
    assert parsed["project_tasks"][0] == "Inspect current state"


def test_parser_ignores_code_braces_before_metadata_json():
    response = """
Here is an example that is not JSON:

```python
payload = {'agent': 'planner', 'retries': 2}
```

The actual machine-readable result is:
{"project_name":"HAIS","project_description":"Autonomous system","project_tasks":["Inspect repository"],"initial_files":{}}
"""

    parsed = AIResponseParser.parse_ai_response(response)

    assert parsed["project_name"] == "HAIS"
    assert parsed["project_tasks"] == ["Inspect repository"]


def test_parse_fenced_metadata_json():
    response = """
```json
{
  "project_name": "HAIS",
  "project_description": "Autonomous system",
  "project_tasks": ["Create plan"],
  "initial_files": {}
}
```
"""

    parsed = AIResponseParser.parse_ai_response(response)

    assert parsed["project_name"] == "HAIS"


def test_markdown_only_without_metadata_is_not_misparsed_as_python_dict():
    response = """
# Plan

```python
config = {'mode': 'autonomous', 'workers': 3}
```

No machine-readable metadata was returned.
"""

    assert AIResponseParser.parse_ai_response(response) is None
