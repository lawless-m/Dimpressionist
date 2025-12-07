"""
Session management and data models for Dimpressionist.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Literal


@dataclass
class GenerationEntry:
    """Represents a single image generation event."""
    id: str
    timestamp: str
    type: Literal["new", "refinement"]
    prompt: str
    seed: int
    steps: int
    guidance_scale: float
    image_path: str
    width: int = 1024
    height: int = 1024
    modification: Optional[str] = None
    strength: Optional[float] = None
    parent_id: Optional[str] = None
    generation_time: Optional[float] = None

    @classmethod
    def create_new(
        cls,
        prompt: str,
        seed: int,
        steps: int,
        guidance_scale: float,
        image_path: str,
        width: int = 1024,
        height: int = 1024,
        generation_time: Optional[float] = None
    ) -> "GenerationEntry":
        """Create a new generation entry."""
        return cls(
            id=f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            type="new",
            prompt=prompt,
            seed=seed,
            steps=steps,
            guidance_scale=guidance_scale,
            image_path=image_path,
            width=width,
            height=height,
            generation_time=generation_time
        )

    @classmethod
    def create_refinement(
        cls,
        prompt: str,
        modification: str,
        seed: int,
        steps: int,
        guidance_scale: float,
        strength: float,
        image_path: str,
        parent_id: str,
        width: int = 1024,
        height: int = 1024,
        generation_time: Optional[float] = None
    ) -> "GenerationEntry":
        """Create a refinement entry."""
        return cls(
            id=f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_refined",
            timestamp=datetime.now().isoformat(),
            type="refinement",
            prompt=prompt,
            modification=modification,
            seed=seed,
            steps=steps,
            guidance_scale=guidance_scale,
            strength=strength,
            image_path=image_path,
            parent_id=parent_id,
            width=width,
            height=height,
            generation_time=generation_time
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationEntry":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SessionState:
    """Manages the current session state."""
    session_id: str
    created_at: str
    updated_at: str
    current_generation_id: Optional[str] = None
    generations: List[GenerationEntry] = field(default_factory=list)

    @classmethod
    def create_new(cls) -> "SessionState":
        """Create a new session."""
        now = datetime.now().isoformat()
        return cls(
            session_id=f"sess_{uuid.uuid4().hex[:12]}",
            created_at=now,
            updated_at=now
        )

    @property
    def current_generation(self) -> Optional[GenerationEntry]:
        """Get the current generation entry."""
        if not self.current_generation_id:
            return None
        for gen in self.generations:
            if gen.id == self.current_generation_id:
                return gen
        return None

    @property
    def generation_count(self) -> int:
        """Get total number of generations."""
        return len(self.generations)

    def add_generation(self, entry: GenerationEntry) -> None:
        """Add a generation and set it as current."""
        self.generations.append(entry)
        self.current_generation_id = entry.id
        self.updated_at = datetime.now().isoformat()

    def clear(self) -> None:
        """Clear all generations."""
        self.generations = []
        self.current_generation_id = None
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_generation_id": self.current_generation_id,
            "generations": [g.to_dict() for g in self.generations]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create from dictionary."""
        generations = [GenerationEntry.from_dict(g) for g in data.get("generations", [])]
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            current_generation_id=data.get("current_generation_id"),
            generations=generations
        )


class SessionManager:
    """Handles session persistence to disk."""

    def __init__(self, session_file: Path):
        self.session_file = Path(session_file)
        self._session: Optional[SessionState] = None

    @property
    def session(self) -> SessionState:
        """Get or create the current session."""
        if self._session is None:
            self._session = self.load()
        return self._session

    def load(self) -> SessionState:
        """Load session from file or create new."""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                return SessionState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load session file: {e}")
        return SessionState.create_new()

    def save(self) -> None:
        """Save current session to file."""
        if self._session:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(self._session.to_dict(), f, indent=2)

    def clear(self) -> None:
        """Clear the session and delete file."""
        if self._session:
            self._session.clear()
        if self.session_file.exists():
            self.session_file.unlink()
        self._session = SessionState.create_new()
