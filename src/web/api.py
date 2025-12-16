"""
FastAPI server for Dimpressionist.

Provides REST API and WebSocket interface for image generation.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Cookie, Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import secrets

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import ConversationalImageGenerator, GenerationConfig, GenerationEntry
from src.utils import get_config, create_thumbnail
from src.web.websocket import ConnectionManager, broadcast_progress


# Pydantic models for API
class GenerateNewRequest(BaseModel):
    """Request model for new image generation."""
    prompt: str = Field(..., min_length=1, max_length=500)
    steps: int = Field(8, ge=4, le=100)  # FLUX.1-schnell works with 4+ steps
    guidance_scale: float = Field(3.5, ge=1.0, le=5.0)
    seed: Optional[int] = None
    width: int = Field(512, ge=256, le=2048)
    height: int = Field(512, ge=256, le=2048)


class RefineRequest(BaseModel):
    """Request model for image refinement."""
    modification: str = Field(..., min_length=1, max_length=500)
    strength: float = Field(0.75, ge=0.1, le=1.0)
    steps: int = Field(8, ge=4, le=100)
    guidance_scale: float = Field(3.5, ge=1.0, le=5.0)


class GenerationResponse(BaseModel):
    """Response model for generation results."""
    id: str
    image_url: str
    thumbnail_url: Optional[str] = None
    metadata: dict


class SessionResponse(BaseModel):
    """Response model for session info."""
    session_id: str
    current_image: Optional[dict] = None
    generation_count: int
    created_at: str
    updated_at: str


class HistoryResponse(BaseModel):
    """Response model for history."""
    total: int
    limit: int
    offset: int
    generations: List[dict]


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    model: str
    default_parameters: dict
    limits: dict
    features: dict


class StatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    model_loaded: bool
    version: str


# Global state
generators: dict[str, ConversationalImageGenerator] = {}  # Per-session generators for privacy
manager = ConnectionManager()
is_generating = False
last_request_time: Optional[float] = None
auto_unload_minutes = 5  # Auto-unload after 5 minutes idle
event_loop: Optional[asyncio.AbstractEventLoop] = None  # Store event loop for thread-safe async calls
config: Optional[any] = None  # Global config

# Other GPU services to request unload from (Service Signaling Protocol)
GPU_SERVICES = [
    "http://10.99.0.3:8765",  # Invoice OCR (Qwen2-VL)
]


def get_session_id(session_id: Optional[str] = Cookie(None, alias="dimp_session")) -> str:
    """
    Get or create session ID from cookie.
    Returns existing session_id or generates a new one.
    """
    if session_id:
        return session_id
    # Generate new session ID
    return secrets.token_urlsafe(16)


def get_generator(session_id: str) -> ConversationalImageGenerator:
    """
    Get or create generator for this session.
    Each session gets its own isolated generator and image history.
    """
    global generators, config

    if session_id not in generators:
        # Create new generator for this session
        generators[session_id] = ConversationalImageGenerator(
            output_dir=config.output_dir,
            model_id=config.model_id,
            device=config.device,
            load_models=False,
            session_id=session_id
        )
        print(f"Created new session: {session_id}")

    return generators[session_id]


async def auto_unload_task():
    """Background task that auto-unloads models after idle timeout."""
    global generators, last_request_time

    while True:
        await asyncio.sleep(60)  # Check every minute

        if last_request_time is None:
            continue

        idle = time.time() - last_request_time
        if idle > (auto_unload_minutes * 60):
            # Unload all loaded models
            loaded_gens = [gen for gen in generators.values() if gen._models_loaded]
            if loaded_gens:
                print(f"💤 Auto-unloading {len(loaded_gens)} model(s) after {idle/60:.1f} minutes idle")
                for gen in loaded_gens:
                    gen.unload_models()


async def _estimate_progress(manager: ConnectionManager, total_steps: int, start_time: float, session_id: str):
    """
    Estimate generation progress based on time elapsed.
    Used when callback_on_step_end doesn't work (e.g., with CPU offloading).
    """
    # Estimated time per step based on measurements
    # ~6.7 seconds per step with CPU offloading at 1024x1024
    # Scales roughly with pixel count: 512x512 is ~4x faster than 1024x1024
    estimated_time_per_step = 6.7  # Will be adjusted dynamically based on actual timing

    try:
        while True:
            elapsed = time.time() - start_time
            estimated_step = min(int(elapsed / estimated_time_per_step), total_steps - 1)

            await broadcast_progress(
                manager,
                step=estimated_step,
                total_steps=total_steps,
                elapsed=elapsed,
                status="generating",
                session_id=session_id
            )

            await asyncio.sleep(2)  # Update every 2 seconds

    except asyncio.CancelledError:
        pass  # Task cancelled when generation completes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global config, event_loop
    config = get_config()

    # Store event loop for thread-safe async calls
    event_loop = asyncio.get_running_loop()

    print("Starting Dimpressionist API server...")
    print(f"Output directory: {config.output_dir}")
    print(f"Auto-unload: {auto_unload_minutes} minutes idle")
    print("Per-user sessions enabled for privacy")

    # Generators created on-demand per session

    # Start auto-unload background task
    unload_task = asyncio.create_task(auto_unload_task())

    yield

    # Cleanup
    print("Shutting down...")
    unload_task.cancel()


# Create FastAPI app
app = FastAPI(
    title="Dimpressionist API",
    description="Conversational Image Generation API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to ensure all errors return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch all unhandled exceptions and return JSON."""
    import traceback

    # Log the full traceback
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


