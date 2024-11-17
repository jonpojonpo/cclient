from typing import Optional
import re
from rich.markdown import Markdown
from rich.console import Console
from rich.text import Text
from rich.segment import Segment

class TextFormatter:
    """Handles text formatting, including rich tags and markdown."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def process_text(self, text: str) -> str:
        """Process all text formatting, including rich tags and markdown."""
        # Preserve ASCII art blocks (content between `````` marks)
        ascii_blocks = {}
        block_counter = 0
        
        def preserve_ascii_art(match):
            nonlocal block_counter
            block_id = f"__ASCII_BLOCK_{block_counter}__"
            ascii_blocks[block_id] = match.group(1)
            block_counter += 1
            return block_id
            
        # Save ASCII art blocks before processing
        text = re.sub(r'```\n(.*?)\n```', preserve_ascii_art, text, flags=re.DOTALL)
        
        # Process markdown and rich tags
        text = self._process_markdown_between_tags(text)
        
        # Restore ASCII art blocks
        for block_id, art in ascii_blocks.items():
            text = text.replace(block_id, f"```\n{art}\n```")
            
        return text

    def _segment_to_string(self, segments) -> str:
        """Convert Rich segments to a plain string with style information preserved."""
        result = ""
        current_style = None
        buffer = ""
        
        for segment in segments:
            if isinstance(segment, Segment):
                # If style changes, flush buffer with previous style
                if current_style != segment.style:
                    if buffer:
                        if current_style:
                            result += f"[{current_style}]{buffer}[/{current_style}]"
                        else:
                            result += buffer
                        buffer = ""
                    current_style = segment.style
                buffer += segment.text
            else:
                # Non-segment content
                if buffer:
                    if current_style:
                        result += f"[{current_style}]{buffer}[/{current_style}]"
                    else:
                        result += buffer
                    buffer = ""
                result += str(segment)
                
        # Flush any remaining content
        if buffer:
            if current_style:
                result += f"[{current_style}]{buffer}[/{current_style}]"
            else:
                result += buffer
                
        return result

    def _process_markdown_between_tags(self, text: str) -> str:
        """Process markdown while preserving rich tags."""
        # Pattern for rich formatting tags
        pattern = r'\[(.*?)\](.*?)\[/\1\]'
        
        def replace_match(match):
            style = match.group(1)
            content = match.group(2)
            
            # Skip markdown processing if content appears to be ASCII art
            if '```' in content or any(line.strip().startswith('|') for line in content.splitlines()):
                return f"[{style}]{content}[/{style}]"
                
            # Create a temporary console for rendering the markdown
            temp_console = Console(force_terminal=True)
            
            # Process the markdown content
            markdown = Markdown(content)
            # Convert the rendered segments to a string while preserving formatting
            rendered_content = self._segment_to_string(temp_console.render(markdown))
            
            # Wrap the rendered content with the original style tag
            return f"[{style}]{rendered_content}[/{style}]"
        
        # Process the tagged sections
        processed = re.sub(pattern, replace_match, text)
        
        # Handle any remaining markdown outside of rich tags
        parts = []
        last_end = 0
        
        for match in re.finditer(pattern, text):
            # Process any text before the tag
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                # Skip markdown processing if content appears to be ASCII art
                if '```' in plain_text or any(line.strip().startswith('|') for line in plain_text.splitlines()):
                    parts.append(plain_text)
                else:
                    markdown = Markdown(plain_text)
                    parts.append(self._segment_to_string(self.console.render(markdown)))
            # Add the already processed tagged content
            parts.append(match.group(0))
            last_end = match.end()
        
        # Process any remaining text after the last tag
        if last_end < len(text):
            plain_text = text[last_end:]
            # Skip markdown processing if content appears to be ASCII art
            if '```' in plain_text or any(line.strip().startswith('|') for line in plain_text.splitlines()):
                parts.append(plain_text)
            else:
                markdown = Markdown(plain_text)
                parts.append(self._segment_to_string(self.console.render(markdown)))
        
        if parts:
            processed = ''.join(parts)
            
        return processed

    def colorize(self, text: str, style: str) -> str:
        """Apply a rich text style to text."""
        return f"[{style}]{text}[/{style}]"
