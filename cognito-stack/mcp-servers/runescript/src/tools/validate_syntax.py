from typing import Dict, Any
from ..wrapper import RuneScriptWrapper

async def validate_syntax(wrapper: RuneScriptWrapper, script: str, language: str) -> Dict[str, Any]:
    """
    Calls the RuneScript wrapper to validate the syntax of a script.
    """
    return await wrapper.validate_syntax(script=script, language=language)
