"""
Core generation engine for Dimpressionist.

Handles image generation using FLUX.1 models with txt2img and img2img pipelines.
"""

import time
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

import torch
from PIL import Image

from .session import SessionManager, SessionState, GenerationEntry
# Prompt interpreter removed - refinements are just new generations now


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
        strength: float = 0.75,  # Higher strength allows prompt changes to actually show
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
        model_id: str = "black-forest-labs/FLUX.1-schnell",
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.bfloat16,
        load_models: bool = True,
        session_id: Optional[str] = None
    ):
        """
        Initialize the generator.

        Args:
            output_dir: Directory for output images and session data
            model_id: Hugging Face model ID for FLUX
            device: Device to run on ("cuda" or "cpu")
            torch_dtype: Torch data type for model
            load_models: Whether to load models on init (set False for testing)
            session_id: Unique session ID for this user (if None, uses 'default')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model_id = model_id
        self.device = device
        self.torch_dtype = torch_dtype

        # Session management - per-user sessions for privacy
        self.session_id = session_id or "default"
        session_dir = self.output_dir / "sessions"
        self.session_manager = SessionManager(session_dir, self.session_id)

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

    def _request_gpu_unload(self, services: list[str]) -> None:
        """Request other services to unload their models (Service Signaling Protocol)."""
        import requests

        for service in services:
            try:
                print(f"🔄 Requesting {service} to unload...")
                resp = requests.post(f"{service}/request-unload", timeout=5)
                result = resp.json()
                if result.get("unloaded"):
                    print(f"✓ {service} unloaded")
                elif result.get("status") == "busy":
                    print(f"⏱ {service} busy (idle {result.get('idle_seconds', 0):.0f}s)")
            except Exception as e:
                print(f"⚠️  {service} not available: {e}")

    def load_models(self, max_retries: int = 3, retry_delay: int = 30, request_unload_services: list[str] = None) -> None:
        """
        Load the FLUX pipelines with Service Signaling Protocol + OOM retry fallback.

        Args:
            max_retries: Number of OOM retry attempts
            retry_delay: Seconds to wait between retries
            request_unload_services: List of service URLs to request unload from
        """
        if self._models_loaded:
            return

        from diffusers import FluxPipeline, FluxImg2ImgPipeline

        # Proactively request other services to unload
        if request_unload_services:
            self._request_gpu_unload(request_unload_services)
            time.sleep(2)  # Give them a moment to unload

        for attempt in range(max_retries):
            try:
                print(f"Loading {self.model_id} text-to-image pipeline...")
                self._txt2img_pipe = FluxPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                )

                # Enable sequential CPU offloading to fit in 24GB VRAM
                print("Enabling CPU offloading for large model...")
                self._txt2img_pipe.enable_sequential_cpu_offload()

                # Also enable attention slicing to reduce memory further
                self._txt2img_pipe.enable_attention_slicing(1)

                # Note: img2img pipeline loaded on-demand to save VRAM
                # FLUX txt2img + img2img together exceed 24GB on RTX 3090
                # We load img2img only when refine() is called

                self._models_loaded = True
                print("Models loaded successfully (txt2img with CPU offloading)!")
                return

            except RuntimeError as e:
                error_msg = str(e).lower()
                if "out of memory" in error_msg or "cuda" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"⚠️  GPU OOM on attempt {attempt + 1}/{max_retries}")
                        print(f"   Waiting {retry_delay}s for other services to unload...")
                        torch.cuda.empty_cache()
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ Failed after {max_retries} attempts")
                        raise RuntimeError(
                            f"GPU OOM after {max_retries} retries. "
                            "Other services may be using GPU memory. "
                            "Wait a moment and try again."
                        ) from e
                else:
                    raise  # Not OOM, raise immediately

    def unload_models(self) -> None:
        """Unload models from GPU memory."""
        if not self._models_loaded:
            return

        print("Unloading models from GPU...")
        self._txt2img_pipe = None
        self._img2img_pipe = None
        self._models_loaded = False

        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        print("Models unloaded, GPU memory freed")

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

        try:
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

        except RuntimeError as e:
            # Clean up GPU memory on error
            if "out of memory" in str(e).lower():
                print("⚠️  GPU OOM during generation, cleaning up...")
                torch.cuda.empty_cache()
            raise

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
