# Dimpressionist - Project Specification

## Project Overview

A self-hosted image generation system that allows iterative, conversational refinement of AI-generated images. Think ChatGPT's DALL-E integration, but running locally with FLUX.1-dev, featuring both CLI and web interfaces.

**Key Advantage:** Self-hosted means no content guardrails - you have complete creative freedom within legal bounds. FLUX.1-dev has no built-in content filters or prompt restrictions.

### Core Value Proposition
- **No restrictions**: Generate whatever you want (within legal bounds)
- **Iterative workflow**: Refine images conversationally ("make the ball red")
- **Complete control**: Seeds, parameters, local privacy
- **No subscriptions**: Run as much as you want on your own hardware
- **Session persistence**: Resume work anytime

---

## Technical Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
│  ┌──────────────────┐        ┌──────────────────────┐      │
│  │   CLI Interface  │        │   Web Interface      │      │
│  │   (Readline)     │        │   (React/HTML)       │      │
│  └────────┬─────────┘        └──────────┬───────────┘      │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Engine Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Generation Manager                            │  │
│  │  - Session state management                           │  │
│  │  - History tracking                                   │  │
│  │  - Prompt interpretation & modification               │  │
│  │  - File management                                    │  │
│  └────────────────────┬──────────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  ML Model Layer                              │
│  ┌─────────────────┐          ┌─────────────────────┐      │
│  │ FLUX.1-dev      │          │ FLUX.1-dev          │      │
│  │ Text-to-Image   │          │ Image-to-Image      │      │
│  │ Pipeline        │          │ Pipeline            │      │
│  └─────────────────┘          └─────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend/Core:**
- Python 3.10+ (core logic)
- PyTorch 2.0+ (ML framework)
- Hugging Face Diffusers (model pipelines)
- FLUX.1-dev (image generation model)
- PIL/Pillow (image processing)

**Web Interface:**
- FastAPI or Flask (API server)
- WebSockets (real-time updates)
- React (frontend framework) OR plain HTML/CSS/JS
- Server-Sent Events (generation progress)

**CLI Interface:**
- Python argparse or Click
- Rich library (for pretty CLI output)
- Prompt toolkit (for advanced readline)

---

## System Components Detail

### 1. Generation Manager (Core)

**Responsibilities:**
- Manage current session state
- Track generation history
- Coordinate between txt2img and img2img pipelines
- Handle prompt modifications
- File I/O for images and metadata

**Key Classes:**

```
ConversationalImageGen
├── session_state
│   ├── current_image: Path
│   ├── current_prompt: str
│   ├── current_seed: int
│   └── generation_count: int
├── history: List[GenerationEntry]
├── txt2img_pipeline: FluxPipeline
├── img2img_pipeline: FluxImg2ImgPipeline
└── methods
    ├── generate_new(prompt, steps, seed)
    ├── refine_current(modification, strength, steps)
    ├── interpret_modification(modification) -> new_prompt
    ├── save_session()
    ├── load_session()
    └── export_history()
```

### 2. Prompt Interpreter

**Challenge:** Converting natural language modifications into effective prompts.

**Current Approach (v1 - Simple):**
- Keyword matching for colors, objects, styles
- Pattern detection: "make X Y", "add X", "remove X", "change to X"
- Append or modify existing prompt

**Future Enhancement (v2 - LLM-powered):**
- Use local LLM (Ollama/llama.cpp) to intelligently interpret modifications
- Context-aware prompt building
- Better semantic understanding
- Could use Claude API via artifacts for this

**Implementation Strategy:**
```python
class PromptInterpreter:
    def interpret(self, current_prompt: str, modification: str) -> str:
        """
        v1: Rule-based keyword matching
        v2: LLM-based interpretation
        """
        pass
```

### 3. Web API Server

**Endpoints:**

```
POST   /api/generate/new
       Body: {prompt, steps?, seed?}
       Returns: {image_id, image_url, metadata}

POST   /api/generate/refine
       Body: {modification, strength?, steps?}
       Returns: {image_id, image_url, metadata}

GET    /api/session/current
       Returns: {current_image, prompt, seed, history}

GET    /api/session/history
       Returns: {generations: [...]}

POST   /api/session/clear
       Returns: {success: bool}

GET    /api/images/{image_id}
       Returns: image file

WS     /api/ws/progress
       Streams: {step, total_steps, preview?}
```

