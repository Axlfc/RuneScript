import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ProcessedCommand:
    prompt_content: str
    variables: Dict[str, str]
    additional_text: str


class PromptCommandHandler:
    def __init__(self, prompt_lookup):
        self.prompt_lookup = prompt_lookup

    def parse_variables(self, text: str) -> Tuple[Dict[str, str], str]:
        """
        Extract variables in the format {{var_name=value}} from text.
        Returns a tuple of (variables_dict, remaining_text)
        """
        var_pattern = r'\{\{(\w+)=(.*?)\}\}'
        matches = re.finditer(var_pattern, text)
        variables = {}
        remaining_text = text

        for match in matches:
            var_name = match.group(1)
            var_value = match.group(2)
            variables[var_name] = var_value
            remaining_text = remaining_text.replace(match.group(0), '')

        return variables, remaining_text.strip()

    def process_prompt_content(self, prompt_data: Dict[str, Any], provided_vars: Dict[str, str]) -> Optional[str]:
        """
        Process prompt content with provided variables.
        Handles variable substitution and validation.
        """
        if not prompt_data:
            return None

        content = prompt_data['content']
        required_vars = {var['name']: var for var in prompt_data.get('variables', [])}

        # Validate all required variables are provided
        missing_vars = []
        for var_name, var_info in required_vars.items():
            if var_name not in provided_vars:
                if not var_info.get('default'):
                    missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

        # Process variables
        for var_name, var_info in required_vars.items():
            value = str(provided_vars.get(var_name, var_info.get('default', '')))
            # Replace both {var_name} and {value} with value
            content = content.replace(f"{{{var_name}}}", value)
            content = content.replace(f"{{{value}}}", value)

        return content

    def process_command_string(self, text: str) -> List[ProcessedCommand]:
        """
        Process a string that may contain multiple commands and additional text.
        Returns a list of ProcessedCommand objects.
        """
        parts = text.split()
        commands: List[ProcessedCommand] = []
        current_command = None
        additional_text = []
        i = 0

        while i < len(parts):
            part = parts[i]

            if part.startswith('/'):  # New command found
                # Process any pending command
                if current_command:
                    if additional_text:
                        current_command.additional_text = ' '.join(additional_text)
                        additional_text = []
                    commands.append(current_command)
                    current_command = None

                # Start new command processing
                prompt_data = self.prompt_lookup.find_prompt_by_alias(part[1:])
                if prompt_data:
                    # Look ahead for variables
                    vars_text = ""
                    next_idx = i + 1
                    while next_idx < len(parts) and '{{' in parts[next_idx]:
                        vars_text += " " + parts[next_idx]
                        next_idx += 1

                    # Parse variables
                    variables, remaining_text = self.parse_variables(vars_text)

                    try:
                        processed_content = self.process_prompt_content(prompt_data, variables)
                        if processed_content:
                            current_command = ProcessedCommand(
                                prompt_content=processed_content,
                                variables=variables,
                                additional_text=""
                            )

                            if remaining_text:
                                additional_text.append(remaining_text)

                        i = next_idx - 1  # Will be incremented at end of loop
                    except ValueError as e:
                        raise ValueError(f"Error processing command '{part}': {str(e)}")
                else:
                    additional_text.append(part)
            else:
                additional_text.append(part)

            i += 1

        # Process final command if exists
        if current_command:
            if additional_text:
                current_command.additional_text = ' '.join(additional_text)
            commands.append(current_command)
        elif additional_text:  # Handle remaining additional text
            commands.append(ProcessedCommand(
                prompt_content="",
                variables={},
                additional_text=' '.join(additional_text)
            ))

        return commands

    def format_for_display(self, commands: List[ProcessedCommand]) -> str:
        """
        Format processed commands for display in the UI.
        """
        output = []
        for cmd in commands:
            if cmd.prompt_content:
                # Format the prompt content
                output.append(f"Command content: {cmd.prompt_content}")

                # Format variables if present
                if cmd.variables:
                    vars_str = ", ".join(f"{k}={v}" for k, v in cmd.variables.items())
                    output.append(f"Variables: {vars_str}")

                # Add additional text if present
                if cmd.additional_text:
                    output.append(f"Additional text: {cmd.additional_text}")

                output.append("-" * 40)  # Separator between commands

        return "\n".join(output)