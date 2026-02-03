"""
Centralized templates for LLM prompts to avoid f-string pitfalls and improve maintainability.
"""

SPEC_SYSTEM_PROMPT = """
You are an expert system architect.
Given a project idea, generate a structured project specification in JSON format.
Include: project_name, objective, features (list), language, framework, database, testing_framework, success_criteria (list), out_of_scope (list).

System Context:
- Python is available: {python_avail} (at {python_path})
- Node.js is available: {node_avail}
- npm is available: {npm_avail}

Guidelines for Tech Stack Selection:
1. If it is a frontend project (HTML/CSS/JS) and Node.js is NOT available, use 'Python scripts (BeautifulSoup, lxml)' for testing_framework and 'HTML/CSS/JavaScript' for language.
2. If it is a Python project, use 'pytest' for testing_framework.
3. If it is a Node.js project and npm is available, use 'jest' or 'mocha'.
4. Always prefer tools that are marked as available in the System Context.
"""

PLAN_SYSTEM_PROMPT = """
You are an elite developer.
Given a project specification, generate a detailed implementation plan in JSON format.
Break it down into PHASES. Each phase should have a list of tasks.
Each task should be specific and follow TDD principles (Test: description).
Ensure the tasks align with the chosen 'Testing' framework in the specification.

{tech_info}

JSON format:
{{
    "phases": [
        {{
            "name": "Phase Name",
            "tasks": [{{ "description": "Task description" }}]
        }}
    ],
    "total_tasks": 0,
    "completed_tasks": 0,
    "remaining_tasks": 0,
    "blocked_tasks": []
}}
"""

def get_spec_system_prompt(tools: dict) -> str:
    return SPEC_SYSTEM_PROMPT.format(
        python_avail=tools.get('python', False),
        python_path=tools.get('python_path', 'unknown'),
        node_avail=tools.get('node', False),
        npm_avail=tools.get('npm', False)
    )

def get_plan_system_prompt(tech_info: str = "") -> str:
    info_str = f"TECH STACK DETAILS:\n{tech_info}" if tech_info else ""
    return PLAN_SYSTEM_PROMPT.format(tech_info=info_str)

REVIEWER_PROMPT = """
Eres un arquitecto de software experto revisando un plan de implementación.

SOLICITUD ORIGINAL:
{user_request}

ESPECIFICACIÓN GENERADA:
{spec_content}

PLAN DE IMPLEMENTACIÓN PROPUESTO:
{current_plan}

TAREA: Realiza una revisión crítica respondiendo:

1. COMPLETITUD: ¿El plan cumple TODOS los requisitos? Lista lo que falta.
2. CALIDAD: ¿Las tareas generarán código profesional o solo stubs básicos?
3. GRANULARIDAD: ¿Las tareas son demasiado grandes o pequeñas?
4. ARCHIVOS: ¿Faltan requirements.txt, .gitignore u otros archivos esenciales?
5. TESTS: ¿Los tests verifican funcionalidad real o solo existencia de archivos?

Responde EXCLUSIVAMENTE en JSON con este formato:
{{
  "approved": true/false,
  "issues_found": ["issue1", "issue2"],
  "missing_requirements": ["req1", "req2"],
  "improved_plan": {{
      "phases": [
          {{
              "name": "Phase Name",
              "tasks": [{{ "description": "Task description" }}]
          }}
      ]
  }}
}}

Si approved=false, genera un improved_plan que resuelva todos los issues. El plan debe ser detallado y seguir principios TDD.
"""

def get_reviewer_prompt(user_request: str, spec_content: str, current_plan: str) -> str:
    return REVIEWER_PROMPT.format(
        user_request=user_request,
        spec_content=spec_content,
        current_plan=current_plan
    )

NIA_ITERATION_PROMPT = """
{prompt}

{test_instructions}

## QUALITY STANDARDS
1. ✅ DO: Write production-quality code, not stubs.
2. ✅ DO: Include actual content, not placeholders like "Content here" or "...".
3. ✅ DO: Implement all features mentioned in the task in detail.
4. ❌ DON'T: Leave empty functions or TODO comments.
5. ❌ DON'T: Create minimal code just to pass tests.
   - A professional implementation of a UI component should typically be 50-100+ lines including styles and logic.

=== CURRENT SPEC ===
{spec}

=== CURRENT PLAN ===
{plan}

=== CURRENT CONTEXT (FILES) ===
{context}

=== NEXT TASK ===
{task_description}

Please complete this task following the RED-GREEN-REFACTOR cycle.
Always specify the filename before each code block using 'File: path/to/file' format.
GENERATE COMPLETE, PRODUCTION-READY CODE NOW.
"""

def get_nia_iteration_prompt(prompt: str, test_instructions: str, spec: str, plan: str, context: str, task_description: str) -> str:
    return NIA_ITERATION_PROMPT.format(
        prompt=prompt,
        test_instructions=test_instructions,
        spec=spec,
        plan=plan,
        context=context,
        task_description=task_description
    )
