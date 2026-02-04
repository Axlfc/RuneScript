# 🔍 nIA Edge Cases & Strategies

This document outlines strategies for handling complex development scenarios with the nIA autonomous system.

## 1. Multi-Language Projects (e.g., Frontend + Backend)
**Detection**: `SpecGenerator` identifies multiple languages/frameworks.
**Strategy**:
- `PlanGenerator` should create separate phases for each stack.
- `LoopOrchestrator` must detect the primary stack for each task to apply correct quality standards and test commands.
- Ensure cross-stack communication (e.g., API endpoints) is documented in `SPEC.md`.

## 2. Docker Integration
**Detection**: Keywords like "docker", "container", "compose".
**Strategy**:
- Include `Dockerfile` and `docker-compose.yml` generation in the early phases of the plan.
- Implement a `DockerValidator` to verify container health if Docker is available in the environment.

## 3. Persistent Databases & Migrations
**Detection**: "PostgreSQL", "MySQL", "Prisma", "Migrations".
**Strategy**:
- Tasks must include schema definition before logic implementation.
- `LoopOrchestrator` environment setup should include DB container spin-up (if using Docker) or local DB verification.
- Use `SPEC.md` to define the exact data model.

## 4. Large-Scale Projects (>50 tasks)
**Detection**: `PlanGenerator.detect_complexity` returns `very_complex` and high feature count.
**Strategy**:
- Increase `max_iterations` in `LoopOrchestrator`.
- Implement sub-plans or hierarchical planning to maintain context.
- Use the `ProjectReconstructor` to periodically verify project integrity.

## 5. Secrets Management
**Detection**: "API Key", "JWT Secret", "OAuth".
**Strategy**:
- AI must generate `.env.example` but NEVER commit real secrets to `.env`.
- `NIA_PROMPT.md` should instruct the AI to use environment variables for all sensitive configuration.

## 6. External API Dependencies
**Detection**: "Stripe", "Twilio", "AWS".
**Strategy**:
- AI should implement mock services or use sandbox/test keys if provided.
- Tests must use mocking libraries (e.g., `unittest.mock` in Python) to avoid real API calls during TDD.
