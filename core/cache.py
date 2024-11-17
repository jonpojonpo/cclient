from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessageParam,
    BetaCacheControlEphemeralParam,
)

@dataclass
class CacheStats:
    created_tokens: int = 0
    read_tokens: int = 0
    total_tokens: int = 0
    last_updated: Optional[datetime] = None

class CacheManager:
    """Manages message caching for Claude conversations."""
    
    def __init__(self):
        self.stats = CacheStats()
        self.last_user_message: Optional[Dict[str, Any]] = None
        self.last_assistant_message: Optional[List[BetaContentBlockParam]] = None
        self._ephemeral_breakpoints = 3  # Number of recent turns to keep ephemeral

    def update_stats(self, response_usage) -> None:
        """Update cache statistics from API response."""
        self.stats.created_tokens = getattr(response_usage, 'cache_creation_input_tokens', 0)
        self.stats.read_tokens = getattr(response_usage, 'cache_read_input_tokens', 0)
        self.stats.total_tokens = getattr(response_usage, 'input_tokens', 0)
        self.stats.last_updated = datetime.now()

    def prepare_messages(self, new_content: str) -> List[BetaMessageParam]:
        """Prepare messages for API request with proper cache control."""
        messages: List[BetaMessageParam] = []

        # Add cached messages if available
        if self.last_user_message:
            messages.append(self.last_user_message)
        if self.last_assistant_message:
            messages.append({
                "role": "assistant",
                "content": [{
                    **block,
                    "cache_control": {"type": "ephemeral"}
                } for block in self.last_assistant_message]
            })

        # Add new message
        messages.append(self._create_user_message(new_content))
        
        # Apply cache control strategy
        return self._inject_cache_control(messages)

    def _create_user_message(self, content: str) -> BetaMessageParam:
        """Create a new user message with appropriate cache control."""
        return {
            "role": "user",
            "content": [{
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"}
            }]
        }

    def _inject_cache_control(
        self, 
        messages: List[BetaMessageParam]
    ) -> List[BetaMessageParam]:
        """
        Implement caching strategy:
        - Keep N most recent turns ephemeral (configurable)
        - One cache point for system/tools
        Based on loop.py's implementation
        """
        breakpoints_remaining = self._ephemeral_breakpoints
        
        # Work backwards through messages
        for message in reversed(messages):
            if message["role"] == "user" and isinstance(
                content := message["content"], list
            ):
                if breakpoints_remaining:
                    breakpoints_remaining -= 1
                    content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                        {"type": "ephemeral"}
                    )
                else:
                    # Remove cache control for older messages
                    content[-1].pop("cache_control", None)
                    break

        return messages

    def update_conversation_state(
        self,
        user_message: Dict[str, Any],
        assistant_message: List[BetaContentBlockParam]
    ) -> None:
        """Update conversation state after successful exchange."""
        self.last_user_message = user_message
        self.last_assistant_message = assistant_message

    def clear(self) -> None:
        """Clear cache state."""
        self.last_user_message = None
        self.last_assistant_message = None
        self.stats = CacheStats()