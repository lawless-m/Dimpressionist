"""
FastAPI server for Dimpressionist.

Provides REST API and WebSocket interface for image generation.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import ConversationalImageGenerator, GenerationConfig, GenerationEntry
from src.utils import get_config, create_thumbnail
from src.web.websocket import ConnectionManager, broadcast_progress


# Pydantic models for API
class GenerateNewRequest(BaseModel):
    """Request model for new image generation."""
    prompt: str = Field(..., min_length=1, max_length=500)
    steps: int = Field(28, ge=10, le=100)
    guidance_scale: float = Field(3.5, ge=1.0, le=5.0)
    seed: Optional[int] = None
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(1024, ge=256, le=2048)


class RefineRequest(BaseModel):
    """Request model for image refinement."""
    modification: str = Field(..., min_length=1, max_length=500)
    strength: float = Field(0.6, ge=0.1, le=1.0)
    steps: int = Field(28, ge=10, le=100)
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
generator: Optional[ConversationalImageGenerator] = None
manager = ConnectionManager()
is_generating = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global generator
    config = get_config()

    print("Starting Dimpressionist API server...")
    print(f"Output directory: {config.output_dir}")

    # Initialize generator (models loaded lazily or on demand)
    generator = ConversationalImageGenerator(
        output_dir=config.output_dir,
        load_models=False  # Load on first request
    )

    yield

    # Cleanup
    print("Shutting down...")


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


# Helper functions
def ensure_generator():
    """Ensure generator is available."""
    if generator is None:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    return generator


def ensure_models_loaded():
    """Ensure models are loaded."""
    gen = ensure_generator()
    if not gen._models_loaded:
        gen.load_models()
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
    gen = ensure_generator()
    return StatusResponse(
        status="operational",
        model_loaded=gen._models_loaded,
        version="1.0.0"
    )


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
async def generate_new(request: GenerateNewRequest):
    """Generate a new image from text prompt."""
    global is_generating

    if is_generating:
        raise HTTPException(status_code=429, detail="Generation already in progress")

    gen = ensure_models_loaded()
    config = get_config()

    is_generating = True
    try:
        gen_config = GenerationConfig(
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            width=request.width,
            height=request.height
        )

        # Set up progress callback for WebSocket
        def progress_callback(step: int, total: int, elapsed: float):
            asyncio.create_task(broadcast_progress(
                manager,
                step=step,
                total_steps=total,
                elapsed=elapsed,
                status="generating"
            ))

        gen.set_progress_callback(progress_callback)

        # Generate
        result = gen.generate_new(request.prompt, gen_config)

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
            image_url=f"/api/v1/images/{result.image_path.name}"
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
    except Exception as e:
        await broadcast_progress(
            manager,
            step=0,
            total_steps=request.steps,
            elapsed=0,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        is_generating = False
        gen.set_progress_callback(None)


@app.post("/api/v1/generate/refine", response_model=GenerationResponse)
async def refine_image(request: RefineRequest):
    """Refine current image with modification."""
    global is_generating

    if is_generating:
        raise HTTPException(status_code=429, detail="Generation already in progress")

    gen = ensure_models_loaded()
    config = get_config()

    current = gen.get_current()
    if not current:
        raise HTTPException(status_code=400, detail="No current image to refine")

    is_generating = True
    try:
        gen_config = GenerationConfig(
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            strength=request.strength,
            width=current.width,
            height=current.height
        )

        # Set up progress callback
        def progress_callback(step: int, total: int, elapsed: float):
            asyncio.create_task(broadcast_progress(
                manager,
                step=step,
                total_steps=total,
                elapsed=elapsed,
                status="generating"
            ))

        gen.set_progress_callback(progress_callback)

        # Refine
        result = gen.refine(request.modification, gen_config)

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
            image_url=f"/api/v1/images/{result.image_path.name}"
        )

        image_name = result.image_path.name
        return GenerationResponse(
            id=result.id,
            image_url=f"/api/v1/images/{image_name}",
            thumbnail_url=f"/api/v1/thumbnails/{result.image_path.stem}_thumb.jpg" if thumb_path else None,
            metadata={
                "prompt": result.prompt,
                "modification": request.modification,
                "parent_id": current.id,
                "seed": result.seed,
                "steps": request.steps,
                "guidance_scale": request.guidance_scale,
                "strength": request.strength,
                "generation_time": result.entry.generation_time
            }
        )
    except Exception as e:
        await broadcast_progress(
            manager,
            step=0,
            total_steps=request.steps,
            elapsed=0,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        is_generating = False
        gen.set_progress_callback(None)


@app.post("/api/v1/generate/cancel")
async def cancel_generation():
    """Cancel ongoing generation."""
    global is_generating
    # Note: Actual cancellation would require pipeline support
    if not is_generating:
        raise HTTPException(status_code=404, detail="No active generation")

    return {"success": True, "message": "Cancellation requested"}


@app.get("/api/v1/session/current", response_model=SessionResponse)
async def get_current_session():
    """Get current session state."""
    gen = ensure_generator()
    session = gen.session
    current = gen.get_current()
    config = get_config()

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
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: str = Query("all", regex="^(all|new|refinement)$")
):
    """Get generation history."""
    gen = ensure_generator()
    config = get_config()

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
async def clear_session():
    """Clear current session."""
    gen = ensure_generator()
    count = gen.session.generation_count
    gen.clear_session()
    return {"success": True, "message": "Session cleared", "images_deleted": count}


@app.get("/api/v1/images/{image_name}")
async def get_image(image_name: str):
    """Get an image by name."""
    gen = ensure_generator()
    image_path = Path(gen.output_dir) / image_name

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
async def delete_image(image_id: str):
    """Delete an image."""
    gen = ensure_generator()

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
    await manager.connect(websocket)
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
@app.on_event("startup")
async def mount_static():
    """Mount static files directory."""
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
