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
5. Identify external dependencies like PostgreSQL, Redis, or Docker and include them in the 'features' or 'success_criteria' if relevant to the architecture.
6. Specify if a virtual environment (venv) or specific dependency manager (bundler, cargo, go mod) is required.
"""

PLAN_SYSTEM_PROMPT = """
You are an elite software architect.
Given a project specification, generate a COMPREHENSIVE and DETAILED implementation plan in JSON format.

CRITICAL REQUIREMENTS:
1. NO PLACEHOLDERS: Do NOT use "..." or "(rest of plan)" or "(remaining tasks)". Generate ALL tasks explicitly.
2. COMPLETENESS: Aim for a detailed breakdown.
   - Simple: min 5 tasks.
   - Medium: min 10 tasks.
   - Complex: min 15 tasks.
   - Very Complex: min 20 tasks.
3. TDD PRINCIPLES: Each task MUST follow the format: "Test: [test description]. Implementation: [impl description]".
4. PRODUCTION-READY CODE: Every task must result in complete, functional code. No stubs, no "Create folder" tasks. Tasks must combine structure with content.
5. NO BLOAT/WRONG TECH: Stick strictly to the detected tech stack. Do not use build tools (Vite, npm) if not part of the stack.
6. QUALITY TASKS: Each task description must be at least 50 characters long and describe a meaningful feature.
7. COMPREHENSIVE COVERAGE: Ensure all critical files (HTML, CSS, JS, backend logic, tests) are covered by dedicated tasks.

{tech_info}

