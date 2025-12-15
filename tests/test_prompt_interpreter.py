"""
Unit tests for prompt interpreter.
"""

import pytest
from src.core.prompt_interpreter import RuleBasedInterpreter, interpret_modification


@pytest.fixture
def interpreter():
    return RuleBasedInterpreter()


class TestColorChanges:
    """Tests for color modification interpretation."""

    def test_simple_color_replacement(self, interpreter):
        """Test replacing a color in the prompt."""
        result = interpreter.interpret("a blue ball", "make it red")
        assert "red" in result.lower()

    def test_color_in_modification(self, interpreter):
        """Test color detection in modification."""
        result = interpreter.interpret("a ball on grass", "make the ball red")
        assert "red" in result.lower()

    def test_multiple_colors(self, interpreter):
        """Test with multiple colors in prompt."""
        result = interpreter.interpret("a blue ball on green grass", "make the ball red")
        assert "red" in result.lower() or "ball red" in result.lower()


class TestStyleChanges:
    """Tests for style modification interpretation."""

    def test_style_change(self, interpreter):
        """Test changing to a specific style."""
        result = interpreter.interpret("a cat", "change to watercolor style")
        assert "watercolor" in result.lower()

    def test_style_addition(self, interpreter):
        """Test adding style to prompt."""
        result = interpreter.interpret("a landscape", "make it impressionist style")
        assert "impressionist" in result.lower()


class TestAdditions:
    """Tests for addition interpretation."""

    def test_add_object(self, interpreter):
        """Test adding an object."""
        result = interpreter.interpret("a house", "add a tree")
        assert "tree" in result.lower()

    def test_include_object(self, interpreter):
        """Test including an object."""
        result = interpreter.interpret("a portrait", "include a hat")
        assert "hat" in result.lower()


class TestRemovals:
    """Tests for removal interpretation."""

    def test_remove_object(self, interpreter):
        """Test removing an object."""
        result = interpreter.interpret("a cat with a hat", "remove the hat")
        assert "without" in result.lower() or "hat" not in result.lower()


class TestBackgroundChanges:
    """Tests for background modification."""

    def test_change_background(self, interpreter):
        """Test changing background."""
        result = interpreter.interpret("a person", "change background to sunset")
        assert "sunset" in result.lower()
        assert "background" in result.lower()


class TestDefaultBehavior:
    """Tests for default fallback behavior."""

    def test_unknown_modification(self, interpreter):
        """Test unknown modification appends to prompt."""
        result = interpreter.interpret("a cat", "make it more fluffy")
        assert "fluffy" in result.lower()
        assert "cat" in result.lower()


class TestConvenienceFunction:
    """Tests for the convenience function."""

    def test_interpret_modification(self):
        """Test the module-level convenience function."""
        result = interpret_modification("a dog", "add spots")
        assert "spots" in result.lower()
        assert "dog" in result.lower()
