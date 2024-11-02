import os
import signal
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime
import re

import anthropic
from anthropic import Anthropic
from anthropic.types import (
    ToolResultBlockParam,
)
from anthropic.types.beta import (
    BetaContentBlock,
    BetaMessage,
)
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.theme import Theme
import pyfiglet

# Import Anthropic's tools directly
from tools import BashTool, EditTool, ToolCollection

class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.messages: List[Dict[str, Any]] = []
        self.models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        self.current_model = "claude-3-5-sonnet-20241022"
        
        # Initialize tools using Anthropic's implementations
        self.tool_collection = ToolCollection(
            BashTool(),
            EditTool(),
        )

        custom_theme = Theme({
            "info": "dim cyan",
            "warning": "magenta",
            "danger": "bold red",
            "user": "green",
            "assistant": "blue",
            "success": "bold green",
            "tool": "yellow",
        })
        self.console = Console(theme=custom_theme, color_system="truecolor")
        self.width, self.height = os.get_terminal_size()
        self.system_prompt = self.create_system_prompt()

    def create_system_prompt(self) -> str:
        """Create the system prompt with current terminal dimensions"""
        return f"""You are Claude, an AI assistant with access to system tools. Terminal dimensions: {self.width}x{self.height}.
Adjust your responses accordingly. You can use Markdown for formatting.

Special formatting:
- Use !figlet[text] to create ASCII art headers
- Use standard markdown for other formatting

Available tools:
- bash: Execute shell commands
- str_replace_editor: Edit files with advanced capabilities

Always explain tool usage and outcomes to the user clearly."""

    def update_dimensions(self, *args):
        """Update terminal dimensions and system prompt when terminal is resized"""
        self.width, self.height = os.get_terminal_size()
        self.system_prompt = self.create_system_prompt()

    def create_welcome_screen(self):
        """Create a fancy welcome screen using pyfiglet"""
        welcome_text = pyfiglet.figlet_format("Claude Chat", font="slant")
        version_text = pyfiglet.figlet_format("v3.5", font="small")
        
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
                Markdown("Type `/help` for available commands. Using model: " + self.current_model),
                style="italic cyan"
            ))
        )
        return layout

    def process_custom_markdown(self, text: str) -> str:
        """Process custom markdown extensions like figlet"""
        figlet_pattern = r'!figlet\[(.*?)\]'
        
        def figlet_replace(match):
            text = match.group(1)
            return f"```\n{pyfiglet.figlet_format(text, font='small')}\n```"
            
        return re.sub(figlet_pattern, figlet_replace, text)

    async def send_message(self, content: str):
            """Send message to Claude and handle responses with tool calls"""
            # Start with user message
            self.messages.append({
                "role": "user", 
                "content": content  # Simple text content for user messages
            })
            
            try:
                while True:  # Support multiple rounds of tool use
                    with self.console.status("[bold green]Claude is thinking...", spinner="dots"):
                        response = self.client.beta.messages.create(
                            max_tokens=1024,
                            messages=self.messages,
                            model=self.current_model,
                            system=self.system_prompt,
                            tools=self.tool_collection.to_params(),
                            betas=["computer-use-2024-10-22"]
                        )

                        assistant_content = []
                        has_tool_calls = False

                        # Process content blocks
                        for content_block in response.content:
                            if content_block.type == "text":
                                processed_text = self.process_custom_markdown(content_block.text)
                                self.console.print(Panel(
                                    Markdown(processed_text),
                                    title="Claude",
                                    border_style="blue",
                                    box=box.ROUNDED
                                ))
                                assistant_content.append(content_block)
                                
                            elif content_block.type == "tool_use":
                                has_tool_calls = True
                                assistant_content.append(content_block)
                                # Pretty print tool call
                                self.console.print(Panel(
                                    f"Command: {content_block.input.get('command', '(no command)')}",
                                    title=f"[tool]Using {content_block.name}[/tool]",
                                    border_style="yellow",
                                    box=box.ROUNDED
                                ))
                                
                                result = await self.tool_collection.run(
                                    name=content_block.name,
                                    tool_input=content_block.input
                                )
                                
                                if result.output:
                                    self.console.print(Panel(
                                        result.output,
                                        title=f"[tool]{content_block.name} output[/tool]",
                                        border_style="yellow",
                                        box=box.ROUNDED
                                    ))

                                if result.error:
                                    self.console.print(Panel(
                                        result.error,
                                        title="[danger]Error[/danger]",
                                        border_style="red",
                                        box=box.ROUNDED
                                    ))

                                # Format tool result for next message
                                tool_result_content = [{
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": (result.output or "")  + (result.error or ""),
                                    "is_error": bool(result.error)
                                }]

                        # First add assistant's message with both text and tool_use blocks
                        self.messages.append({
                            "role": "assistant",
                            "content": assistant_content
                        })

                        # Then add tool results if there were tool calls
                        if has_tool_calls:
                            self.messages.append({
                                "role": "user",
                                "content": tool_result_content
                            })
                            continue  # Continue the loop for potential chained tool calls
                        
                        break  # No more tool calls, exit the loop

            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
                self.console.print_exception()

    def print_help(self):
        """Display help information"""
        help_text = """
        # Available Commands

        - `/help`: Show this help message
        - `/model`: Change the current model
        - `/clear`: Clear the current conversation
        - `/quit`: Exit the chat

        ## Special Formatting
        - Use !figlet[text] for ASCII art headers
        - Standard markdown supported
        - Code blocks with syntax highlighting

        ## Available Tools
        - bash: Execute shell commands
        - str_replace_editor: File editing capabilities

        ## Current Model
        {}
        """.format(self.current_model)
        
        self.console.print(Panel(
            Markdown(help_text),
            title="Help",
            border_style="bold cyan",
            box=box.ROUNDED,
            expand=False
        ))

    def clear_conversation(self):
        """Clear the current conversation"""
        self.messages = []
        self.console.print("[bold green]Conversation cleared.[/bold green]")

    def change_model(self):
        """Cycle through available models"""
        current_index = self.models.index(self.current_model)
        next_index = (current_index + 1) % len(self.models)
        self.current_model = self.models[next_index]
        self.console.print(f"[bold green]Switched to model:[/bold green] {self.current_model}")

    async def run(self):
        """Main CLI loop"""
        #signal.signal(signal.SIGWINCH, self.update_dimensions)
        
        # Show welcome screen
        self.console.print(self.create_welcome_screen())
        self.console.rule(style="dim")

        while True:
            try:
                user_input = self.console.input("[bold green]You (type /help for commands):[/bold green] ").strip()

                if user_input.lower() in ['/quit', '/exit', '/q']:
                    break
                elif user_input.lower() == '/help':
                    self.print_help()
                elif user_input.lower() == '/model':
                    self.change_model()
                elif user_input.lower() == '/clear':
                    self.clear_conversation()
                elif user_input:
                    # Display user input in a panel
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
        farewell_text = pyfiglet.figlet_format("Goodbye!", font="small")
        self.console.print(Panel(
            farewell_text,
            title="Thanks for using Claude Chat!",
            border_style="bold blue",
            box=box.DOUBLE
        ))

if __name__ == "__main__":
    cli = ClaudeClient()
    asyncio.run(cli.run())
