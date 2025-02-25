# main.py
import os
import signal
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

import anthropic
from anthropic import Anthropic
from anthropic.types import ToolResultBlockParam
from anthropic.types.beta import BetaContentBlock, BetaMessage
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.theme import Theme
import pyfiglet

from tools.base import BaseAnthropicTool, ToolResult
from tools.tool_manager import ToolManager
from tools.bash import BashTool20250124
from tools.edit import EditTool20250124
from formatters.art_manager import ArtManager
from formatters.text_formatter import TextFormatter
from core.cache import CacheManager
from core.config import ConfigManager
from message_processor import MessageProcessor

class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-7-sonnet-latest"
        
        # Setup theming
        custom_theme = Theme({
            "info": "dim cyan",
            "warning": "yellow",
            "danger": "bold red",
            "user": "green",
            "assistant": "blue",
            "success": "bold green",
            "tool": "yellow",
            "system": "grey70",
            "prompt": "cyan",
            "cache": "dim magenta",
            "error": "red",
            "fancy": "magenta",
            # Standard colors
            "red": "red",
            "green": "green",
            "blue": "blue",
            "yellow": "yellow",
            "magenta": "magenta",
            "cyan": "cyan",
            "white": "white",
            # Combined styles
            "bold red": "bold red",
            "bold green": "bold green",
            "bold blue": "bold blue",
            "bold yellow": "bold yellow",
            "italic green": "italic green",
            "italic blue": "italic blue",
            "dim blue": "dim blue",
            "dim cyan": "dim cyan"
        })
        
        # Initialize console and managers
        self.console = Console(theme=custom_theme, color_system="truecolor")
        config_dir = Path(__file__).parent / "config"
        
        # Initialize all managers and formatters
        self.config_manager = ConfigManager(config_dir)
        self.cache_manager = CacheManager()
        self.art_manager = ArtManager(self.console)
        self.text_formatter = TextFormatter(self.console)
        self.tool_manager = ToolManager(console=self.console)
        
        # Initialize message processor
        self.message_processor = MessageProcessor(
            console=self.console,
            art_manager=self.art_manager,
            text_formatter=self.text_formatter,
            tool_manager=self.tool_manager,
            cache_manager=self.cache_manager
        )
        self.messages = []
        self.system_prompt = self.config_manager.get_system_prompt()
        
        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register available tools."""
        for tool in [BashTool(), EditTool()]:
            self.tool_manager.register_tool(tool.name, tool)
            self.console.print(f"[system]Registered tool:[/system] [tool]{tool.name}[/tool]")

    def create_welcome_screen(self) -> Layout:
        """Create a fancy welcome screen."""
        welcome_text = self.art_manager.create_art_text(
            "Claude Chat",
            style="slant",
            art_type="figlet",
            color="fancy"
        )
        version_text = self.art_manager.create_art_text(
            "v3.5",
            style="small",
            art_type="figlet",
            color="info"
        )
        
        layout = Layout()
        layout.split(
            Layout(Panel(
                f"{welcome_text}\n{version_text}",
                title="Welcome",
                style="bold blue",
                border_style="bold cyan",
                box=box.DOUBLE
            )),
            Layout(Panel(
                Markdown("Type `/help` for available commands. Using model: " + self.model),
                style="italic cyan"
            ))
        )
        return layout

    def _display_cache_stats(self) -> None:
        """Display current cache statistics."""
        stats = self.cache_manager.stats
        if stats.last_updated:
            self.console.print(
                f"[cache]Cache stats: "
                f"created={stats.created_tokens}, "
                f"read={stats.read_tokens}, "
                f"total={stats.total_tokens}[/cache]"
            )

    async def _get_claude_response(self, messages: List[Dict[str, Any]]):
        """Get response from Claude API."""
        response = self.client.beta.messages.create(
            max_tokens=1024,
            messages=messages,
            model=self.model,
            system=[self.config_manager.get_system_prompt()],
            tools=self.tool_manager.get_tool_configs(),
            betas=["computer-use-2024-10-22", "prompt-caching-2024-07-31"]
        )
        
        # Update cache stats if available
        if hasattr(response, 'usage'):
            self.cache_manager.update_stats(response.usage)
            self._display_cache_stats()
            
        return response

    async def send_message(self, content: str):
            """Send message to Claude and handle responses with tool calls"""
            self.messages.append({
                "role": "user", 
                "content": content
            })
            
            try:
                while True:  # Support multiple rounds of tool use
                    with self.console.status("[bold green]Claude is thinking...", spinner="dots"):
                        # Get Claude's response
                        response = await self._get_claude_response(self.messages)
                        
                        # Process the response using MessageProcessor
                        result = await self.message_processor.process_response(response)
                        
                        # Add assistant's message
                        self.messages.append({
                            "role": "assistant",
                            "content": result.assistant_content
                        })

                        # If there were tool calls, add results and continue
                        if result.has_tool_calls:
                            if result.tool_content:
                                # Add tool results as a user message
                                self.messages.append({
                                    "role": "user",
                                    "content": result.tool_content  # This is already in the correct format
                                })
                            else:
                                # If no tool results, still need to send empty result
                                self.messages.append({
                                    "role": "user",
                                    "content": [{
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": "",
                                        "is_error": True
                                    } for block in result.assistant_content if block.type == "tool_use"]
                                })
                            continue
                        
                        break  # No tool calls, end the conversation turn

            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
                self.console.print_exception()



    def print_help(self) -> None:
        """Display help information."""
        help_text = """
        # Available Commands

        - `/help`: Show this help message
        - `/clear`: Clear the current conversation
        - `/styles`: Show available art styles
        - `/colors`: Show color formatting demo
        - `/quit`: Exit the chat

        ## Formatting Options
        - ASCII art with !art[] and !figlet[]
        - Rich text formatting with [style]text[/style]
        - Standard markdown supported

        ## Tools
        - bash: Execute shell commands
        - str_replace_editor: File editing capabilities

        ## Current Model
        {}
        """.format(self.model)
        
        self.console.print(Panel(
            Markdown(help_text),
            title="Help",
            border_style="bold cyan",
            box=box.ROUNDED,
            expand=False
        ))

    def print_color_demo(self) -> None:
        """Display color formatting demo."""
        self.console.print("\n=== Color Formatting Demo ===\n")
        
        self.console.print("[bold]Basic Colors:[/bold]")
        for color in ["red", "green", "blue", "yellow", "magenta", "cyan", "white"]:
            self.console.print(f"[{color}]This is {color} text[/{color}]")
        
        self.console.print("\n[bold]Style Combinations:[/bold]")
        self.console.print("[bold red]Bold Red[/bold red]")
        self.console.print("[italic green]Italic Green[/italic green]")
        self.console.print("[dim blue]Dim Blue[/dim blue]")
        
        self.console.print("\n[bold]Predefined Styles:[/bold]")
        self.console.print("[success]Success Message[/success]")
        self.console.print("[error]Error Message[/error]")
        self.console.print("[warning]Warning Message[/warning]")
        self.console.print("[info]Info Message[/info]")
        self.console.print("[fancy]Fancy Text[/fancy]")

    def clear_conversation(self) -> None:
        """Clear conversation state and cache."""
        self.cache_manager.clear()
        self.tool_manager.clear_results()
        self.console.print("[bold green]Conversation and cache cleared.[/bold green]")

    async def run(self) -> None:
        """Main client loop."""
        # Show welcome screen
        self.console.print(self.create_welcome_screen())
        self.console.rule(style="dim")

        while True:
            try:
                user_input = self.console.input("[bold green]You:[/bold green] ").strip()

                if user_input.lower() in ['/quit', '/exit', '/q']:
                    break
                elif user_input.lower() == '/help':
                    self.print_help()
                elif user_input.lower() == '/clear':
                    self.clear_conversation()
                elif user_input.lower() == '/styles':
                    self.art_manager.display_art_gallery()
                elif user_input.lower() == '/colors':
                    self.print_color_demo()
                elif user_input:
                    self.console.print(Panel(
                        user_input,
                        title="You",
                        border_style="green",
                        box=box.ROUNDED
                    ))
                    await self.send_message(user_input)

                self.console.rule(style="dim")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

        # Farewell message
        farewell_text = self.art_manager.create_art_text(
            "Goodbye!",
            style="small",
            art_type="figlet",
            color="info"
        )
        self.console.print(Panel(
            farewell_text,
            title="Thanks for using Claude Chat!",
            border_style="bold blue",
            box=box.DOUBLE
        ))

if __name__ == "__main__":
    cli = ClaudeClient()
    asyncio.run(cli.run())