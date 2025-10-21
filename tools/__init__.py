from .base import CLIResult, ToolResult
from .bash import BashTool20241022, BashTool20250124
from .collection import ToolCollection
from .computer import ComputerTool
from .edit import EditTool20241022, EditTool20250124
#from .groups import TOOL_GROUPS_BY_VERSION, ToolVersion

# Default aliases to latest versions
BashTool = BashTool20250124  # Latest bash tool
EditTool = EditTool20250124  # Latest text editor tool

__ALL__ = [
    BashTool,
    BashTool20241022,
    BashTool20250124,
    CLIResult,
    ComputerTool,
    EditTool,
    EditTool20241022,
    EditTool20250124,
    ToolCollection,
    ToolResult,
]