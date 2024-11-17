# output_manager.py
from typing import Optional, Union, AsyncIterator
import asyncio
from pathlib import Path
import subprocess
from functools import partial

from rich.console import Console
from rich.syntax import Syntax
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.padding import Padding
from rich.columns import Columns
from rich.text import Text
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.util import ClassNotFound
from art import text2art, art_list
import pyfiglet

class OutputManager:
    """Manages rich text output formatting and real-time updates."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._current_live: Optional[Live] = None
        
        # Configure available ASCII art fonts
        self.figlet_fonts = pyfiglet.FigletFont.getFonts()
        self.art_fonts = [style for style in art_list() if not style.startswith("random")]
    
    def format_code(self, code: str, filename: Optional[str] = None, line_numbers: bool = True) -> Syntax:
        """Format code with syntax highlighting."""
        try:
            if filename:
                lexer = get_lexer_for_filename(filename)
            else:
                # Try to guess lexer from content
                lexer = TextLexer()
            
            return Syntax(
                code,
                lexer.name,
                line_numbers=line_numbers,
                word_wrap=True,
                indent_guides=True,
                theme="monokai"
            )
        except ClassNotFound:
            return Syntax(code, "text", line_numbers=line_numbers)

    async def stream_bash_output(self, command: str) -> None:
        """Stream bash command output in real-time."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Create output table
        table = Table.grid(padding=(0, 1))
        table.add_column("Output")
        table.add_column("Error", style="red")
        
        # Set up live display
        with Live(table, console=self.console, refresh_per_second=10) as live:
            stdout_lines = []
            stderr_lines = []
            
            # Stream output and error simultaneously
            while True:
                stdout_data = await process.stdout.readline()
                stderr_data = await process.stderr.readline()
                
                if not stdout_data and not stderr_data and process.returncode is not None:
                    break
                    
                if stdout_data:
                    line = stdout_data.decode().rstrip()
                    stdout_lines.append(line)
                if stderr_data:
                    line = stderr_data.decode().rstrip()
                    stderr_lines.append(line)
                    
                # Update display
                table.rows = []
                table.add_row(
                    "\n".join(stdout_lines),
                    "\n".join(stderr_lines)
                )
        
        await process.wait()
        
    def display_file_content(self, content: str, filename: str, 
                           start_line: Optional[int] = None,
                           end_line: Optional[int] = None) -> None:
        """Display file content with syntax highlighting and line numbers."""
        if start_line is not None and end_line is not None:
            lines = content.splitlines()
            content = "\n".join(lines[start_line-1:end_line])
            
        syntax = self.format_code(content, filename)
        self.console.print(Panel(
            syntax,
            title=f"[blue]{filename}[/blue] [dim](lines {start_line}-{end_line})[/dim]" if start_line else filename,
            border_style="blue"
        ))

    def display_art_text(self, text: str, style: str = "random", 
                        art_type: str = "figlet") -> None:
        """Display text as ASCII art using either figlet or art library."""
        if art_type == "figlet":
            if style == "random":
                style = pyfiglet.FigletFont.getFonts()[0]
            art = pyfiglet.figlet_format(text, font=style)
        else:
            if style == "random":
                style = self.art_fonts[0]
            art = text2art(text, style)
            
        self.console.print(Panel(art, border_style="cyan"))

    def display_art_styles(self) -> None:
        """Display available ASCII art styles."""
        # Create preview table
        table = Table(title="Available ASCII Art Styles")
        table.add_column("Library")
        table.add_column("Style")
        table.add_column("Preview")
        
        # Add figlet fonts
        for font in self.figlet_fonts[:5]:  # Show first 5 as preview
            preview = pyfiglet.figlet_format("Hi!", font=font)
            table.add_row("figlet", font, preview)
            
        # Add art fonts
        for style in self.art_fonts[:5]:  # Show first 5 as preview
            preview = text2art("Hi!", style)
            table.add_row("art", style, preview)
            
        self.console.print(table)

    def display_diff(self, old_content: str, new_content: str, 
                    filename: str) -> None:
        """Display file changes with syntax highlighting."""
        from difflib import unified_diff
        
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff_lines = list(unified_diff(
            old_lines, new_lines,
            fromfile=f"old/{filename}",
            tofile=f"new/{filename}",
            lineterm=""
        ))
        
        if diff_lines:
            diff_text = Text()
            for line in diff_lines:
                if line.startswith("+"):
                    diff_text.append(line + "\n", style="green")
                elif line.startswith("-"):
                    diff_text.append(line + "\n", style="red")
                else:
                    diff_text.append(line + "\n")
                    
            self.console.print(Panel(
                diff_text,
                title=f"Changes in {filename}",
                border_style="yellow"
            ))
        else:
            self.console.print("[yellow]No changes detected[/yellow]")