JSON format:
{{
    "phases": [
        {{
            "name": "Phase Name",
            "tasks": [{{ "description": "Test: [test description]. Implementation: [impl description]" }}]
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

def get_plan_system_prompt(tech_info: str = "", complexity: str = "medium") -> str:
    info_str = f"TECH STACK DETAILS:\n{tech_info}\nPROJECT COMPLEXITY: {complexity.upper()}" if tech_info else f"PROJECT COMPLEXITY: {complexity.upper()}"
    return PLAN_SYSTEM_PROMPT.format(tech_info=info_str.replace('{', '{{').replace('}', '}}'))

REVIEWER_PROMPT = """
Eres un arquitecto de software experto revisando un plan de implementación.

SOLICITUD ORIGINAL:
{user_request}

TECH STACK DETECTADO:
{tech_stack}

ESPECIFICACIÓN GENERADA:
{spec_content}

PLAN DE IMPLEMENTACIÓN PROPUESTO:
{current_plan}

TAREA: Realiza una revisión crítica respondiendo:

1. CONSISTENCIA TECNOLÓGICA: ¿El plan utiliza las herramientas del TECH STACK DETECTADO? RECHAZA el plan si intenta usar herramientas ajenas al stack.
2. EVITAR STUBS/PLACEHOLDERS: ¿El plan tiene tareas incompletas o usa "..."? RECHAZA si no es 100% explícito.
3. SIN TAREAS DE SOLO ESTRUCTURA: RECHAZA si hay tareas que solo dicen "Crear carpeta x" o "Crear index.html" sin implementar lógica real.
4. COMPLETITUD: ¿El plan cumple TODOS los requisitos de la SOLICITUD ORIGINAL?
5. CALIDAD TDD: ¿Cada tarea tiene un test claro y una implementación funcional?
6. ARCHIVOS ESENCIALES: ¿Se incluyen .gitignore, README, requirements.txt/Gemfile/Cargo.toml según corresponda?

Responde EXCLUSIVAMENTE en JSON con este formato:
{{
  "approved": true/false,
  "issues_found": ["issue1", "issue2"],
  "missing_requirements": ["req1", "req2"],
  "improved_plan": {{
      "phases": [
          {{
              "name": "Phase Name",
              "tasks": [{{ "description": "Test: [test]. Implementation: [impl]" }}]
          }}
      ]
  }}
}}

Si approved=false, genera un improved_plan que sea exhaustivo, sin placeholders y 100% funcional.
"""

def get_reviewer_prompt(user_request: str, spec_content: str, current_plan: str, tech_stack: str = "unknown") -> str:
    def safe_escape(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.replace('{', '{{').replace('}', '}}')

    return REVIEWER_PROMPT.format(
        user_request=safe_escape(user_request),
        spec_content=safe_escape(spec_content),
        current_plan=safe_escape(current_plan),
        tech_stack=safe_escape(tech_stack)
    )

NIA_ITERATION_PROMPT = """
{prompt}

{test_instructions}

## MANDATORY QUALITY STANDARDS
1. 💎 PRODUCTION CODE: Write full implementations. NO STUBS. NO PLACEHOLDERS.
2. 🚫 NO TRUNCATION: Do NOT use "..." or "// rest of code". Generate the ENTIRE file every time.
3. 🛠️ FUNCTIONAL LOGIC: Implement real business logic, not just UI skeletons.
4. 📏 MINIMUM LENGTH:
   - HTML files should be 150+ lines.
   - CSS files should be 200+ lines.
   - JS/Python/Ruby/Go/Rust files should be 100+ lines of real logic.
5. 🧪 TDD ADHERENCE: Follow the RED-GREEN-REFACTOR cycle strictly.

=== CURRENT SPEC ===
{spec}

=== CURRENT PLAN ===
{plan}

=== AGENT GUIDELINES (AGENTS.md) ===
{agents_rules}

=== CURRENT CONTEXT (FILES) ===
{context}

=== RAM CONTEXT ===
{ram_context}

=== NEXT TASK ===
{task_description}

Example of GOOD implementation:
File: js/app.js
```javascript
// Full implementation of the feature
function initApp() {{
    console.log("App starting...");
    const elements = document.querySelectorAll('.item');
    elements.forEach(el => {{
        el.addEventListener('click', () => {{
            // Real logic here, at least 100 lines total
        }});
    }});
}}
initApp();
// ... more real code ...
```

Example of BAD implementation:
File: js/app.js
```javascript
// TODO: Implement this later
// ...
```

Please complete this task now.
Specify filenames as 'File: path/to/file' OR use a JSON response with a "files" array:
{{
  "files": [
    {{"path": "path/to/file", "content": "..."}}
  ]
}}

### 🧪 TEST WRITING GUIDELINES
When generating tests (especially for frontend):
- **NEVER use `requests.get()` for local files**: Tests run in a restricted sandbox without a web server. To test HTML/CSS files, read them directly from the disk.
  - ❌ BAD: `response = requests.get('index.html')`
  - ✅ GOOD: `with open('index.html', 'r', encoding='utf-8') as f: html_content = f.read()`
- **Use BeautifulSoup with local content**:
  ```python
  with open('index.html', 'r', encoding='utf-8') as f:
      soup = BeautifulSoup(f.read(), 'html.parser')
  ```
- **ROBUST PATHS**: Use `.endswith()` or normalized paths when checking `href` or `src`.
  - BAD: `assert link['href'] == 'css/style.css'`
  - GOOD: `assert 'css/style.css' in link['href']` or `assert link['href'].endswith('css/style.css')`
- **DESCRIPTIVE ERRORS**: Always include helpful messages in assertions.
  - GOOD: `assert soup.find(id="main"), "CRITICAL: Element with id='main' is missing from index.html"`

### 🚫 COMMON MISTAKES TO AVOID
- **NO SYNTAX ERRORS IN ASSERTIONS**:
  - ❌ BAD: `assert soup, soup.find(id='skills'), "Message"` (Syntax Error: invalid syntax)
  - ✅ GOOD: `assert soup.find(id='skills'), "Message"`
- **ONE ASSERTION PER CHECK**: Don't chain multiple elements in a single `assert` if it breaks syntax.

### 💎 PRODUCTION CODE STANDARDS
- **NO STUBS**: Every file must be fully functional. No "TODO" comments in place of logic.
- **MANDATORY LENGTH**:
  - HTML: 150+ lines of content-rich structure (navigation, hero, features, footer, etc.).
  - CSS: 200+ lines of detailed, modern styling (variables, flexbox/grid, animations, responsive design).
  - JS: 100+ lines of interactive logic (event listeners, state management, UI updates).
- **COMPLETE SETS**: If the task involves a UI component, you MUST provide the HTML, the CSS, and the JS in the SAME response.

CRITICAL: If using JSON, escape all special characters properly:
- Use \\n for newlines
- Use \\t for tabs
- Use \\" for quotes inside strings
- Use \\\\ for backslashes

GENERATE COMPLETE, PRODUCTION-READY CODE NOW.
"""

def get_nia_iteration_prompt(prompt: str, test_instructions: str, spec: str, plan: str, context: str, task_description: str, ram_context: str = "", agents_rules: str = "") -> str:
    """
    Generates the full prompt for a nIA iteration, ensuring all dynamic content
    is safely escaped for f-string/format curly braces.
    """
    def safe_escape(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.replace('{', '{{').replace('}', '}}')

    # ram_context is expected to be already wrapped and escaped by PromptFilter,
    # but we'll be extra safe if it's not.
    # Actually, if PromptFilter already escaped it, doubling it again would be wrong
    # IF we want the braces to remain as literals in the final prompt.
    # PromptFilter returns wrapped content with {{ }}.
    # .format() will turn {{ }} into { }. Correct.

    return NIA_ITERATION_PROMPT.format(
        prompt=safe_escape(prompt),
        test_instructions=safe_escape(test_instructions),
        spec=safe_escape(spec),
        plan=safe_escape(plan),
        agents_rules=safe_escape(agents_rules),
        context=safe_escape(context),
        task_description=safe_escape(task_description),
        ram_context=ram_context # Already escaped by PromptFilter
    )
