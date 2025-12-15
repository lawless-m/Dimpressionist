"""
Prompt interpreter for converting natural language modifications into effective prompts.

v1: Rule-based interpretation
v2 (future): LLM-powered interpretation
"""

import re
from typing import Optional, Tuple
from abc import ABC, abstractmethod


class PromptInterpreter(ABC):
    """Base class for prompt interpretation."""

    @abstractmethod
    def interpret(self, current_prompt: str, modification: str) -> str:
        """
        Interpret a modification request and return an updated prompt.

        Args:
            current_prompt: The current image prompt
            modification: The user's modification request

        Returns:
            Updated prompt incorporating the modification
        """
        pass


class RuleBasedInterpreter(PromptInterpreter):
    """
    Rule-based prompt interpreter using keyword matching and patterns.

    Supports:
    - Color changes: "make X red", "change the color to blue"
    - Additions: "add X", "include X"
    - Style changes: "change to X style", "make it X style"
    - Object replacements: "make the X a Y", "replace X with Y"
    - Removals: "remove X", "without X"
    - Background changes: "change background to X"
    - General modifications: Appended to prompt
    """

    COLORS = [
        'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink',
        'black', 'white', 'brown', 'grey', 'gray', 'cyan', 'magenta',
        'gold', 'silver', 'bronze', 'crimson', 'navy', 'teal', 'coral',
        'violet', 'indigo', 'turquoise', 'maroon', 'olive', 'beige'
    ]

    STYLES = [
        'photorealistic', 'realistic', 'cartoon', 'anime', 'sketch',
        'watercolor', 'oil painting', 'digital art', 'pixel art',
        'impressionist', 'surrealist', 'minimalist', 'abstract',
        'vintage', 'retro', 'modern', 'futuristic', 'cyberpunk',
        'steampunk', 'fantasy', 'gothic', 'baroque', 'renaissance',
        'pop art', 'art nouveau', 'art deco', 'comic book', 'manga'
    ]

    def __init__(self):
        # Compile regex patterns for efficiency
        self._color_pattern = re.compile(
            r'\b(' + '|'.join(self.COLORS) + r')\b', re.IGNORECASE
        )
        self._make_pattern = re.compile(
            r'make\s+(?:the\s+)?(\w+)\s+(\w+)', re.IGNORECASE
        )
        self._change_to_pattern = re.compile(
            r'change\s+(?:the\s+)?(?:(\w+)\s+)?to\s+(.+)', re.IGNORECASE
        )
        self._add_pattern = re.compile(
            r'(?:add|include|put)\s+(.+)', re.IGNORECASE
        )
        self._remove_pattern = re.compile(
            r'(?:remove|delete|take away|get rid of)\s+(?:the\s+)?(.+)', re.IGNORECASE
        )
        self._replace_pattern = re.compile(
            r'replace\s+(?:the\s+)?(\w+)\s+with\s+(.+)', re.IGNORECASE
        )
        self._background_pattern = re.compile(
            r'(?:change|set|make)\s+(?:the\s+)?background\s+(?:to\s+)?(.+)', re.IGNORECASE
        )
        self._style_pattern = re.compile(
            r'(?:change\s+to|make\s+it|in)\s+(.+?)\s*style', re.IGNORECASE
        )

    def interpret(self, current_prompt: str, modification: str) -> str:
        """Interpret modification and return updated prompt."""
        mod_lower = modification.lower().strip()

        # Try each interpretation strategy in order of specificity
        result = self._try_color_change(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_style_change(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_background_change(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_replacement(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_addition(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_removal(current_prompt, modification, mod_lower)
        if result:
            return result

        result = self._try_make_pattern(current_prompt, modification, mod_lower)
        if result:
            return result

        # Default: append modification to prompt
        return self._append_modification(current_prompt, modification)

    def _try_color_change(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as a color change."""
        # Find color in modification
        color_match = self._color_pattern.search(mod_lower)
        if not color_match:
            return None

        new_color = color_match.group(1).lower()

        # Check if there's an existing color in the prompt to replace
        existing_colors = self._color_pattern.findall(current_prompt.lower())
        if existing_colors:
            # Replace the first color found
            result = current_prompt
            for old_color in existing_colors:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(old_color), re.IGNORECASE)
                result = pattern.sub(new_color, result, count=1)
                break
            return result

        # No existing color, append the modification
        return None

    def _try_style_change(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as a style change."""
        match = self._style_pattern.search(modification)
        if match:
            new_style = match.group(1).strip()
            # Remove existing style references
            result = current_prompt
            for style in self.STYLES:
                pattern = re.compile(
                    r',?\s*(?:in\s+)?' + re.escape(style) + r'\s*style',
                    re.IGNORECASE
                )
                result = pattern.sub('', result)
            # Add new style
            return f"{result.strip()}, in {new_style} style"

        # Check for direct style mentions without "style" keyword
        for style in self.STYLES:
            if style in mod_lower and ('make it' in mod_lower or 'more' in mod_lower):
                return f"{current_prompt}, {style}"

        return None

    def _try_background_change(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as a background change."""
        match = self._background_pattern.search(modification)
        if match:
            new_bg = match.group(1).strip()
            # Remove existing background references
            result = re.sub(
                r',?\s*(?:with\s+)?(?:a\s+)?[\w\s]+\s+background',
                '',
                current_prompt,
                flags=re.IGNORECASE
            )
            return f"{result.strip()}, with {new_bg} background"
        return None

    def _try_replacement(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as an object replacement."""
        match = self._replace_pattern.search(modification)
        if match:
            old_obj = match.group(1)
            new_obj = match.group(2).strip()
            pattern = re.compile(r'\b' + re.escape(old_obj) + r'\b', re.IGNORECASE)
            if pattern.search(current_prompt):
                return pattern.sub(new_obj, current_prompt)
        return None

    def _try_addition(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as an addition."""
        match = self._add_pattern.search(modification)
        if match:
            addition = match.group(1).strip()
            return f"{current_prompt}, with {addition}"
        return None

    def _try_removal(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret as a removal."""
        match = self._remove_pattern.search(modification)
        if match:
            to_remove = match.group(1).strip()
            # Try to remove from prompt
            pattern = re.compile(
                r',?\s*(?:with\s+)?(?:a\s+)?' + re.escape(to_remove),
                re.IGNORECASE
            )
            result = pattern.sub('', current_prompt)
            if result != current_prompt:
                return result.strip()
            # If not found, add "without" clause
            return f"{current_prompt}, without {to_remove}"
        return None

    def _try_make_pattern(
        self, current_prompt: str, modification: str, mod_lower: str
    ) -> Optional[str]:
        """Try to interpret 'make X Y' patterns."""
        match = self._make_pattern.search(modification)
        if match:
            subject = match.group(1)
            attribute = match.group(2)

            # Check if attribute is a color
            if attribute.lower() in self.COLORS:
                # Try to find and modify the subject's color
                pattern = re.compile(
                    r'(\b\w+\s+)?' + re.escape(subject),
                    re.IGNORECASE
                )
                match_in_prompt = pattern.search(current_prompt)
                if match_in_prompt:
                    # Check if there's an adjective (possibly a color) before the subject
                    prefix = match_in_prompt.group(1)
                    if prefix and prefix.strip().lower() in self.COLORS:
                        # Replace the color
                        return current_prompt.replace(
                            prefix.strip(),
                            attribute,
                            1
                        )

            # General "make X Y" - append as modification
            return f"{current_prompt}, {modification}"
        return None

    def _append_modification(self, current_prompt: str, modification: str) -> str:
        """Append modification to the prompt."""
        # Clean up the modification
        mod_clean = modification.strip()

        # Remove common prefixes that don't add meaning
        prefixes_to_remove = [
            'please ', 'can you ', 'i want to ', 'i would like to ',
            'could you ', 'try to '
        ]
        mod_lower = mod_clean.lower()
        for prefix in prefixes_to_remove:
            if mod_lower.startswith(prefix):
                mod_clean = mod_clean[len(prefix):]
                break

        return f"{current_prompt}, {mod_clean}"


# Default interpreter instance
default_interpreter = RuleBasedInterpreter()


def interpret_modification(current_prompt: str, modification: str) -> str:
    """
    Convenience function to interpret a modification using the default interpreter.

    Args:
        current_prompt: The current image prompt
        modification: The user's modification request

    Returns:
        Updated prompt incorporating the modification
    """
    return default_interpreter.interpret(current_prompt, modification)