# Helper functions
def ensure_models_loaded(gen: ConversationalImageGenerator):
    """Ensure models are loaded for this generator."""
    from huggingface_hub.errors import GatedRepoError

    if not gen._models_loaded:
        try:
            gen.load_models(request_unload_services=GPU_SERVICES)
        except GatedRepoError as e:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Authentication required",
                    "message": "HuggingFace authentication required to download model. Please run: huggingface-cli login",
                    "model": gen.model_id,
                    "instructions": "Visit https://huggingface.co/settings/tokens to create a token, then run 'huggingface-cli login' on the server."
                }
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "Authentication required",
                        "message": "HuggingFace authentication required to download model.",
                        "instructions": "Run 'huggingface-cli login' on the server."
                    }
                )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model loading failed",
                    "message": str(e)
                }
            )
    return gen


def entry_to_dict(entry: GenerationEntry, config) -> dict:
    """Convert GenerationEntry to API response dict."""
    image_name = Path(entry.image_path).name
    return {
        "id": entry.id,
        "type": entry.type,
        "image_url": f"/api/v1/images/{image_name}",
        "thumbnail_url": f"/api/v1/thumbnails/{Path(image_name).stem}_thumb.jpg",
        "prompt": entry.prompt,
        "modification": entry.modification,
        "parent_id": entry.parent_id,
        "timestamp": entry.timestamp,
        "metadata": {
            "prompt": entry.prompt,
            "seed": entry.seed,
            "steps": entry.steps,
            "guidance_scale": entry.guidance_scale,
            "strength": entry.strength,
            "width": entry.width,
            "height": entry.height,
            "generation_time": entry.generation_time
        }
    }


# REST Endpoints

@app.get("/api/v1/system/status", response_model=StatusResponse)
async def get_status():
    """Get system status."""
    global generators
    # Check if any generator has models loaded
    model_loaded = any(gen._models_loaded for gen in generators.values())
    return StatusResponse(
        status="operational",
        model_loaded=model_loaded,
        version="1.0.0"
    )


@app.get("/status")
async def get_status_simple():
    """Simple status endpoint for Service Signaling Protocol."""
    global last_request_time, generators
    # Check if any generator has models loaded
    model_loaded = any(gen._models_loaded for gen in generators.values())
    idle = time.time() - last_request_time if last_request_time else None
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "idle_seconds": idle,
        "auto_unload_enabled": auto_unload_minutes is not None,
        "auto_unload_minutes": auto_unload_minutes,
    }


