# CClient

A feature-rich terminal-based chat client for Claude AI using the Anthropic API.

## Description
CClient is an interactive terminal application that provides a sophisticated interface to chat with Claude, Anthropic's AI model. It features:

- Rich text formatting and colored output
- Support for multiple Claude models (3.5, Opus, Sonnet, Haiku)
- ASCII art welcome screens and headers
- System tool integration (bash commands and file editing)
- Markdown support in chat
- Interactive command system

## Prerequisites
- Python 3.8 or higher
- An Anthropic API key

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/cclient.git

# Install dependencies
pip install -r requirements.txt

# Set up your Anthropic API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage
To start the chat client:
```bash
python cclient.py
```

### Available Commands
- `/help`: Show help information
- `/model`: Switch between different Claude models
- `/clear`: Clear the current conversation
- `/quit`: Exit the application

### What's New
This section was added by Claude to demonstrate its capabilities.
Last updated: 2024-10-26 11:04

### Special Features
1. **ASCII Art Headers**
   ```
   !figlet[Your Text Here]
   ```

2. **Rich Markdown Support**
   - Code blocks with syntax highlighting
   - Tables
   - Lists and headings

3. **System Tools**
   - Execute bash commands directly from chat
   - Edit files interactively

4. **Multiple Model Support**
   - claude-3-5-sonnet-20241022
   - claude-3-opus-20240229
   - claude-3-sonnet-20240229
   - claude-3-haiku-20240307

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

Please make sure to:
1. Update requirements.txt if adding new dependencies
2. Test your changes thoroughly
3. Follow the existing code style

## License
[MIT](https://choosealicense.com/licenses/mit/)
