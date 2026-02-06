
import sys
import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.core.issue_manager import IssueManager
from src.core.file_structure_validator import FileStructureValidator
from src.core.quality import QualityChecker

def test_all_systems():
    print("\n" + "="*60)
    print("🧪 COMPLETE SYSTEM VALIDATION")
    print("="*60 + "\n")

    results = []

    # Test 1: File Structure Validation
    print("TEST 1: File Structure Validator")
    try:
        validator = FileStructureValidator()

        test_paths = {
            "tests/test_index.py": True,      # Should be valid via _base
            "tests/unit/test_ui.py": True,    # Should be valid via _base flexible regex
            "index.html": True,               # Valid for frontend_web
            "css/style.css": True,            # Valid for frontend_web
            "project/index.html": False,      # Invalid for frontend_web (needs auto-fix)
            "README.md": True,                # Valid via _base
            "requirements.txt": True          # Valid via _base
        }

        for path, expected in test_paths.items():
            is_valid = validator.is_valid(path, "frontend_web")
            status = "✅" if is_valid == expected else "❌"
            print(f"  {status} {path}: valid={is_valid} (expected={expected})")
            results.append(is_valid == expected)

        # Test auto-fix
        fixed_files, warnings = validator.validate_and_fix([{'path': "project/index.html"}], "frontend_web")
        is_fixed = fixed_files[0]['path'] == "index.html"
        status = "✅" if is_fixed else "❌"
        print(f"  {status} Auto-fix project/index.html -> {fixed_files[0]['path']}")
        results.append(is_fixed)

    except Exception as e:
        print(f"  ❌ Error in File Structure Test: {e}")
        results.append(False)

    # Test 2: Issue Manager
    print("\nTEST 2: Issue Manager")
    try:
        temp_dir = Path("test_temp_issues")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        mgr = IssueManager(temp_dir)

        # Test null-safe creation and validation
        issue_id = mgr.create_issue(
            category="InvalidCategory", # Should default to General
            priority="SuperHigh",        # Should default to Medium
            description=None,            # Should default
            title=None                   # Should default
        )

        assert issue_id is not None, "Issue not created"

        issues = mgr.get_issues()
        assert len(issues) == 1, f"Expected 1 issue, got {len(issues)}"
        issue = issues[0]

        title_ok = issue['title'] == "Untitled Issue"
        cat_ok = issue['category'] == "General"
        prio_ok = issue['priority'] == "Medium"
        desc_ok = issue['description'] == "No description provided"

        print(f"  {'✅' if title_ok else '❌'} Title defaulted: {issue['title']}")
        print(f"  {'✅' if cat_ok else '❌'} Category defaulted: {issue['category']}")
        print(f"  {'✅' if prio_ok else '❌'} Priority defaulted: {issue['priority']}")
        print(f"  {'✅' if desc_ok else '❌'} Description defaulted: {issue['description']}")

        results.extend([title_ok, cat_ok, prio_ok, desc_ok])

        # Test auto-fixed status
        issue_id_2 = mgr.create_issue(
            category="Quality",
            priority="Low",
            description="Auto-fixed issue",
            auto_fixed=True
        )
        issue_2 = [i for i in mgr.get_issues() if i['id'] == issue_id_2][0]
        status_ok = issue_2['status'] == "Auto-Fixed"
        print(f"  {'✅' if status_ok else '❌'} Auto-fixed status: {issue_2['status']}")
        results.append(status_ok)

        # Cleanup
        shutil.rmtree(temp_dir)

    except Exception as e:
        print(f"  ❌ Error in Issue Manager Test: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Test 3: Quality Checker (False Positives & Semantic)
    print("\nTEST 3: Quality Checker")
    try:
        checker = QualityChecker()

        # 3.1. Markdown Checkboxes
        md_content = "# Plan\n- [ ] Task 1\n- [x] Task 2"
        has_placeholder = checker.check_placeholders({"IMPLEMENTATION_PLAN.md": md_content})
        assert has_placeholder is None, f"Markdown checkboxes wrongly detected as placeholders"
        print(f"  ✅ IMPLEMENTATION_PLAN.md checkboxes ignored")
        results.append(True)

        # 3.2. Line counts should be WARNINGS now
        files = {"app.js": "console.log('hi');\n" * 5}
        tech_config = {"quality_standards": {"js": {"min_lines": 100}}}
        issues = checker.validate(files, tech_config)
        line_count_issues = [i for i in issues if i.type == "LINE_COUNT"]
        assert len(line_count_issues) > 0
        assert line_count_issues[0].severity == "WARNING"
        print(f"  ✅ Line count issues are warnings")
        results.append(True)

        # 3.3. JS Semantic completeness should be ERROR
        js_content = "console.log('hi');"
        issues = checker.validate({"app.js": js_content}, tech_config)
        js_errors = [i for i in issues if i.type == "JS_COMPLETENESS" and i.severity == "ERROR"]
        assert len(js_errors) > 0
        print(f"  ✅ JS semantic missing features are errors")
        results.append(True)

    except Exception as e:
        print(f"  ❌ Error in Quality Checker Test: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Test 4: Iteration State Consistency
    print("\nTEST 4: Iteration State")
    try:
        from src.core.iteration_state import IterationState
        state = IterationState("Test Task")

        # Register first attempt
        state.register_attempt({"tests/test_a.py": "content"}, False, "tests/test_a.py", "test_a")

        # Valid retry
        is_ok, msg = state.validate_retry_attempt({"tests/test_a.py": "new content"}, "tests/test_a.py")
        assert is_ok
        print(f"  ✅ Consistent retry accepted")
        results.append(True)

        # Invalid retry (changed filename)
        is_ok, msg = state.validate_retry_attempt({"tests/test_b.py": "content"}, "tests/test_b.py")
        assert not is_ok
        assert "Test file changed" in msg
        print(f"  ✅ Inconsistent retry (filename change) rejected")
        results.append(True)

    except Exception as e:
        print(f"  ❌ Error in Quality Checker Test: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Results
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL SYSTEMS OPERATIONAL")
        return 0
    else:
        print(f"❌ {total - passed} SYSTEMS FAILING")
        return 1

if __name__ == "__main__":
    exit(test_all_systems())