@app.post("/request-unload")
async def request_unload():
    """Request model unload if idle (Service Signaling Protocol)."""
    global last_request_time, generators

    # Check if any generator has models loaded
    loaded_generators = [gen for gen in generators.values() if gen._models_loaded]
    if not loaded_generators:
        return {"status": "ok", "unloaded": False, "message": "No model loaded"}

    if last_request_time is None:
        idle = 0
    else:
        idle = time.time() - last_request_time

    # Only unload if idle for at least 30 seconds
    if idle < 30:
        return {
            "status": "busy",
            "unloaded": False,
            "message": f"Model in use (idle {idle:.0f}s)",
            "idle_seconds": idle,
        }

    # Unload all loaded models
    print(f"🔄 Unloading on request from another service (idle {idle:.0f}s)")
    for gen in loaded_generators:
        gen.unload_models()

    return {
        "status": "ok",
        "unloaded": True,
        "message": f"Unloaded {len(loaded_generators)} model(s)",
        "idle_seconds": idle,
    }


@app.get("/api/v1/config", response_model=ConfigResponse)
async def get_configuration():
    """Get current configuration."""
    config = get_config()
    return ConfigResponse(
        model="FLUX.1-dev",
        default_parameters={
            "steps": config.default_steps,
            "guidance_scale": config.default_guidance_scale,
            "strength": config.default_strength
        },
        limits={
            "max_steps": config.max_steps,
            "max_width": config.max_width,
            "max_height": config.max_height
        },
        features={
            "refinement": True,
            "inpainting": False,
            "batch_generation": False
        }
    )


@app.post("/api/v1/generate/new", response_model=GenerationResponse)
async def generate_new(
    request: GenerateNewRequest,
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """Generate a new image from text prompt."""
    global is_generating, last_request_time

    if is_generating:
        raise HTTPException(status_code=429, detail="Generation already in progress")

    # Track request time for auto-unload
    last_request_time = time.time()

    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)
    ensure_models_loaded(gen)

    is_generating = True
    try:
        gen_config = GenerationConfig(
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            width=request.width,
            height=request.height
        )

        # Start time-based progress estimation (callback_on_step_end doesn't work with CPU offloading)
        start_time = time.time()
        progress_task = asyncio.create_task(
            _estimate_progress(manager, gen_config.steps, start_time, session_id)
        )

        try:
            # Generate in thread pool so async progress updates can run
            import concurrent.futures
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    gen.generate_new,
                    request.prompt,
                    gen_config
                )
        finally:
            # Cancel progress estimation
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # Create thumbnail
        thumb_path = None
        if config.enable_thumbnails:
            try:
                thumb_dir = Path(config.thumbnails_dir)
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = create_thumbnail(
                    result.image_path,
                    size=config.thumbnail_size,
                    output_path=thumb_dir / f"{result.image_path.stem}_thumb.jpg"
                )
            except Exception as e:
                print(f"Warning: Could not create thumbnail: {e}")

        # Broadcast completion
        await broadcast_progress(
            manager,
            step=request.steps,
            total_steps=request.steps,
            elapsed=result.entry.generation_time or 0,
            status="complete",
            image_url=f"/api/v1/images/{result.image_path.name}",
            session_id=session_id
        )

        image_name = result.image_path.name
        return GenerationResponse(
            id=result.id,
            image_url=f"/api/v1/images/{image_name}",
            thumbnail_url=f"/api/v1/thumbnails/{result.image_path.stem}_thumb.jpg" if thumb_path else None,
            metadata={
                "prompt": result.prompt,
                "seed": result.seed,
                "steps": request.steps,
                "guidance_scale": request.guidance_scale,
                "width": request.width,
                "height": request.height,
                "generation_time": result.entry.generation_time
            }
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like auth errors) as-is
        raise
    except Exception as e:
        error_detail = {
            "error": "Generation failed",
            "message": str(e),
            "type": type(e).__name__
        }
        await broadcast_progress(
            manager,
            step=0,
            total_steps=request.steps,
            elapsed=0,
            status="error",
            error=str(e),
            session_id=session_id
        )
        raise HTTPException(status_code=500, detail=error_detail)
    finally:
        is_generating = False
        gen.set_progress_callback(None)


