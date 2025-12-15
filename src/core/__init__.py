"""
Core module for Dimpressionist - conversational image generation.
"""

from .generator import (
    ConversationalImageGenerator,
    GenerationConfig,
    GenerationResult,
    get_generator,
)
from .session import (
    GenerationEntry,
    SessionState,
    SessionManager,
)
from .prompt_interpreter import (
    PromptInterpreter,
    RuleBasedInterpreter,
    interpret_modification,
)

__all__ = [
    "ConversationalImageGenerator",
    "GenerationConfig",
    "GenerationResult",
    "get_generator",
    "GenerationEntry",
    "SessionState",
    "SessionManager",
    "PromptInterpreter",
    "RuleBasedInterpreter",
    "interpret_modification",
]
