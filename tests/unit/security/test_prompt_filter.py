import pytest
from src.security.prompt_filter import PromptFilter

def test_prepare_context():
    filter = PromptFilter()
    content = "<script>alert('xss')</script>"
    result = filter.prepare_context("ram_context", content)

    assert "<ram_context>" in result
    assert "</ram_context>" in result
    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