@app.post("/api/v1/generate/refine", response_model=GenerationResponse)
async def refine_image(
    request: RefineRequest,
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """Generate a new image with the given prompt (treating it as a new generation, not a refinement)."""
    global is_generating, last_request_time

    if is_generating:
        raise HTTPException(status_code=429, detail="Generation already in progress")

    # Track request time for auto-unload
    last_request_time = time.time()

    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)
    ensure_models_loaded(gen)

    is_generating = True
    try:
        # Just treat the "modification" as a new prompt
        gen_config = GenerationConfig(
            steps=request.steps,
            guidance_scale=request.guidance_scale
        )

        # Start time-based progress estimation (callback_on_step_end doesn't work with CPU offloading)
        start_time = time.time()
        progress_task = asyncio.create_task(
            _estimate_progress(manager, gen_config.steps, start_time, session_id)
        )

        try:
            # Generate in thread pool so async progress updates can run
            import concurrent.futures
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    gen.generate_new,
                    request.modification,  # Just use modification as the prompt
                    gen_config
                )
        finally:
            # Cancel progress estimation
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # Create thumbnail
        thumb_path = None
        if config.enable_thumbnails:
            try:
                thumb_dir = Path(config.thumbnails_dir)
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = create_thumbnail(
                    result.image_path,
                    size=config.thumbnail_size,
                    output_path=thumb_dir / f"{result.image_path.stem}_thumb.jpg"
                )
            except Exception as e:
                print(f"Warning: Could not create thumbnail: {e}")

        # Broadcast completion
        await broadcast_progress(
            manager,
            step=request.steps,
            total_steps=request.steps,
            elapsed=result.entry.generation_time or 0,
            status="complete",
            image_url=f"/api/v1/images/{result.image_path.name}",
            session_id=session_id
        )

        image_name = result.image_path.name
        return GenerationResponse(
            id=result.id,
            image_url=f"/api/v1/images/{image_name}",
            thumbnail_url=f"/api/v1/thumbnails/{result.image_path.stem}_thumb.jpg" if thumb_path else None,
            metadata={
                "prompt": result.prompt,
                "seed": result.seed,
                "steps": request.steps,
                "guidance_scale": request.guidance_scale,
                "generation_time": result.entry.generation_time
            }
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like auth errors) as-is
        raise
    except Exception as e:
        error_detail = {
            "error": "Generation failed",
            "message": str(e),
            "type": type(e).__name__
        }
        await broadcast_progress(
            manager,
            step=0,
            total_steps=request.steps,
            elapsed=0,
            status="error",
            error=str(e),
            session_id=session_id
        )
        raise HTTPException(status_code=500, detail=error_detail)
    finally:
        is_generating = False
        gen.set_progress_callback(None)


