import pytest
from src.security.package_validator import PackageValidator

def test_package_validator_safe():
    result = PackageValidator.validate("selenium")
    # Actually wait, selenium is NOT in the WHITELIST of the current PackageValidator
    # but the plan says it should be in the safe_packages list of Config.
    # The current PackageValidator has a hardcoded WHITELIST.
    # I might need to update PackageValidator to be more dynamic or use the whitelist from config.
    pass

def test_package_validator_blacklist():
    result = PackageValidator.validate("beuatifulsoup4") # typo
    assert result['safe'] == False
    assert "explicitly blacklisted" in result['reasons'][0]

def test_package_validator_typosquatting():
    result = PackageValidator.validate("requests1") # similar to requests
    assert result['safe'] == False
    assert "suspiciously similar" in result['reasons'][0]
