"""
Core generation engine for Dimpressionist.

Handles image generation using FLUX.1-dev with txt2img and img2img pipelines.
"""

import time
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

import torch
from PIL import Image

from .session import SessionManager, SessionState, GenerationEntry
from .prompt_interpreter import interpret_modification


# Type for progress callback: (step: int, total_steps: int, elapsed: float) -> None
ProgressCallback = Callable[[int, int, float], None]


class GenerationConfig:
    """Configuration for image generation."""

    def __init__(
        self,
        steps: int = 28,
        guidance_scale: float = 3.5,
        width: int = 1024,
        height: int = 1024,
        strength: float = 0.6,
        seed: Optional[int] = None
    ):
        self.steps = steps
        self.guidance_scale = guidance_scale
        self.width = width
        self.height = height
        self.strength = strength
        self.seed = seed

    def to_dict(self) -> dict:
        return {
            "steps": self.steps,
            "guidance_scale": self.guidance_scale,
            "width": self.width,
            "height": self.height,
            "strength": self.strength,
            "seed": self.seed
        }


class GenerationResult:
    """Result of an image generation."""

    def __init__(
        self,
        image: Image.Image,
        entry: GenerationEntry,
        image_path: Path
    ):
        self.image = image
        self.entry = entry
        self.image_path = image_path

    @property
    def id(self) -> str:
        return self.entry.id

    @property
    def prompt(self) -> str:
        return self.entry.prompt

    @property
    def seed(self) -> int:
        return self.entry.seed


