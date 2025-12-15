"""
Configuration management for Dimpressionist.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class AppConfig:
    """Application configuration."""

    # Paths
    output_dir: str = "./outputs"
    thumbnails_dir: str = "./outputs/thumbnails"

    # Model settings
    model_id: str = "black-forest-labs/FLUX.1-dev"
    device: str = "cuda"

    # Default generation parameters
    default_steps: int = 28
    default_guidance_scale: float = 3.5
    default_strength: float = 0.6
    default_width: int = 1024
    default_height: int = 1024

    # Limits
    max_steps: int = 100
    min_steps: int = 10
    max_width: int = 2048
    max_height: int = 2048
    min_width: int = 256
    min_height: int = 256
    max_prompt_length: int = 500

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list = field(default_factory=lambda: ["*"])

    # Feature flags
    enable_thumbnails: bool = True
    thumbnail_size: int = 120

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config from environment variables."""
        return cls(
            output_dir=os.getenv("DIMP_OUTPUT_DIR", "./outputs"),
            thumbnails_dir=os.getenv("DIMP_THUMBNAILS_DIR", "./outputs/thumbnails"),
            model_id=os.getenv("DIMP_MODEL_ID", "black-forest-labs/FLUX.1-dev"),
            device=os.getenv("DIMP_DEVICE", "cuda"),
            default_steps=int(os.getenv("DIMP_DEFAULT_STEPS", "28")),
            default_guidance_scale=float(os.getenv("DIMP_DEFAULT_GUIDANCE", "3.5")),
            default_strength=float(os.getenv("DIMP_DEFAULT_STRENGTH", "0.6")),
            default_width=int(os.getenv("DIMP_DEFAULT_WIDTH", "1024")),
            default_height=int(os.getenv("DIMP_DEFAULT_HEIGHT", "1024")),
            host=os.getenv("DIMP_HOST", "127.0.0.1"),
            port=int(os.getenv("DIMP_PORT", "8000")),
        )

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        """Load config from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, path: str) -> None:
        """Save config to JSON file."""
        data = {
            "output_dir": self.output_dir,
            "thumbnails_dir": self.thumbnails_dir,
            "model_id": self.model_id,
            "device": self.device,
            "default_steps": self.default_steps,
            "default_guidance_scale": self.default_guidance_scale,
            "default_strength": self.default_strength,
            "default_width": self.default_width,
            "default_height": self.default_height,
            "max_steps": self.max_steps,
            "min_steps": self.min_steps,
            "max_width": self.max_width,
            "max_height": self.max_height,
            "min_width": self.min_width,
            "min_height": self.min_height,
            "max_prompt_length": self.max_prompt_length,
            "host": self.host,
            "port": self.port,
            "cors_origins": self.cors_origins,
            "enable_thumbnails": self.enable_thumbnails,
            "thumbnail_size": self.thumbnail_size,
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        if self.enable_thumbnails:
            Path(self.thumbnails_dir).mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def set_config(config: AppConfig) -> None:
    """Set the global config instance."""
    global _config
    _config = config