**Features:**
- Authentication (optional, for multi-user)
- Rate limiting (prevent abuse)
- Progress streaming during generation
- Image caching
- Session management (cookies/JWT)

### 4. Web Frontend

**Core Views:**

1. **Main Canvas View**
   - Large image display
   - Generation history sidebar (thumbnails)
   - Prompt input box
   - Quick actions (new, refine, parameters)

2. **Settings Panel**
   - Model parameters (steps, guidance scale)
   - Default refinement strength
   - Output directory
   - Seed control

3. **History View**
   - Timeline of all generations
   - Click to restore/view
   - Export options

**UI/UX Considerations:**
- Real-time generation progress
- Preview thumbnails during generation
- Keyboard shortcuts (Enter to generate)
- Drag-and-drop for initial images (future)
- Gallery view with filtering

**Design Aesthetic (per frontend-design skill):**
- Avoid generic AI aesthetics
- Bold, distinctive visual direction
- Creative typography choices
- Atmospheric backgrounds
- Smooth animations and transitions
- Consider: Dark theme with high-contrast accents OR minimal, editorial style

---

## Data Models

### Generation Entry
```python
@dataclass
class GenerationEntry:
    id: str  # UUID
    timestamp: datetime
    type: Literal["new", "refinement"]
    prompt: str
    modification: Optional[str]  # For refinements
    seed: int
    steps: int
    strength: Optional[float]  # For refinements
    guidance_scale: float
    image_path: Path
    parent_id: Optional[str]  # For tracking refinement chains
```

### Session State
```python
@dataclass
class SessionState:
    session_id: str
    created_at: datetime
    updated_at: datetime
    current_generation: Optional[str]  # UUID of current image
    generations: List[GenerationEntry]
    
    def to_json(self) -> dict: ...
    @classmethod
    def from_json(cls, data: dict) -> "SessionState": ...
```

---

## File Structure

```
conversational-image-gen/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
│
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── generator.py          # Main generation manager
│   │   ├── pipelines.py          # FLUX pipeline wrappers
│   │   ├── prompt_interpreter.py # Modification logic
│   │   └── session.py            # Session management
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py               # CLI interface
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── api.py                # FastAPI server
│   │   ├── websocket.py          # Progress streaming
│   │   └── static/
│   │       ├── index.html
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           ├── app.js
│   │           └── api-client.js
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py        # Image operations
│       └── config.py             # Configuration management
│
├── outputs/                      # Generated images
│   └── .gitkeep
│
├── tests/
│   ├── test_generator.py
│   ├── test_prompt_interpreter.py
│   └── test_api.py
│
└── docs/
    ├── ARCHITECTURE.md           # This file
    ├── API.md                    # API documentation
    ├── CLI_USAGE.md              # CLI guide
    ├── WEB_UI_DESIGN.md          # UI/UX specifications
    └── DEPLOYMENT.md             # Deployment guide
```

---

## Hardware Requirements

### Minimum (for FLUX.1-schnell):
- GPU: 8GB VRAM (RTX 3060 Ti, 4060)
- RAM: 16GB
- Storage: 15GB (model + outputs)
- Generation time: ~3-5 seconds

### Recommended (for FLUX.1-dev):
- GPU: 12GB+ VRAM (RTX 3080, 4070 Ti)
- RAM: 32GB
- Storage: 30GB
- Generation time: ~10-20 seconds

### Optimal (current hardware - RTX 3090):
- GPU: 24GB VRAM
- RAM: 64GB
- Storage: 50GB+
- Generation time: ~15-30 seconds (high quality)
- Can run multiple models simultaneously

---

## Performance Optimizations

### Model Loading
- Keep models in VRAM between generations
- Use `torch.compile()` for faster inference (PyTorch 2.0+)
- Consider model quantization for lower VRAM usage

### Image Generation
- Batch processing for multiple images
- Progressive preview generation (low-res → high-res)
- Caching common model components

### Web Interface
- Lazy load history images
- Thumbnail generation for previews
- Server-side image compression
- CDN for static assets (if deploying publicly)

---

## Security Considerations

