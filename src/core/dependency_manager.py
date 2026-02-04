import subprocess
import logging
import os
from src.security.package_validator import PackageValidator
from src.security.exceptions import SecurityException


class DependencyManagementUnit:
    def __init__(self, project_path, security_auditor=None):
        self.project_path = project_path
        self.security_auditor = security_auditor

    def install_dependencies(self, dependencies):
        for dep in dependencies:
            # Parse dependency (simple name only for now)
            dep_name = dep.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
            dep_version = None
            if '==' in dep:
                dep_version = dep.split('==')[1].strip()

            validation = PackageValidator.validate(dep_name, dep_version)

            if not validation['safe']:
                msg = f"Security Violation: Blocked installation of unsafe package '{dep}': {validation['reasons']}"
                logging.error(msg)
                if self.security_auditor:
                    self.security_auditor.log_security_violation(
                        severity='HIGH',
                        category='UNSAFE_PACKAGE_BLOCKED',
                        description=msg,
                        package=dep_name,
                        version=dep_version
                    )
                continue

            target_dep = f"{dep_name}=={validation['allowed_version']}" if validation.get('allowed_version') else dep

            try:
                # Use --break-system-packages as required in this environment
                subprocess.run(["pip", "install", target_dep, "--break-system-packages"], check=True)
                if self.security_auditor:
                    self.security_auditor.log_package_install(dep_name, validation.get('allowed_version'), approved=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install dependency: {dep}: {e}")

    def save_requirements(self, dependencies):
        req_path = os.path.join(self.project_path, "requirements.txt")
        with open(req_path, "w", encoding='utf-8') as f:
            for dep in dependencies:
                f.write(f"{dep}\n")

