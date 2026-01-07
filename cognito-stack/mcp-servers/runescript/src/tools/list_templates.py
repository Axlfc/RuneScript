from typing import List, Dict
from ..wrapper import RuneScriptWrapper

async def list_templates(wrapper: RuneScriptWrapper) -> List[Dict[str, str]]:
    """
    Calls the RuneScript wrapper to list available code templates.
    """
    return await wrapper.list_templates()
