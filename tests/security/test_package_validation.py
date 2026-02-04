import pytest
from src.security.package_validator import PackageValidator

def test_package_blacklist():
    result = PackageValidator.validate("requsts")
    assert not result['safe']
    assert "blacklisted" in result['reasons'][0]

def test_package_typosquatting():
    result = PackageValidator.validate("beautfulsoup4")
    assert not result['safe']
    assert "suspiciously similar" in result['reasons'][0]

def test_package_whitelist_valid():
    result = PackageValidator.validate("pytest", "7.4.3")
    assert result['safe']
    assert result['allowed_version'] == "7.4.3"

def test_package_whitelist_invalid_version():
    result = PackageValidator.validate("pytest", "1.0.0")
    assert not result['safe']
    assert "version" in result['reasons'][0].lower()

def test_package_not_in_whitelist():
    result = PackageValidator.validate("some-unknown-lib")
    assert not result['safe']
    assert "not in the approved whitelist" in result['reasons'][0]
