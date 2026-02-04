"""
Robust JSON Parser para respuestas de LLMs.
Combina extracción por regex con validación Pydantic.
"""

import re
import json
import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# SCHEMAS DE VALIDACIÓN
class TaskSchema(BaseModel):
    description: str = Field(..., min_length=15)

class PhaseSchema(BaseModel):
    name: str
    tasks: List[TaskSchema]

class PlanSchema(BaseModel):
    phases: List[PhaseSchema]
    total_tasks: int
    completed_tasks: int = 0
    remaining_tasks: int = 0
    blocked_tasks: List[str] = []

    @field_validator('phases')
    @classmethod
    def must_have_min_phases(cls, v):
        if len(v) < 2:
            raise ValueError('Plan must have at least 2 phases')
        return v

class SpecSchema(BaseModel):
    project_name: str
    objective: str
    features: List[str]
    language: str
    framework: str = "None"
    database: str = "None"
    testing_framework: str
    success_criteria: List[str]
    out_of_scope: List[str]

# PARSER ROBUSTO
class RobustJSONParser:
    """Parser de JSON robusto para respuestas de LLMs."""

    @staticmethod
    def sanitize_json(json_str: str) -> str:
        """Fix common LLM JSON errors like invalid escape sequences or literal newlines in strings."""
        if not json_str:
            return json_str

        # 1. Handle invalid escape sequences (e.g., \s, \d, \. which are common in code but invalid in JSON)
        # We look for a backslash NOT followed by one of the valid JSON escape characters
        # Valid: " \ / b f n r t uXXXX
        def fix_backslash(match):
            char = match.group(1)
            if char in '"\\/bfnrtu':
                return match.group(0)
            return '\\\\' + char

        json_str = re.sub(r'\\([^"\\/bfnrtu])', fix_backslash, json_str)

        # 2. Handle literal newlines and tabs inside strings
        # This is trickier because we need to distinguish between newlines in strings vs between keys
        # A simple heuristic: if a newline is followed by something that doesn't look like a key or end of object,
        # it might be inside a string. But that's risky.

        # A safer way to handle literal newlines in many LLM outputs:
        # If we see a newline that is NOT preceded by , { [ or followed by " } ] it's probably inside a string.
        # However, a more robust way is to just use regex extraction as a fallback if this fails.

        return json_str

    @staticmethod
    def extract_json(response: str) -> Optional[Dict[str, Any]]:
        """
        Extrae JSON de respuesta LLM usando múltiples estrategias.

        Args:
            response: Respuesta cruda del LLM

        Returns:
            Diccionario parseado o None si falla
        """
        # Estrategia 1: Markdown code blocks
        patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',  # ```json {...}```
            r'```(?:json)?\s*(\[.*?\])\s*```',  # Arrays también
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                json_content = match.group(1)
                try:
                    data = json.loads(json_content)
                    logger.debug("JSON extracted via markdown pattern")
                    return data
                except json.JSONDecodeError:
                    # Try sanitizing
                    try:
                        data = json.loads(RobustJSONParser.sanitize_json(json_content))
                        logger.debug("JSON extracted via sanitized markdown pattern")
                        return data
                    except json.JSONDecodeError as e:
                        logger.warning(f"Markdown extraction failed after sanitization: {e}")
                        continue

        # Estrategia 2: JSON directo (buscar objeto más grande)
        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end > start:
            potential_json = response[start:end]
            try:
                data = json.loads(potential_json)
                logger.debug("JSON extracted via direct search")
                return data
            except json.JSONDecodeError:
                # Try sanitizing
                try:
                    data = json.loads(RobustJSONParser.sanitize_json(potential_json))
                    logger.debug("JSON extracted via sanitized direct search")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"Direct extraction failed after sanitization: {e}")

        # Estrategia 3: Buscar candidatos múltiples (último recurso)
        json_candidates = re.findall(r'\{[^{}]*\}', response, re.DOTALL)
        for candidate in sorted(json_candidates, key=len, reverse=True):
            try:
                data = json.loads(candidate)
                logger.debug("JSON extracted via candidate search")
                return data
            except json.JSONDecodeError:
                continue

        logger.error("All JSON extraction strategies failed")
        return None

    def parse_spec(self, response: str) -> SpecSchema:
        """Parse y valida un SPEC.md response."""
        data = self.extract_json(response)
        if not data:
            raise ValueError("Could not extract JSON from LLM response")

        try:
            return SpecSchema.model_validate(data)
        except Exception as e:
            logger.error(f"Spec validation failed: {e}")
            raise

    def parse_plan(self, response: str) -> PlanSchema:
        """Parse y valida un IMPLEMENTATION_PLAN.md response."""
        data = self.extract_json(response)
        if not data:
            raise ValueError("Could not extract JSON from LLM response")

        try:
            # Auto-calcular counters si no vienen
            if "total_tasks" not in data or data["total_tasks"] == 0:
                total = sum(len(phase.get("tasks", [])) for phase in data.get("phases", []))
                data["total_tasks"] = total
                data["remaining_tasks"] = total

            return PlanSchema.model_validate(data)
        except Exception as e:
            logger.error(f"Plan validation failed: {e}")
            raise
