from ..wrapper import RuneScriptWrapper
from ..schemas.tool_schemas import GenerateScriptInput

async def generate_script(wrapper: RuneScriptWrapper, **kwargs) -> str:
    """
    Calls the RuneScript wrapper to generate a script based on a description.
    """
    validated_input = GenerateScriptInput(**kwargs)
    return await wrapper.generate_script(
        language=validated_input.language,
        description=validated_input.description
    )