### Local-only Deployment
- No authentication needed
- Bind to localhost only
- CORS restrictions

### Public Deployment
- User authentication (OAuth/JWT)
- Rate limiting per user
- Input sanitization
- Content filtering (if required)
- HTTPS required
- Session security
- API key for external access

---

## Development Phases

### Phase 1: Core Functionality ✓
- [x] Basic generation manager
- [x] CLI interface
- [x] Session persistence
- [x] Simple prompt interpretation

### Phase 2: Web Interface (Current)
- [ ] FastAPI backend
- [ ] WebSocket progress streaming
- [ ] React/HTML frontend
- [ ] Real-time updates
- [ ] History management

### Phase 3: Enhanced Features
- [ ] LLM-powered prompt interpretation
- [ ] Inpainting support (regional edits)
- [ ] ControlNet integration (pose, depth, etc.)
- [ ] Multiple model support (SDXL, SD3)
- [ ] Batch generation
- [ ] Style presets

### Phase 4: Advanced Features
- [ ] Multi-user support
- [ ] Gallery/collection management
- [ ] Export workflows
- [ ] API for external integration
- [ ] Mobile-responsive design
- [ ] Keyboard shortcuts
- [ ] Undo/redo history

---

## Testing Strategy

### Unit Tests
- Prompt interpretation logic
- Session state management
- File operations
- API endpoints

### Integration Tests
- End-to-end generation workflows
- CLI commands
- Web API flows
- WebSocket connections

### Performance Tests
- Generation speed benchmarks
- Memory usage monitoring
- Concurrent request handling

### User Testing
- CLI usability
- Web UI intuitiveness
- Generation quality satisfaction

---

## Deployment Options

### Local Development
```bash
# CLI
python src/cli/main.py

# Web server
python src/web/api.py
# Access at http://localhost:8000
```

### Systemd Service (Linux)
- Auto-start on boot
- Run as background service
- Logging to journal

### Docker Container
- Isolated environment
- Easy deployment
- GPU passthrough required

### Windows Service
- Background service
- Start with Windows
- System tray icon (optional)

---

## Future Enhancements

### Short-term
- Multiple output resolutions
- Parameter presets (photorealistic, artistic, etc.)
- Export to common formats (PNG, JPG, WebP)
- Generation queue for batch processing

### Medium-term
- LoRA support (fine-tuned models)
- Custom model training interface
- Video generation (AnimateDiff)
- Upscaling integration (RealESRGAN)

### Long-term
- Plugin system for extensions
- Community model sharing
- Collaborative sessions
- Mobile app (iOS/Android)
- Voice control integration

---

## Success Metrics

### Technical
- Generation time < 30s on RTX 3090
- API response time < 100ms (excluding generation)
- Memory usage stable over long sessions
- 99% uptime for web interface

### User Experience
- Intuitive refinement workflow
- Clear progress indication
- Reliable session persistence
- Satisfying generation quality

### Code Quality
- 80%+ test coverage
- Clear documentation
- Modular, maintainable architecture
- Type hints throughout

---

## Known Limitations & Considerations

### Current Limitations
1. **Prompt interpretation**: Rule-based system is limited
2. **No regional editing**: Can't target specific image areas yet
3. **Single user**: No multi-user support initially
4. **Limited model variety**: Only FLUX.1 initially

### Technical Constraints
1. **VRAM requirement**: Need significant GPU memory
2. **Model size**: 24GB disk space per model
3. **Generation speed**: Still slower than cloud services
4. **No streaming output**: Can't see intermediate steps

### Considerations
1. **Model licensing**: FLUX.1-dev is non-commercial
2. **Content responsibility**: User generates content locally
3. **Storage management**: Images accumulate quickly
4. **Update frequency**: Model updates require manual download

---

## References & Resources

### Documentation
- FLUX documentation: https://blackforestlabs.ai/
- Diffusers library: https://huggingface.co/docs/diffusers
- PyTorch: https://pytorch.org/docs/

### Inspiration
- Midjourney's /imagine refinement
- ChatGPT's DALL-E editor
- ComfyUI's node system
- InvokeAI's unified canvas

### Community
- Civitai (model sharing)
- r/StableDiffusion
- Hugging Face forums

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Author:** Project specification for Claude Code implementation
