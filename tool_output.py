# tool_output.py
from typing import Any, Dict
import asyncio
from pathlib import Path

from .output_manager import OutputManager

class ToolOutputHandler:
    """Handles tool output processing and display."""
    
    def __init__(self, output_manager: OutputManager):
        self.output = output_manager
        self._last_file_contents: Dict[str, str] = {}

    async def handle_bash(self, command: str) -> None:
        """Handle bash command output in real-time."""
        self.output.console.print(Panel(
            f"[bold]$ {command}[/bold]",
            title="Bash Command",
            border_style="yellow"
        ))
        
        await self.output.stream_bash_output(command)

    async def handle_editor(self, command: str, path: str, 
                          params: Dict[str, Any]) -> None:
        """Handle editor command output with syntax highlighting."""
        if command == "view":
            with open(path) as f:
                content = f.read()
            
            view_range = params.get("view_range")
            if view_range:
                start_line, end_line = view_range
            else:
                start_line = end_line = None
                
            self.output.display_file_content(
                content, Path(path).name,
                start_line, end_line
            )
            
        elif command in ["create", "str_replace", "insert"]:
            # Store previous content for diff
            if path in self._last_file_contents:
                old_content = self._last_file_contents[path]
            else:
                old_content = ""
                
            # Get new content
            with open(path) as f:
                new_content = f.read()
                
            # Show diff
            self.output.display_diff(old_content, new_content, Path(path).name)
            
            # Update stored content
            self._last_file_contents[path] = new_content

    def handle_art_command(self, text: str, style: str = "random",
                          art_type: str = "figlet") -> None:
        """Handle ASCII art generation."""
        self.output.display_art_text(text, style, art_type)

    def show_available_styles(self) -> None:
        """Show available ASCII art styles."""
        self.output.display_art_styles()