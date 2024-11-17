# art_manager.py
from typing import Optional, List, Dict, Tuple
import random
from pathlib import Path
import tempfile

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from art import text2art, art_list, decor, art, font_list, FONT_NAMES
import pyfiglet
import ascii_magic
from PIL import Image

class ArtManager:
    """Enhanced manager for ASCII art and text effects."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        
        # Load available fonts and styles
        self.figlet_fonts = pyfiglet.FigletFont.getFonts()
        self.art_fonts = [f for f in FONT_NAMES if not f.startswith(('random', 'wizard'))]
        self.art_decorations = [d for d in decor() if not d.startswith('random')]
        
        # Rich text color palettes
        self.color_palettes = {
            'success': ['bold green', 'green'],
            'error': ['bold red', 'red'],
            'warning': ['bold yellow', 'yellow'],
            'info': ['bold blue', 'blue', 'cyan'],
            'fancy': ['magenta', 'purple', 'bright_magenta']
        }

    def create_art_text(self, text: str, style: str = "random", 
                       art_type: str = "art", decoration: Optional[str] = None,
                       color: Optional[str] = None) -> str:
        """Create ASCII art text with optional decoration and color."""
        if art_type == "figlet":
            if style == "random":
                style = random.choice(self.figlet_fonts)
            art_text = pyfiglet.figlet_format(text, font=style)
        else:
            if style == "random":
                style = random.choice(self.art_fonts)
            art_text = text2art(text, font=style)
            
        # Add decoration if requested
        if decoration:
            if decoration == "random":
                decoration = random.choice(self.art_decorations)
            art_text = art(decoration) + "\n" + art_text + "\n" + art(decoration)
            
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
        for font in random.sample(self.figlet_fonts, 5):
            preview = pyfiglet.figlet_format(text, font=font)
            figlet_table.add_row(font, preview)
            
        for font in random.sample(self.art_fonts, 5):
            preview = text2art(text, font=font)
            art_table.add_row(font, preview)
            
        for decoration in random.sample(self.art_decorations, 5):
            preview = art(decoration)
            decor_table.add_row(decoration, preview)
            
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

    def create_demo_output(self) -> None:
        """Create a demo of available formatting options."""
        self.console.print("\n=== Text Formatting Demo ===\n")
        
        # Show color palettes
        for name, styles in self.color_palettes.items():
            self.console.print(f"[bold]Palette: {name}")
            for style in styles:
                self.console.print(f"[{style}]Sample text in {style}[/{style}]")
            self.console.print()
            
        # Show ASCII art examples
        self.console.print("[bold]ASCII Art Examples:[/bold]\n")
        
        # Figlet example
        figlet_art = self.create_art_text(
            "Demo!", 
            style="slant",
            art_type="figlet",
            color="fancy"
        )
        self.console.print(Panel(figlet_art, title="Figlet Art"))
        
        # Art library example
        art_text = self.create_art_text(
            "Cool!", 
            style="block",
            decoration="coffee",
            color="success"
        )
        self.console.print(Panel(art_text, title="Art Library"))

    def list_fonts(self, category: str = "all") -> None:
        """List all available fonts in specified category."""
        if category in ["figlet", "all"]:
            self.console.print("[bold]Figlet Fonts:[/bold]")
            for font in sorted(self.figlet_fonts):
                self.console.print(f"- {font}")
                
        if category in ["art", "all"]:
            self.console.print("\n[bold]Art Library Fonts:[/bold]")
            for font in sorted(self.art_fonts):
                self.console.print(f"- {font}")
                
        if category in ["decorations", "all"]:
            self.console.print("\n[bold]Decorations:[/bold]")
            for dec in sorted(self.art_decorations):
                self.console.print(f"- {dec}")