@app.post("/api/v1/generate/upscale", response_model=GenerationResponse)
async def upscale_current(
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """
    Upscale the current image to high resolution.

    Uses img2img to regenerate at 1024x1024 with 28 steps for a high-quality final render.
    """
    global is_generating, last_request_time

    if is_generating:
        raise HTTPException(status_code=409, detail="Generation already in progress")

    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    last_request_time = time.time()
    is_generating = True

    try:
        gen = get_generator(session_id)
        ensure_models_loaded(gen)

        current = gen.get_current()
        if not current:
            raise HTTPException(status_code=400, detail="No image to upscale")

        print(f"🔼 Upscaling: {current.prompt[:50]}... (seed={current.seed})")

        # High-quality upscale settings
        upscale_config = GenerationConfig(
            steps=28,
            guidance_scale=3.5,
            strength=0.35,  # Low strength for consistency
            width=1024,
            height=1024,
            seed=current.seed
        )

        start_time = time.time()
        progress_task = asyncio.create_task(
            _estimate_progress(manager, upscale_config.steps, start_time, session_id)
        )

        try:
            import concurrent.futures
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                # Empty modification = just use original prompt
                result = await loop.run_in_executor(
                    pool,
                    lambda: gen.refine("", upscale_config)
                )
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        thumb_path = None
        if config.enable_thumbnails:
            try:
                thumb_dir = Path(config.thumbnails_dir)
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = create_thumbnail(
                    result.image_path,
                    size=config.thumbnail_size,
                    output_path=thumb_dir / f"{result.image_path.stem}_thumb.jpg"
                )
            except Exception as e:
                print(f"Warning: Could not create thumbnail: {e}")

        await broadcast_progress(
            manager,
            step=upscale_config.steps,
            total_steps=upscale_config.steps,
            elapsed=result.entry.generation_time or 0,
            status="complete",
            image_url=f"/api/v1/images/{result.image_path.name}"
        )

        image_name = result.image_path.name
        return GenerationResponse(
            id=result.id,
            image_url=f"/api/v1/images/{image_name}",
            thumbnail_url=f"/api/v1/thumbnails/{result.image_path.stem}_thumb.jpg" if thumb_path else None,
            metadata={
                "prompt": result.prompt,
                "upscaled": True,
                "seed": result.seed,
                "steps": upscale_config.steps,
                "generation_time": result.entry.generation_time
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        error_detail = {"error": "Upscale failed", "message": str(e)}
        await broadcast_progress(
            manager, step=0, total_steps=28, elapsed=0,
            status="error", error=str(e)
        )
        raise HTTPException(status_code=500, detail=error_detail)
    finally:
        is_generating = False


@app.post("/api/v1/generate/cancel")
async def cancel_generation():
    """Cancel ongoing generation."""
    global is_generating
    # Note: Actual cancellation would require pipeline support
    if not is_generating:
        raise HTTPException(status_code=404, detail="No active generation")

    return {"success": True, "message": "Cancellation requested"}


@app.get("/api/v1/session/current", response_model=SessionResponse)
async def get_current_session(
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """Get current session state."""
    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)
    session = gen.session
    current = gen.get_current()

    current_image = None
    if current:
        current_image = entry_to_dict(current, config)

    return SessionResponse(
        session_id=session.session_id,
        current_image=current_image,
        generation_count=session.generation_count,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@app.get("/api/v1/session/history", response_model=HistoryResponse)
async def get_history(
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: str = Query("all", regex="^(all|new|refinement)$")
):
    """Get generation history."""
    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)

    history = gen.get_history()

    # Filter by type
    if type != "all":
        history = [h for h in history if h.type == type]

    total = len(history)

    # Sort by timestamp descending (newest first)
    history = sorted(history, key=lambda x: x.timestamp, reverse=True)

    # Apply pagination
    history = history[offset:offset + limit]

    return HistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        generations=[entry_to_dict(h, config) for h in history]
    )


@app.post("/api/v1/session/clear")
async def clear_session(
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """Clear current session."""
    # Get or create session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)
    count = gen.session.generation_count
    gen.clear_session()
    return {"success": True, "message": "Session cleared", "images_deleted": count}


@app.get("/api/v1/images/{image_name}")
async def get_image(image_name: str):
    """Get an image by name."""
    # Images are stored in shared output directory
    image_path = Path(config.output_dir) / image_name

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )


@app.get("/api/v1/thumbnails/{thumb_name}")
async def get_thumbnail(thumb_name: str):
    """Get a thumbnail by name."""
    config = get_config()
    thumb_path = Path(config.thumbnails_dir) / thumb_name

    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(
        thumb_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )


@app.delete("/api/v1/images/{image_id}")
async def delete_image(
    image_id: str,
    response: FastAPIResponse,
    session_id: str = Cookie(None, alias="dimp_session")
):
    """Delete an image."""
    # Get session
    session_id = get_session_id(session_id)
    response.set_cookie(key="dimp_session", value=session_id, max_age=30*24*60*60, httponly=True, samesite="lax")

    gen = get_generator(session_id)

    # Check if it's the current image
    current = gen.get_current()
    if current and current.id == image_id:
        raise HTTPException(status_code=409, detail="Cannot delete current image")

    # Find and delete the image
    for entry in gen.get_history():
        if entry.id == image_id:
            image_path = Path(entry.image_path)
            if image_path.exists():
                image_path.unlink()
            return {"success": True, "message": "Image deleted"}

    raise HTTPException(status_code=404, detail="Image not found")


# WebSocket endpoint
@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    # Extract session_id from cookies
    session_id = websocket.cookies.get("dimp_session")
    if not session_id:
        # Generate new session if none exists
        session_id = get_session_id(None)

    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()

            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                # Client subscribing to updates
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": data.get("channel", "generation_progress")
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Mount static files for frontend
# Note: This must be done after all API routes are defined
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
