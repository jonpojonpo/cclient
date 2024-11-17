# client.py
from typing import Optional
import re
from pathlib import Path

from .art_manager import ArtManager

class FormattingExtension:
    """Extension to handle rich formatting and art in Claude's responses."""
    
    def __init__(self, art_manager: ArtManager):
        self.art = art_manager
        
        # Regex patterns for special formatting
        self.art_pattern = re.compile(r'!art\[(.*?)\](?:\{(.*?)\})?')
        self.figlet_pattern = re.compile(r'!figlet\[(.*?)\](?:\{(.*?)\})?')
        self.rich_pattern = re.compile(r'\[(.*?)\](.*?)\[/\1\]')
        
    def process_response(self, text: str) -> str:
        """Process Claude's response for special formatting."""
        # Process ASCII art commands
        text = self._process_art_commands(text)
        
        # Process rich formatting
        text = self._process_rich_formatting(text)
        
        return text
        
    def _process_art_commands(self, text: str) -> str:
        """Process ASCII art commands in text."""
        # Handle !art[] commands
        for match in self.art_pattern.finditer(text):
            content = match.group(1)
            options = self._parse_options(match.group(2)) if match.group(2) else {}
            
            art_text = self.art.create_art_text(
                content,
                style=options.get('style', 'random'),
                art_type='art',
                decoration=options.get('decoration'),
                color=options.get('color')
            )
            
            text = text.replace(match.group(0), art_text)
            
        # Handle !figlet[] commands
        for match in self.figlet_pattern.finditer(text):
            content = match.group(1)
            options = self._parse_options(match.group(2)) if match.group(2) else {}
            
            art_text = self.art.create_art_text(
                content,
                style=options.get('style', 'random'),
                art_type='figlet',
                color=options.get('color')
            )
            
            text = text.replace(match.group(0), art_text)
            
        return text
        
    def _process_rich_formatting(self, text: str) -> str:
        """Process rich formatting tags in text."""
        return text  # Rich formatting tags are passed through to rich.Console
        
    def _parse_options(self, options_str: str) -> dict:
        """Parse options string into dictionary."""
        if not options_str:
            return {}
            
        options = {}
        for opt in options_str.split(','):
            if '=' in opt:
                key, value = opt.split('=')
                options[key.strip()] = value.strip()
            else:
                options[opt.strip()] = True
        return options

# Usage example:
# client = ClaudeClient()
# response = "Hello !art[World]{style=block,color=fancy,decoration=coffee}"
# formatted = client.formatting.process_response(response)
# client.console.print(formatted)