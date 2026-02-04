import difflib
from .exceptions import PackageValidationError

class PackageValidator:
    """Paranoid package security validation."""

    # Curated whitelist of known-safe packages and versions
    # In a real scenario, this would include SHA256 hashes
    WHITELIST = {
        'beautifulsoup4': {
            'allowed_versions': ['4.9.3', '4.10.0', '4.11.1', '4.12.0', '4.12.1', '4.12.2', '4.12.3'],
            'latest_safe': '4.12.3'
        },
        'pytest': {
            'allowed_versions': ['7.0.1', '7.1.2', '7.2.0', '7.3.1', '7.4.0', '7.4.3', '8.0.0'],
            'latest_safe': '8.0.0'
        },
        'lxml': {
            'allowed_versions': ['4.9.1', '4.9.2', '4.9.3', '5.1.0'],
            'latest_safe': '5.1.0'
        },
        'requests': {
            'allowed_versions': ['2.28.1', '2.31.0'],
            'latest_safe': '2.31.0'
        },
        'numpy': {
            'allowed_versions': ['1.24.0', '1.25.0', '1.26.0', '1.26.4'],
            'latest_safe': '1.26.4'
        },
        'pandas': {
            'allowed_versions': ['2.0.0', '2.1.0', '2.2.0'],
            'latest_safe': '2.2.0'
        },
        'flask': {
            'allowed_versions': ['2.3.0', '3.0.0', '3.0.2'],
            'latest_safe': '3.0.2'
        },
        'django': {
            'allowed_versions': ['4.2.0', '5.0.0', '5.0.2'],
            'latest_safe': '5.0.2'
        }
    }

    BLACKLIST = {
        'requsts', 'beuatifulsoup4', 'numppy', 'pandsa',
        'requsets', 'beautifulsoup', 'djago', 'flaks',
        'py-spy', 'crypto-miner', 'reverse-shell'
    }

    @classmethod
    def validate(cls, package_name: str, version: str = None):
        """
        Validate package safety.
        Returns a dict with 'safe', 'reasons', and 'allowed_version'.
        """
        package_name = package_name.lower().strip()

        # 1. Blacklist check
        if package_name in cls.BLACKLIST:
            return {
                'safe': False,
                'reasons': [f"Package '{package_name}' is explicitly blacklisted"],
                'risk_score': 100
            }

        # 2. Typosquatting check
        similar = cls._find_similar_packages(package_name)
        if similar:
            return {
                'safe': False,
                'reasons': [f"Package '{package_name}' is suspiciously similar to whitelisted: {similar}"],
                'risk_score': 80
            }

        # 3. Whitelist check
        if package_name not in cls.WHITELIST:
            return {
                'safe': False,
                'reasons': [f"Package '{package_name}' is not in the approved whitelist"],
                'risk_score': 70
            }

        package_info = cls.WHITELIST[package_name]

        # 4. Version check
        if version:
            if version not in package_info['allowed_versions']:
                return {
                    'safe': False,
                    'reasons': [f"Version {version} of {package_name} is not in the approved list"],
                    'risk_score': 60,
                    'suggested_version': package_info['latest_safe']
                }
            allowed_version = version
        else:
            allowed_version = package_info['latest_safe']

        return {
            'safe': True,
            'reasons': [],
            'risk_score': 0,
            'allowed_version': allowed_version
        }

    @staticmethod
    def _find_similar_packages(name: str):
        """Detect potential typosquatting."""
        whitelisted = ['beautifulsoup4', 'pytest', 'lxml', 'requests', 'numpy', 'pandas', 'django', 'flask']
        similar = []
        for legit in whitelisted:
            if name == legit:
                continue
            ratio = difflib.SequenceMatcher(None, name, legit).ratio()
            if ratio > 0.8:
                similar.append(legit)
        return similar
