import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.core.issue_manager import IssueManager
from src.core.file_structure_validator import FileStructureValidator
from pathlib import Path
import json

def test_structure_error_tracking():
    """Test que errors d'estructura es documenten correctament"""

    # Setup
    test_project = Path("test_projects/structure_test")
    test_project.mkdir(parents=True, exist_ok=True)

    issue_mgr = IssueManager(test_project)
    validator = FileStructureValidator(issue_mgr)

    # Simulate LLM generating wrong paths
    wrong_files = [
        {"path": "project/index.html", "content": "..."},
        {"path": "project/css/style.css", "content": "..."},
        {"path": "src/js/app.js", "content": "..."}
    ]

    print("=" * 60)
    print("TEST: Structure Validation & Issue Tracking")
    print("=" * 60)

    # Validate & fix
    fixed_files, warnings = validator.validate_and_fix(wrong_files, "frontend_web")

    print(f"\n✅ Auto-fixed {len(warnings)} files:")
    for w in warnings:
        print(f"  - {w}")

    # Verify fixed paths
    assert fixed_files[0]['path'] == "index.html"
    assert fixed_files[1]['path'] == "css/style.css"
    assert fixed_files[2]['path'] == "js/app.js"
    print("\n✅ All paths corrected successfully")

    # Check issues created
    issues = issue_mgr.get_issues(status="Open")
    print(f"\n📋 Issues created: {len(issues)}")
    for issue in issues:
        print(f"  - [{issue['priority']}] {issue['title']}")
        print(f"    Category: {issue['category']}")
        print(f"    Auto-fixed: {issue.get('auto_fixed', False)}")

    # Simulate resolution
    for issue in issues:
        issue_mgr.resolve_issue(issue['id'], "Auto-correction successful")

    print("\n✅ Issues resolved")

    # Check Wiki generation
    issue_mgr.generate_wiki()
    wiki_path = test_project / ".nia" / "wiki"
    troubleshooting = wiki_path / "Troubleshooting.md"
    changelog = wiki_path / "Changelog.md"

    if troubleshooting.exists():
        print(f"\n📖 Troubleshooting.md generated:")
        print(troubleshooting.read_text()[:500] + "...")
    else:
        print("\n❌ Troubleshooting.md NOT generated")
        sys.exit(1)

    if changelog.exists():
        print(f"\n📝 Changelog.md generated:")
        print(changelog.read_text()[:500] + "...")
    else:
        print("\n❌ Changelog.md NOT generated")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

    # Cleanup
    import shutil
    shutil.rmtree(test_project)

def test_critical_error_escalation():
    """Test que errors crítics s'escalen correctament"""

    test_project = Path("test_projects/critical_test")
    test_project.mkdir(parents=True, exist_ok=True)

    issue_mgr = IssueManager(test_project)

    # Simulate critical file write failure
    issue_mgr.create_issue(
        title="Physical file verification failed",
        category="FileSystem",
        priority="Critical",
        description="Files not found after write: index.html, css/style.css",
        context={
            "missing_files": ["index.html", "css/style.css"],
            "attempt": 3,
            "tech_stack": "frontend_web"
        }
    )

    # Get suggestions
    suggestions = issue_mgr.get_suggestions("Physical file verification failed")

    print("\n🔍 Suggestions for critical error:")
    for i, sugg in enumerate(suggestions, 1):
        print(f"\n{i}. {sugg}")

    # Cleanup
    import shutil
    shutil.rmtree(test_project)

if __name__ == "__main__":
    print("\n🧪 Starting Issue System Validation...\n")

    test_structure_error_tracking()
    test_critical_error_escalation()

    print("\n✅ All validation tests completed successfully!")
