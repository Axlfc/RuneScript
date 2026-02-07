# nIA TDD Loop Architectural Audit Report (Feb 2026)

## EXECUTIVE SUMMARY

**System Status:** **Partially Functional / Needs Stabilisation**

The nIA TDD Loop system has a solid conceptual foundation and many fully implemented core components. However, it is currently "brittle" due to widespread missing error handling in critical I/O paths and a lack of robustness in its autonomous execution loop.

**Critical Blockers Found: 2**
1.  **Initialization Order Bug:** `LoopOrchestrator` attempted to use `self.config_manager` before it was initialized (FIXED during this audit).
2.  **Rigid Validation:** `PlanValidator` and `LoopOrchestrator` critical file validation are too strict, blocking small projects or simple tasks from completing (e.g., requiring 5+ tasks and specific files like `app.py`).

**Components Status:**
-   Fully Implemented: 8/12
-   Partially Implemented: 4/12
-   Missing/Stub: 0/12 (Most planned components exist in some form)

**Test Coverage:** 26% (Critical gaps in `ProjectLifecycleManager` and `LoopOrchestrator`)
**Security Posture:** **Strong** (Sandboxing and path validation are well-integrated)

**Recommended Action:** **Fix & Ship** (Stabilize the foundation before adding "godly automation" features)

---

## COMPONENT STATUS MATRIX

| Component | Status | Tests | Gaps/Findings |
| :--- | :--- | :--- | :--- |
| **ConfigManager** | ⚠️ Partial | ❌ No | YAML structure mismatch (Flat vs Nested). |
| **FileSystemStorage** | ✅ Full | ✅ Yes | Missing file locking (low priority). |
| **NIAMetricsManager** | ✅ Full | ✅ Yes | Uses atomic writes correctly. |
| **RAMContextManager** | ✅ Full | ✅ Yes | Updates context file correctly. |
| **PatternTracker** | ✅ Full | ✅ Yes | Frequency counting implemented. |
| **RateLimitedTelemetry**| ✅ Full | ✅ Yes | Token bucket rate limiting active. |
| **LoopOrchestrator** | ⚠️ Partial | ❌ No | No unit tests; missing error handling for I/O. |
| **TDDValidator** | ⚠️ Partial | ❌ No | Logic works but relies on subprocess without timeouts. |
| **ProjectLifecycleManager**| ❌ Weak | ❌ No | Zero test coverage; direct file I/O without try/except. |
| **IssueManager** | ✅ Full | ✅ Yes | Robust issue tracking and wiki generation. |
| **SecureSandbox** | ✅ Full | ✅ Yes | Cross-platform compatibility handled. |
| **CodeSecurityAnalyzer**| ✅ Full | ✅ Yes | Permissive whitelist for tests implemented. |

---

## CRITICAL PATH ANALYSIS

### 1. Initialization Flow
-   **Trace:** `ProjectLifecycleManager` -> `LoopOrchestrator.__init__` -> Managers.
-   **Bug Found:** `config_manager` usage before initialization (FIXED).
-   **Verification:** Line-by-line audit confirmed that re-ordered initialization now follows a strict "Foundational first" (Storage/Config) then "Managers" pattern with graceful fallback.

### 2. Autonomous Loop Flow
-   **RED-GREEN-REFACTOR:** Verified via functional smoke test. Phases execute in sequence.
-   **Gap:** The loop is easily blocked by "Quality" or "Critical File" failures which trigger infinite retry-loops or early aborts for non-critical omissions.

### 3. File I/O & Safety
-   **Finding:** 20+ instances of `open()` calls without `try/except` blocks in `src/core/`.
-   **Finding:** `LoopOrchestrator._write_file` does NOT use `FileSystemStorage.write_atomic`, leading to potential partial writes for implementation code.

---

## GAP ANALYSIS (Planned vs. Actual)

1.  **ConfigManager Schema:** Planned for a nested YAML structure (`security: { ... }`), but actual implementation expects a flat YAML file for each section.
2.  **Storage Locking:** Planned but not implemented. Not critical for current single-process use case.
3.  **Test Coverage:** Planned "production-ready" status, but 74% of the core logic is currently untested.
4.  **Intelligence Integration:** Intelligence components are well-isolated and functional, but `LoopOrchestrator` only uses a fraction of the insights they provide.

---

## PERFORMANCE BASELINE

-   **Total Time (1 Iteration):** ~2.4s (Mocked AI, includes 4 retries).
-   **I/O Operations:** ~10-15 per task completion (Checkpoints, Plan updates, Metrics, RAM).
-   **Slow Operations (>1s):** None detected in logic, but `subprocess` calls lack timeouts and could hang indefinitely in real-world scenarios.

---

## PRIORITIZED FIX LIST

### **1. CRITICAL (Must fix now)**
-   [ ] **Wrap all file operations in `try/except`**: Fix the 20+ unguarded `open()` calls.
-   [ ] **Add timeouts to all `subprocess.run` calls**: Prevent system hangs during test execution or package installation.
-   [ ] **Loosen `PlanValidator` constraints**: Change `min_tasks` from 5 to 1 to support small tasks and testing.

### **2. HIGH (Next 1-2 weeks)**
-   [ ] **Implement unit tests for `LoopOrchestrator`**: Mock dependencies and verify the loop logic in isolation.
-   [ ] **Migrate `_write_file` to `storage.write_atomic`**: Ensure implementation code is never corrupted.
-   [ ] **Align ConfigManager with Nested YAMLs**: Update `manager.py` to handle the intended schema.

### **3. MEDIUM (Technical Debt)**
-   [ ] **Add file locking to `FileSystemStorage`**: Use platform-agnostic locking (fcntl/msvcrt).
-   [ ] **Refactor Intelligence into modular directory**: Move managers to `src/core/intelligence/`.

---

## FINAL RECOMMENDATION

**Option B: Fix & Ship**

The architecture is **sound** but the implementation is **unfinished**. We should not proceed with new features (like auto-docs) until the "Prioritized Fix List (Critical)" is completed and test coverage for the Orchestrator reaches at least 60%.

**Minimum Viable Path to Stability:**
1.  Apply error-handling and timeout "hardening" to all I/O and Subprocess calls.
2.  Loosen rigid validation constraints to allow smaller iterations.
3.  Add basic unit test suite for the Orchestrator.

**Once these 3 items are done, the system will be ready for further feature expansion.**