class ConversationalImageGenerator:
    """
    Main class for conversational image generation.

    Supports:
    - Text-to-image generation
    - Image-to-image refinement
    - Session persistence
    - Progress callbacks
    """

    def __init__(
        self,
        output_dir: str = "./outputs",
        model_id: str = "black-forest-labs/FLUX.1-dev",
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.bfloat16,
        load_models: bool = True
    ):
        """
        Initialize the generator.

        Args:
            output_dir: Directory for output images and session data
            model_id: Hugging Face model ID for FLUX
            device: Device to run on ("cuda" or "cpu")
            torch_dtype: Torch data type for model
            load_models: Whether to load models on init (set False for testing)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model_id = model_id
        self.device = device
        self.torch_dtype = torch_dtype

        # Session management
        self.session_manager = SessionManager(self.output_dir / "session.json")

        # Pipelines (lazy loaded)
        self._txt2img_pipe = None
        self._img2img_pipe = None
        self._models_loaded = False

        # Progress callback
        self._progress_callback: Optional[ProgressCallback] = None

        if load_models:
            self.load_models()

    @property
    def session(self) -> SessionState:
        """Get current session."""
        return self.session_manager.session

    @property
    def current_image_path(self) -> Optional[Path]:
        """Get path to current image."""
        gen = self.session.current_generation
        if gen:
            return Path(gen.image_path)
        return None

    @property
    def current_prompt(self) -> Optional[str]:
        """Get current prompt."""
        gen = self.session.current_generation
        return gen.prompt if gen else None

    @property
    def current_seed(self) -> Optional[int]:
        """Get current seed."""
        gen = self.session.current_generation
        return gen.seed if gen else None

    def load_models(self) -> None:
        """Load the FLUX pipelines."""
        if self._models_loaded:
            return

        from diffusers import FluxPipeline, FluxImg2ImgPipeline

        print("Loading FLUX.1-dev text-to-image pipeline...")
        self._txt2img_pipe = FluxPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype
        )
        self._txt2img_pipe.to(self.device)

        print("Loading FLUX.1-dev image-to-image pipeline...")
        self._img2img_pipe = FluxImg2ImgPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype
        )
        self._img2img_pipe.to(self.device)

        self._models_loaded = True
        print("Models loaded successfully!")

    def set_progress_callback(self, callback: Optional[ProgressCallback]) -> None:
        """Set a callback for generation progress updates."""
        self._progress_callback = callback

    def _create_progress_callback(self, start_time: float):
        """Create a callback function for pipeline progress."""
        def callback(pipe, step, timestep, callback_kwargs):
            if self._progress_callback:
                elapsed = time.time() - start_time
                # Note: total_steps comes from the pipeline's num_inference_steps
                total = getattr(pipe, '_num_timesteps', 28)
                self._progress_callback(step, total, elapsed)
            return callback_kwargs
        return callback

    def generate_new(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        Generate a new image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            config: Generation configuration (optional)

        Returns:
            GenerationResult with the generated image and metadata
        """
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        config = config or GenerationConfig()

        # Generate seed if not provided
        seed = config.seed
        if seed is None:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()

        generator = torch.Generator(self.device).manual_seed(seed)

        start_time = time.time()

        # Generate image
        result = self._txt2img_pipe(
            prompt,
            guidance_scale=config.guidance_scale,
            num_inference_steps=config.steps,
            width=config.width,
            height=config.height,
            generator=generator,
            callback_on_step_end=self._create_progress_callback(start_time)
        )
        image = result.images[0]

        generation_time = time.time() - start_time

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{timestamp}_{seed}.png"
        image_path = self.output_dir / filename
        image.save(image_path)

        # Create generation entry
        entry = GenerationEntry.create_new(
            prompt=prompt,
            seed=seed,
            steps=config.steps,
            guidance_scale=config.guidance_scale,
            image_path=str(image_path),
            width=config.width,
            height=config.height,
            generation_time=generation_time
        )

        # Update session
        self.session.add_generation(entry)
        self.session_manager.save()

        return GenerationResult(image, entry, image_path)

    def refine(
        self,
        modification: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        Refine the current image based on a modification request.

        Args:
            modification: Natural language description of the desired change
            config: Generation configuration (optional)

        Returns:
            GenerationResult with the refined image and metadata

        Raises:
            ValueError: If there's no current image to refine
        """
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        current = self.session.current_generation
        if not current:
            raise ValueError("No current image to refine. Generate one first.")

        config = config or GenerationConfig()

        # Use current seed for consistency
        seed = config.seed if config.seed is not None else current.seed
        generator = torch.Generator(self.device).manual_seed(seed)

        # Interpret the modification
        new_prompt = interpret_modification(current.prompt, modification)

        # Load current image
        current_image = Image.open(current.image_path)
        current_image = current_image.resize(
            (config.width, config.height),
            Image.Resampling.LANCZOS
        )

        start_time = time.time()

        # Generate refined image
        result = self._img2img_pipe(
            prompt=new_prompt,
            image=current_image,
            strength=config.strength,
            guidance_scale=config.guidance_scale,
            num_inference_steps=config.steps,
            generator=generator,
            callback_on_step_end=self._create_progress_callback(start_time)
        )
        image = result.images[0]

        generation_time = time.time() - start_time

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{timestamp}_{seed}_refined.png"
        image_path = self.output_dir / filename
        image.save(image_path)

        # Create generation entry
        entry = GenerationEntry.create_refinement(
            prompt=new_prompt,
            modification=modification,
            seed=seed,
            steps=config.steps,
            guidance_scale=config.guidance_scale,
            strength=config.strength,
            image_path=str(image_path),
            parent_id=current.id,
            width=config.width,
            height=config.height,
            generation_time=generation_time
        )

        # Update session
        self.session.add_generation(entry)
        self.session_manager.save()

        return GenerationResult(image, entry, image_path)

    def get_history(self) -> list[GenerationEntry]:
        """Get generation history."""
        return self.session.generations.copy()

    def get_current(self) -> Optional[GenerationEntry]:
        """Get current generation entry."""
        return self.session.current_generation

    def clear_session(self) -> None:
        """Clear the current session."""
        self.session_manager.clear()

    def save_session(self) -> None:
        """Save the current session to disk."""
        self.session_manager.save()

    def load_session(self) -> None:
        """Load session from disk."""
        self.session_manager._session = self.session_manager.load()


# Singleton instance for convenience
_generator_instance: Optional[ConversationalImageGenerator] = None


def get_generator(
    output_dir: str = "./outputs",
    load_models: bool = True
) -> ConversationalImageGenerator:
    """
    Get or create the global generator instance.

    Args:
        output_dir: Output directory for images
        load_models: Whether to load models

    Returns:
        ConversationalImageGenerator instance
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ConversationalImageGenerator(
            output_dir=output_dir,
            load_models=load_models
        )
    return _generator_instance
