# message_processor.py
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from rich.panel import Panel
from rich.box import ROUNDED

@dataclass
class MessageResult:
    """Represents the result of processing a message."""
    assistant_content: List[Dict[str, Any]]
    has_tool_calls: bool
    tool_content: List[Dict[str, Any]]

class MessageProcessor:
    """Handles message processing and display."""
    
    def __init__(self, console, art_manager, text_formatter, tool_manager, cache_manager):
        self.console = console
        self.art_manager = art_manager
        self.text_formatter = text_formatter
        self.tool_manager = tool_manager
        self.cache_manager = cache_manager

    async def process_response(self, response) -> MessageResult:
        """Process API response and return results."""
        assistant_content = []
        tool_content = []
        has_tool_calls = False

        for content_block in response.content:
            if content_block.type == "text":
                processed_block = await self._handle_text_block(content_block)
                assistant_content.append(processed_block)
            elif content_block.type == "tool_use":
                has_tool_calls = True
                assistant_content.append(content_block)
                # Process tool and get result
                await self.tool_manager.handle_tool(content_block)
                result = self.tool_manager.get_tool_result(content_block.id)
                
                # Format tool result for Claude API
                if result:
                    is_error = bool(result.error)
                    content = ""
                    
                    # Handle content based on whether it's an error or success
                    if is_error:
                        content = f"Error: {result.error}" if result.error else "Unknown error occurred"
                    else:
                        content = result.output if result.output else "Success but no output"
                    
                    tool_content.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": content,  # Never empty content
                        "is_error": is_error
                    })
                else:
                    # Handle case where no result was returned
                    tool_content.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": "Tool execution failed to produce a result",
                        "is_error": True
                    })

        return MessageResult(
            assistant_content=assistant_content,
            has_tool_calls=has_tool_calls,
            tool_content=tool_content
        )

    async def _handle_text_block(self, block) -> Dict[str, Any]:
        """Process and display text block."""
        text = block.text
        
        # Process art commands if present
        if "!art[" in text or "!figlet[" in text:
            text = self.art_manager.process_text_commands(text)
        
        # Process rich formatting and markdown
        text = self.text_formatter.process_text(text)
        
        # Display processed text
        self.console.print(Panel(
            text,
            title="Claude",
            border_style="blue",
            box=ROUNDED
        ))
        
        return block

    async def _handle_tool_block(self, block) -> List[Dict[str, Any]]:
        """Process tool use block and return tool content."""
        await self.tool_manager.handle_tool(block)
        tool_result = self.tool_manager.get_tool_result(block.id)
        
        if not tool_result:
            return []

        tool_content = []
        if tool_result.output:
            tool_content.append({"type": "text", "text": tool_result.output})
        if tool_result.error:
            tool_content.append({"type": "text", "text": tool_result.error})

        return tool_content