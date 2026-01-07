from typing import Dict, Any
from ..wrapper import RuneScriptWrapper
from ..schemas.tool_schemas import ExecuteScriptInput

async def execute_script(wrapper: RuneScriptWrapper, **kwargs) -> Dict[str, Any]:
    """
    Calls the RuneScript wrapper to execute a script.
    """
    validated_input = ExecuteScriptInput(**kwargs)
    return await wrapper.execute_script(
        script=validated_input.script,
        language=validated_input.language,
        args=validated_input.args,
        timeout=validated_input.timeout,
    )
