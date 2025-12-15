"""
Unit tests for session management.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.session import GenerationEntry, SessionState, SessionManager


class TestGenerationEntry:
    """Tests for GenerationEntry dataclass."""

    def test_create_new(self):
        """Test creating a new generation entry."""
        entry = GenerationEntry.create_new(
            prompt="a cat",
            seed=42,
            steps=28,
            guidance_scale=3.5,
            image_path="/tmp/test.png"
        )

        assert entry.type == "new"
        assert entry.prompt == "a cat"
        assert entry.seed == 42
        assert entry.steps == 28
        assert entry.modification is None
        assert entry.parent_id is None
        assert entry.id.startswith("gen_")

    def test_create_refinement(self):
        """Test creating a refinement entry."""
        entry = GenerationEntry.create_refinement(
            prompt="a red cat",
            modification="make it red",
            seed=42,
            steps=28,
            guidance_scale=3.5,
            strength=0.6,
            image_path="/tmp/test_refined.png",
            parent_id="gen_parent"
        )

        assert entry.type == "refinement"
        assert entry.modification == "make it red"
        assert entry.parent_id == "gen_parent"
        assert entry.strength == 0.6
        assert "_refined" in entry.id

    def test_to_dict(self):
        """Test serialization to dict."""
        entry = GenerationEntry.create_new(
            prompt="test",
            seed=1,
            steps=10,
            guidance_scale=3.0,
            image_path="/tmp/test.png"
        )
        data = entry.to_dict()

        assert data["prompt"] == "test"
        assert data["seed"] == 1
        assert data["type"] == "new"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "test_id",
            "timestamp": "2024-01-01T00:00:00",
            "type": "new",
            "prompt": "test",
            "seed": 1,
            "steps": 10,
            "guidance_scale": 3.0,
            "image_path": "/tmp/test.png",
            "width": 1024,
            "height": 1024,
            "modification": None,
            "strength": None,
            "parent_id": None,
            "generation_time": None
        }
        entry = GenerationEntry.from_dict(data)

        assert entry.id == "test_id"
        assert entry.prompt == "test"


class TestSessionState:
    """Tests for SessionState dataclass."""

    def test_create_new(self):
        """Test creating a new session."""
        session = SessionState.create_new()

        assert session.session_id.startswith("sess_")
        assert session.generation_count == 0
        assert session.current_generation is None

    def test_add_generation(self):
        """Test adding a generation."""
        session = SessionState.create_new()
        entry = GenerationEntry.create_new(
            prompt="test",
            seed=1,
            steps=10,
            guidance_scale=3.0,
            image_path="/tmp/test.png"
        )

        session.add_generation(entry)

        assert session.generation_count == 1
        assert session.current_generation_id == entry.id
        assert session.current_generation == entry

    def test_clear(self):
        """Test clearing session."""
        session = SessionState.create_new()
        entry = GenerationEntry.create_new(
            prompt="test",
            seed=1,
            steps=10,
            guidance_scale=3.0,
            image_path="/tmp/test.png"
        )
        session.add_generation(entry)

        session.clear()

        assert session.generation_count == 0
        assert session.current_generation is None

    def test_serialization(self):
        """Test JSON serialization round-trip."""
        session = SessionState.create_new()
        entry = GenerationEntry.create_new(
            prompt="test",
            seed=1,
            steps=10,
            guidance_scale=3.0,
            image_path="/tmp/test.png"
        )
        session.add_generation(entry)

        data = session.to_dict()
        restored = SessionState.from_dict(data)

        assert restored.session_id == session.session_id
        assert restored.generation_count == 1
        assert restored.current_generation_id == entry.id


class TestSessionManager:
    """Tests for SessionManager."""

    def test_load_nonexistent(self):
        """Test loading when file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            manager = SessionManager(Path(tmpdir) / "session.json")
            session = manager.load()

            assert session is not None
            assert session.generation_count == 0

    def test_save_and_load(self):
        """Test saving and loading session."""
        with TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "session.json"
            manager = SessionManager(session_file)

            # Add a generation
            entry = GenerationEntry.create_new(
                prompt="test",
                seed=1,
                steps=10,
                guidance_scale=3.0,
                image_path="/tmp/test.png"
            )
            manager.session.add_generation(entry)
            manager.save()

            # Load in new manager
            manager2 = SessionManager(session_file)
            loaded = manager2.load()

            assert loaded.generation_count == 1
            assert loaded.generations[0].prompt == "test"

    def test_clear(self):
        """Test clearing session."""
        with TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "session.json"
            manager = SessionManager(session_file)

            entry = GenerationEntry.create_new(
                prompt="test",
                seed=1,
                steps=10,
                guidance_scale=3.0,
                image_path="/tmp/test.png"
            )
            manager.session.add_generation(entry)
            manager.save()

            manager.clear()

            assert not session_file.exists()
            assert manager.session.generation_count == 0
