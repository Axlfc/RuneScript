from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Literal

class GenerateScriptInput(BaseModel):
    """
    Input schema for the 'generate_script' tool.
    """
    language: Literal["python", "javascript", "bash"] = Field(
        ...,
        description="The programming language for the script to be generated."
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="A detailed description of the script's desired functionality."
    )

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensures the description is not just whitespace."""
        if not v.strip():
            raise ValueError("Description cannot be empty or contain only whitespace.")
        return v.strip()

class ExecuteScriptInput(BaseModel):
    """
    Input schema for the 'execute_script' tool.
    """
    script: str = Field(
        ...,
        min_length=1,
        description="The source code of the script to be executed."
    )
    language: Literal["python", "javascript"] = Field(
        ...,
        description="The programming language of the script."
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary of arguments to pass to the script."
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="The maximum execution time in seconds (1 to 300)."
    )
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="A dictionary of environment variables to set for the script's execution."
    )
