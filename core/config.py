# config_manager.py
from pathlib import Path
from typing import Dict, Any
import yaml
from jinja2 import Template

class ConfigManager:
    """Manages loading and templating of YAML configurations."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.system_prompt = None
        self.tools = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Load all configuration files."""
        # Load system prompt
        system_prompt_path = self.config_dir / "system_prompt.yaml"
        with open(system_prompt_path) as f:
            self.system_prompt = yaml.safe_load(f)

        # Load tool configs
        tools_dir = self.config_dir / "tools"
        for tool_file in tools_dir.glob("*.yaml"):
            with open(tool_file) as f:
                tool_config = yaml.safe_load(f)
                self.tools[tool_config["name"]] = tool_config

    def get_system_prompt(self) -> Dict[str, Any]:
        """Get system prompt with tool descriptions templated in."""
        if not self.system_prompt:
            raise ValueError("System prompt not loaded")

        # Build tool descriptions string
        tool_descriptions = []
        for tool in self.tools.values():
            tool_descriptions.append(f"- {tool['name']}: {tool['description']}")

        # Template tool descriptions into system prompt
        template = Template(self.system_prompt["prompt"]["text"])
        templated_text = template.render(
            tool_descriptions="\n".join(tool_descriptions)
        )

        return {
            "type": "text",
            "text": templated_text,
            "cache_control": self.system_prompt["prompt"]["cache_control"]
        }

    def get_tool_configs(self) -> Dict[str, Any]:
        """Get tool configurations."""
        return self.tools