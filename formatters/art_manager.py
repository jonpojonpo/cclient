# formatters/art_manager.py
from typing import Optional, List, Dict, Tuple
import random
import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from art import text2art, art, FONT_NAMES
import pyfiglet
import ascii_magic

class ArtManager:
    """Enhanced manager for ASCII art and text effects."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        
        # Load available fonts and styles
        self.figlet_fonts = pyfiglet.FigletFont.getFonts()
        self.art_fonts = [f for f in FONT_NAMES if not f.startswith(('random', 'wizard'))]
        
        # Common working decorations from art library
        self.art_decorations = [
            'coffee', 'happy', 'love', 'music', 'star',
            'butterfly', 'heart', 'bath', 'rose', 'fish',
            'cat', 'dog', 'snail', 'mouse', 'rabbit'
        ]
        
        # Rich text color palettes
        self.color_palettes = {
            'success': ['bold green', 'green'],
            'error': ['bold red', 'red'],
            'warning': ['bold yellow', 'yellow'],
            'info': ['bold blue', 'blue', 'cyan'],
            'fancy': ['magenta', 'purple', 'bright_magenta']
        }

    def _parse_options(self, options_str: Optional[str]) -> Dict[str, str]:
        """Parse options string into dictionary."""
        if not options_str:
            return {}
            
        options = {}
        try:
            for opt in options_str.split(','):
                if '=' in opt:
                    key, value = opt.split('=', 1)
                    options[key.strip()] = value.strip()
                else:
                    options[opt.strip()] = True
        except Exception:
            # Return empty dict if parsing fails
            return {}
            
        return options

    def process_text_commands(self, text: str) -> str:
        """Process art and figlet commands in text."""
        # Process !art[] commands
        art_pattern = r'!art\[(.*?)\](?:\{(.*?)\})?'
        for match in re.finditer(art_pattern, text):
            content = match.group(1)
            options = self._parse_options(match.group(2)) if match.group(2) else {}
            art_text = self.create_art_text(
                content,
                style=options.get('style', 'random'),
                art_type='art',
                decoration=options.get('decoration'),
                color=options.get('color')
            )
            text = text.replace(match.group(0), f"\n{art_text}\n")

        # Process !figlet[] commands
        figlet_pattern = r'!figlet\[(.*?)\](?:\{(.*?)\})?'
        for match in re.finditer(figlet_pattern, text):
            content = match.group(1)
            options = self._parse_options(match.group(2)) if match.group(2) else {}
            art_text = self.create_art_text(
                content,
                style=options.get('style', 'random'),
                art_type='figlet',
                color=options.get('color')
            )
            text = text.replace(match.group(0), f"\n{art_text}\n")

        return text

    def create_art_text(self, text: str, style: str = "random", 
                       art_type: str = "art", decoration: Optional[str] = None,
                       color: Optional[str] = None) -> str:
        """Create ASCII art text with optional decoration and color."""
        if art_type == "figlet":
            if style == "random" or style not in self.figlet_fonts:
                style = random.choice(self.figlet_fonts)
            art_text = pyfiglet.figlet_format(text, font=style)
        else:
            if style == "random" or style not in self.art_fonts:
                style = random.choice(self.art_fonts)
            try:
                art_text = text2art(text, font=style)
            except Exception:
                # Fallback to a simple font if the chosen one fails
                art_text = text2art(text, font="block")
            
        # Add decoration if requested
        if decoration:
            if decoration == "random":
                decoration = random.choice(self.art_decorations)
            if decoration in self.art_decorations:
                try:
                    dec = art(decoration)
                    if dec:  # Only add decoration if it's valid
                        art_text = f"{dec}\n{art_text}\n{dec}"
                except Exception:
                    pass  # Skip decoration if it fails
            
        # Add rich color formatting if requested
        if color:
            if color in self.color_palettes:
                color = random.choice(self.color_palettes[color])
            art_text = f"[{color}]{art_text}[/{color}]"
            
        return art_text

    def display_art_gallery(self, text: str = "Hello!") -> None:
        """Display a gallery of available art styles."""
        # Create preview tables
        figlet_table = Table(title="Figlet Fonts")
        figlet_table.add_column("Font")
        figlet_table.add_column("Preview")
        
        art_table = Table(title="Art Library Fonts")
        art_table.add_column("Font")
        art_table.add_column("Preview")
        
        decor_table = Table(title="Decorations")
        decor_table.add_column("Style")
        decor_table.add_column("Preview")
        
        # Add samples
        for font in random.sample(self.figlet_fonts, min(5, len(self.figlet_fonts))):
            preview = pyfiglet.figlet_format(text, font=font)
            figlet_table.add_row(font, preview)
            
        for font in random.sample(self.art_fonts, min(5, len(self.art_fonts))):
            try:
                preview = text2art(text, font=font)
                art_table.add_row(font, preview)
            except Exception:
                continue
            
        for decoration in random.sample(self.art_decorations, min(5, len(self.art_decorations))):
            try:
                preview = art(decoration)
                if preview:
                    decor_table.add_row(decoration, preview)
            except Exception:
                continue
            
        # Display tables
        self.console.print(figlet_table)
        self.console.print(art_table)
        self.console.print(decor_table)

    async def image_to_ascii(self, image_path: str, columns: int = 100, 
                           mode: str = "standard") -> str:
        """Convert image to ASCII art using ascii-magic."""
        output = ascii_magic.from_image_file(
            image_path,
            columns=columns,
            mode=mode  # standard, full, terminal
        )
        return output

    def add_rich_formatting(self, text: str, style: Optional[str] = None,
                          random_style: bool = False) -> str:
        """Add rich text formatting to string."""
        if random_style:
            # Choose random color and style combinations
            color = random.choice(list(self.color_palettes.keys()))
            style = random.choice(self.color_palettes[color])
        elif style in self.color_palettes:
            style = random.choice(self.color_palettes[style])
            
        if style:
            return f"[{style}]{text}[/{style}]"
        return text