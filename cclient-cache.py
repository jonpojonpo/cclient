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

        # Track state for caching
        self.last_user_message = None
        self.last_assistant_message = None
        self.last_has_tools = False

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
        self.system_prompt = self.create_system_prompt()

    def create_system_prompt(self) -> str:
        """Create the system prompt with cache control"""
        return [{
            "type": "text",
            "text": """You are Claude, an AI assistant with access to system tools.
You can use Markdown for formatting.

Special formatting:
- Use !figlet[text] to create ASCII art headers
- Use standard markdown for other formatting

Available tools:
- bash: Execute shell commands
- str_replace_editor: File editor with these commands:
  - view: View file contents (params: path, view_range[optional])
  - create: Create new file (params: path, file_text)
  - str_replace: Replace text in file (params: path, old_str, new_str)
  - insert: Insert text at line (params: path, insert_line, new_str)
  - undo_edit: Undo last edit (params: path)

Always explain tool usage and outcomes to the user clearly.""",
            "cache_control": {"type": "ephemeral"}
        }]

    def prepare_tools(self):
        """Prepare tools with cache control"""
        tools = self.tool_collection.to_params()
        if tools and isinstance(tools, list) and tools[-1]:
            tools[-1]["cache_control"] = {"type": "ephemeral"}
        return tools

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
        # Store previous user message with cache control
        if self.messages and self.messages[-1]["role"] == "user":
            self.last_user_message = {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": self.messages[-1]["content"][0]["text"],
                    "cache_control": {"type": "ephemeral"}
                }]
            }
        
        # Add new user message without cache control
        current_message = {
            "role": "user",
            "content": [{
                "type": "text",
                "text": content
            }]
        }
        
        try:
            while True:  # Support multiple rounds of tool use
                with self.console.status("[bold green]Claude is thinking...", spinner="dots"):
                    # Prepare messages for request
                    messages_for_request = []
                        
                    if self.last_user_message:
                        messages_for_request.append(self.last_user_message)
                    if self.last_assistant_message:
                        messages_for_request.append({
                            "role": "assistant",
                            "content": [{
                                **block.__dict__,
                                "cache_control": {"type": "ephemeral"}
                            } for block in self.last_assistant_message]
                        })
                    messages_for_request.append(current_message)

                    response = self.client.beta.prompt_caching.messages.create(
                        max_tokens=1024,
                        messages=messages_for_request,
                        model=self.current_model,
                        system=self.system_prompt,
                        tools=self.prepare_tools(),
                        betas=["computer-use-2024-10-22"]
                    )

                    if hasattr(response, 'usage'):
                        self.console.print(
                            f"[info]Cache stats: "
                            f"created={getattr(response.usage, 'cache_creation_input_tokens', 0)}, "
                            f"read={getattr(response.usage, 'cache_read_input_tokens', 0)}, "
                            f"input={getattr(response.usage, 'input_tokens', 0)}[/info]"
                        )

                    assistant_content = []
                    has_tool_calls = False
                    tool_results = []

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
                            
                            self.console.print(Panel(
                                f"Command: {content_block.input.get('command', '(no command)')}",
                                title=f"[tool]Using {content_block.name}[/tool]",
                                border_style="yellow",
                                box=box.ROUNDED
                            ))
                            
                            try:
                                result = await self.tool_collection.run(
                                    name=content_block.name,
                                    tool_input=content_block.input
                                )
                                
                                if hasattr(result, 'output'):
                                    output = result.output
                                    error = result.error if hasattr(result, 'error') else None
                                else:
                                    output = str(result)
                                    error = None

                                if output:
                                    self.console.print(Panel(
                                        output,
                                        title=f"[tool]{content_block.name} output[/tool]",
                                        border_style="yellow",
                                        box=box.ROUNDED
                                    ))

                                if error:
                                    self.console.print(Panel(
                                        error,
                                        title="[danger]Error[/danger]",
                                        border_style="red",
                                        box=box.ROUNDED
                                    ))

                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": (output or "") + (error or ""),
                                    "is_error": bool(error)
                                })

                            except Exception as tool_error:
                                error_msg = str(tool_error)
                                self.console.print(Panel(
                                    error_msg,
                                    title="[danger]Tool Error[/danger]",
                                    border_style="red",
                                    box=box.ROUNDED
                                ))
                                
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": error_msg,
                                    "is_error": True
                                })

                    # Store assistant response and tool state for next request
                    self.last_assistant_message = response.content
                    self.last_has_tools = has_tool_calls

                    # Add to conversation history
                    self.messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })

                    if has_tool_calls:
                        current_message = {
                            "role": "user",
                            "content": tool_results
                        }
                        self.messages.append(current_message)
                        continue
                    
                    break

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
          Commands:
          - view: View file contents
          - create: Create new file
          - str_replace: Replace text in file
          - insert: Insert text at line
          - undo_edit: Undo last edit

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
        self.last_assistant_message = None
        self.last_user_message = None
        self.last_has_tools = False
        self.console.print("[bold green]Conversation and cache cleared.[/bold green]")

    def change_model(self):
        """Cycle through available models"""
        current_index = self.models.index(self.current_model)
        next_index = (current_index + 1) % len(self.models)
        self.current_model = self.models[next_index]
        self.console.print(f"[bold green]Switched to model:[/bold green] {self.current_model}")

    async def run(self):
        """Main CLI loop"""
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
