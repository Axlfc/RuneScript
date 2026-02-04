# nIA Incident Response Playbook

This document outlines the procedures for responding to security incidents within the nIA autonomous system.

## 🟢 Phase 1: Preparation
- Ensure `SecurityAuditor` is active and logging to `.nia/security/`.
- Maintain a clean baseline of the system using Git checkpoints.
- Regularly review security logs for anomalies.

## 🟡 Phase 2: Detection & Analysis
### Indicators of Compromise (IoC)
- 🚨 `SECURITY ALERT` in console output.
- Non-zero exit codes in tests with "Security Violation" messages.
- Unexpected files appearing in the project directory.
- High CPU/Memory usage by child processes (detected by sandbox).

### Analysis Steps
1. Inspect `.nia/security/security_violations.jsonl`.
2. Extract the malicious payload from `code_execution.jsonl`.
3. Verify if the attack was successful or blocked by the sandbox.

## 🟠 Phase 3: Containment
- **Automated:** The sandbox will kill processes exceeding time/memory limits.
- **Manual:** Kill any suspicious python processes: `pkill -f "sandboxed_code.py"`.
- **Isolation:** Delete the compromised project directory.

## 🔴 Phase 4: Eradication
- Identify the prompt injection or AI failure that led to the attack.
- Update `src/security/` components to block the specific attack vector.
- Add the malicious pattern to `CodeSecurityAnalyzer.SUSPICIOUS_PATTERNS`.

## 🔵 Phase 5: Recovery
- Restore the project from the last known safe Git checkpoint.
- Re-run all security tests to ensure the environment is safe.
- Resume operations with enhanced monitoring.

## ⚪ Phase 6: Post-Incident Activity
- Document the incident in the security log.
- Perform a technical review of the bypass.
- Share lessons learned with the engineering team.
