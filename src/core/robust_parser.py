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
                try:
                    data = json.loads(match.group(1))
                    logger.debug("JSON extracted via markdown pattern")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"Markdown extraction failed: {e}")
                    continue

        # Estrategia 2: JSON directo (buscar objeto más grande)
        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end > start:
            try:
                potential_json = response[start:end]
                data = json.loads(potential_json)
                logger.debug("JSON extracted via direct search")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Direct extraction failed: {e}")

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
