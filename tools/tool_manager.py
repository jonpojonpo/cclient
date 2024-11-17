# tools/tool_manager.py
from typing import Dict, Any, List
from pathlib import Path
import asyncio

from rich.console import Console
from rich.panel import Panel
from anthropic.types.beta import BetaToolUseBlock

from .base import BaseAnthropicTool, ToolResult, ToolError, CLIResult
from .bash import BashTool  # Using Anthropic's BashTool

class ToolManager:
    """Manages tool registration, execution, and output handling."""
    
    def __init__(self, console: Console):
        self.tools: Dict[str, BaseAnthropicTool] = {}
        self.console = console
        self._tool_results: Dict[str, ToolResult] = {}

    def register_tool(self, name: str, tool: BaseAnthropicTool) -> None:
        """Register a tool with the manager."""
        self.tools[name] = tool

    def get_tool_configs(self) -> List[Dict[str, Any]]:
        """Get tool configurations for Claude API."""
        return [tool.to_params() for tool in self.tools.values()]

    async def handle_tool(self, tool_block: BetaToolUseBlock) -> None:
        """Handle tool execution and output display."""
        tool_name = tool_block.name
        tool_id = tool_block.id
        
        if tool_name not in self.tools:
            raise ToolError(f"Unknown tool: {tool_name}")

        # Show tool invocation
        self.console.print(Panel(
            f"[bold]Command:[/bold] {tool_block.input}",
            title=f"[yellow]Using {tool_name}[/yellow]",
            border_style="yellow"
        ))

        try:
            # Execute tool
            tool = self.tools[tool_name]
            # All tools are now called with await since they're async
            result = await tool(**tool_block.input)

            # Store result
            self._tool_results[tool_id] = result

            # Display result
            await self._display_tool_result(result, tool_name)

        except Exception as e:
            error_result = ToolResult(error=str(e))
            self._tool_results[tool_id] = error_result
            self.console.print(Panel(
                f"[bold red]Error:[/bold red] {str(e)}",
                title="Tool Error",
                border_style="red"
            ))

    async def _display_tool_result(self, result: ToolResult, tool_name: str) -> None:
        """Display tool result with appropriate formatting."""
        if result.system:
            self.console.print(f"[dim]{result.system}[/dim]")

        if result.output:
            self.console.print(Panel(
                result.output,
                title=f"[yellow]{tool_name} Output[/yellow]",
                border_style="yellow"
            ))

        if result.error:
            self.console.print(Panel(
                result.error,
                title="[red]Error[/red]",
                border_style="red"
            ))

    def get_tool_result(self, tool_id: str) -> ToolResult:
        """Get result from a previous tool execution."""
        return self._tool_results.get(tool_id, ToolResult())

    def clear_results(self) -> None:
        """Clear stored tool results."""
        self._tool_results.clear()