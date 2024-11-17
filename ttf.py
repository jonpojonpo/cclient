from rich.console import Console
from formatters.text_formatter import TextFormatter

def main():
    console = Console()
    formatter = TextFormatter(console)
    
    # Test case with ASCII art, markdown and rich tags
    test_text = """[blue]**Welcome!**[/blue]

```
 .----------------.  .----------------.  .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. |
| |  ________    | || |  _________   | || |  ____  ____  | || |     ____     | |
| |  |_   _  |   | || | |_   ___  |  | || | |_   ||   _| | || |   .'    `.   | |
| |    | |_) |   | || |   | |_  \_|  | || |   | |__| |   | || |  /  .--.  \  | |
| |    |  __'.   | || |   |  _|  _   | || |   |  __  |   | || |  | |    | |  | |
| |   _| |__) |  | || |  _| |___/ |  | || |  _| |  | |_  | || |  \  `--'  /  | |
| |  |_______/   | || | |_________|  | || | |____||____| | || |   `.____.'   | |
| |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------' 
```

[green]*This* is a **test** of mixing:
1. ASCII art
2. *Markdown*
3. [red]Rich[/red] tags[/green]"""

    try:
        processed = formatter.process_text(test_text)
        console.print(processed)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")

if __name__ == "__main__":
    main()