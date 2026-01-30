# Testing Guide

## Running Tests

Ensure you have the dependencies installed:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/core/test_plan_parser.py -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Test Organization

```
tests/
├── core/                      # Core module tests
│   ├── test_plan_parser.py
│   ├── test_task_tracker.py
│   ├── test_tdd_validator.py
│   ├── test_loop_orchestrator.py
│   ├── test_config.py
│   ├── test_error_handling.py
│   └── test_git_integration.py
├── cli/                       # CLI tests
│   └── test_commands.py
└── integration/               # Integration tests
    └── test_full_nia_cycle.py
```

## Coverage Goals

- Core modules: >90%
- CLI modules: >85%
- Overall: >85% (for the RGR IDE components)
