# Implementation Guide for Claude Code

This document provides a structured implementation plan for building the Conversational Image Generator.

---

## Phase 1: Core Backend (Priority: CRITICAL)

### 1.1 Project Setup
**Estimated Time:** 30 minutes

**Tasks:**
- [ ] Create project structure (see PROJECT_SPECIFICATION.md)
- [ ] Set up virtual environment
- [ ] Create requirements.txt with all dependencies
- [ ] Initialize git repository
- [ ] Create .gitignore (exclude outputs/, venv/, __pycache__)

**Deliverables:**
- Clean project structure
- requirements.txt
- README.md with setup instructions

---

### 1.2 Core Generation Engine
**Estimated Time:** 2-3 hours

**File:** `src/core/generator.py`

**Implementation Order:**
1. Create `GenerationEntry` dataclass
2. Create `SessionState` dataclass with JSON serialization
3. Implement `ConversationalImageGen` class:
   - `__init__`: Load pipelines (txt2img + img2img)
   - `load_session()`: Read from session.json
   - `save_session()`: Write to session.json
   - `generate_from_scratch()`: Use txt2img pipeline
   - `refine_image()`: Use img2img pipeline
   - `get_current_state()`: Return session info

**Key Points:**
- Use `torch.bfloat16` for FLUX.1-dev
- Always use same seed for refinements
- Save images with descriptive timestamps
- Track parent-child relationships in refinements

**Testing:**
```python
# Basic test
gen = ConversationalImageGen()
gen.generate_from_scratch("a cat", steps=10)  # Quick test
gen.refine_image("make it blue", strength=0.6, steps=10)
assert gen.current_image is not None
```

---

### 1.3 Prompt Interpreter
**Estimated Time:** 1-2 hours

**File:** `src/core/prompt_interpreter.py`

**Implementation:**
```python
class PromptInterpreter:
    def interpret(self, current_prompt: str, modification: str) -> str:
        """
        v1: Rule-based interpretation
        Returns modified prompt based on modification text
        """
        pass
```

**Rules to Implement:**
1. Color replacements: "make X red" → replace existing color
2. Additions: "add X" → append to prompt
3. Style changes: "change to Y style" → append style
4. Object replacements: "make the X a Y" → replace object
5. Removals: "remove X" → note in prompt (tricky without inpainting)
6. Background changes: "change background to X" → append
7. Default: Append modification to prompt

**Testing:**
- Test each rule type
- Test edge cases (empty prompt, multiple colors)
- Verify output prompt quality

---

### 1.4 Image Utilities
**Estimated Time:** 1 hour

**File:** `src/utils/image_utils.py`

**Functions to Implement:**
- `create_thumbnail(image_path, size=120) -> Path`
- `validate_image_dimensions(width, height) -> bool`
- `optimize_image_for_web(image_path) -> Path`
- `batch_resize(images, target_size) -> List[Image]`

---

## Phase 2: CLI Interface (Priority: HIGH)

### 2.1 Basic CLI
**Estimated Time:** 2 hours

**File:** `src/cli/main.py`

**Features:**
- Interactive REPL loop
- Commands: new, refine, history, current, clear, help, exit
- Progress indicators (use `rich` library)
- Error handling with helpful messages
- Colored output for better UX

**Implementation:**
```python
from rich.console import Console
from rich.progress import Progress

console = Console()

def main():
    gen = ConversationalImageGen()
    console.print("[bold green]🎨 Conversational Image Generator[/bold green]")
    
    while True:
        user_input = console.input("[cyan]🎨 > [/cyan]")
        # Parse and execute commands
```

**Testing:**
- Test all commands work
- Test parameter parsing (--steps, --seed)
- Test error messages are clear
- Test history display formats correctly

---

## Phase 3: Web API (Priority: HIGH)

### 3.1 FastAPI Server
**Estimated Time:** 3-4 hours

**File:** `src/web/api.py`

**Implementation Order:**
1. Basic FastAPI app setup
2. CORS middleware
3. Static file serving (for images)
4. Implement all REST endpoints (see API_SPECIFICATION.md)
5. Error handling middleware
6. Request validation with Pydantic models

**Key Endpoints to Implement First:**
1. `POST /api/v1/generate/new` (CRITICAL)
2. `POST /api/v1/generate/refine` (CRITICAL)
3. `GET /api/v1/session/current` (HIGH)
4. `GET /api/v1/session/history` (HIGH)
5. `GET /api/v1/images/{image_id}` (CRITICAL)

**Pydantic Models:**
```python
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    steps: int = Field(28, ge=10, le=100)
    guidance_scale: float = Field(3.5, ge=1.0, le=5.0)
    seed: Optional[int] = None

class RefineRequest(BaseModel):
    modification: str = Field(..., min_length=1, max_length=500)
    strength: float = Field(0.6, ge=0.1, le=1.0)
    steps: int = Field(28, ge=10, le=100)
```

**Testing:**
- Use `pytest` with `httpx.AsyncClient`
- Test all endpoints
- Test error responses
- Test parameter validation

---

### 3.2 WebSocket Progress
**Estimated Time:** 2 hours

**File:** `src/web/websocket.py`

**Implementation:**
```python
from fastapi import WebSocket

class GenerationProgressManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast_progress(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
```

**Integration with Generator:**
- Add progress callback to pipeline
- Emit WebSocket messages on each step
- Calculate ETA based on average step time

**Testing:**
- Test WebSocket connection
- Test message broadcasting
- Test reconnection handling

---

## Phase 4: Web Frontend (Priority: HIGH)

### 4.1 HTML/CSS Structure
**Estimated Time:** 3-4 hours

**File:** `src/web/static/index.html`

**IMPORTANT:** Read frontend-design skill FIRST!

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Conversational Image Generator</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Header -->
    <header></header>
    
    <!-- Main Layout -->
    <div class="container">
        <!-- History Sidebar -->
        <aside id="history-sidebar"></aside>
        
        <!-- Canvas -->
        <main id="canvas"></main>
    </div>
    
    <!-- Prompt Input -->
    <footer id="prompt-panel"></footer>
    
    <script src="js/app.js"></script>
</body>
</html>
```

**Follow WEB_UI_DESIGN.md for:**
- Choose one aesthetic direction (Studio Dark recommended)
- Implement color system with CSS variables
- Typography scale and font choices
- Spacing and layout grid
- Animation timings

---

### 4.2 CSS Styling
**Estimated Time:** 4-5 hours

**File:** `src/web/static/css/style.css`

**Key Sections:**
1. CSS Reset/Normalize
2. CSS Variables (colors, fonts, spacing)
3. Layout (grid/flexbox)
4. Component styles (buttons, inputs, cards)
5. Animations and transitions
6. Responsive breakpoints

**CRITICAL Requirements from frontend-design skill:**
- Avoid generic fonts (no Inter, Roboto, Arial)
- Choose distinctive typography
- Bold aesthetic direction
- Micro-interactions on hover/click
- Smooth animations (use CSS animations)

---

### 4.3 JavaScript Application
**Estimated Time:** 5-6 hours

**File:** `src/web/static/js/app.js`

**Architecture:**
```javascript
// State management
const state = {
    session: null,
    currentImage: null,
    history: [],
    isGenerating: false
};

// API client
class APIClient {
    async generateNew(prompt, params) { }
    async refineImage(modification, params) { }
    async getHistory() { }
    async getCurrentSession() { }
}

// WebSocket handler
class WSHandler {
    connect() { }
    onProgress(callback) { }
    onComplete(callback) { }
}

// UI updates
function updateCanvas(imageData) { }
function updateHistory(images) { }
function showProgress(percentage) { }
```

**Implementation Order:**
1. API client class
2. WebSocket handler
3. DOM manipulation functions
4. Event listeners (buttons, inputs)
5. State management
6. Progress updates
7. Error handling

**Testing:**
- Manual browser testing
- Test all user flows
- Test error states
- Test WebSocket reconnection

---

## Phase 5: Polish & Testing (Priority: MEDIUM)

### 5.1 Error Handling
**Estimated Time:** 2 hours

**Tasks:**
- Graceful degradation in web UI
- Clear error messages everywhere
- Retry logic for failed generations
- User-friendly validation messages

---

### 5.2 Performance Optimization
**Estimated Time:** 2-3 hours

**Backend:**
- Profile generation pipeline
- Optimize image loading
- Add response caching where appropriate
- Implement connection pooling

**Frontend:**
- Lazy load images
- Optimize thumbnail sizes
- Debounce input events
- Virtual scrolling for long history

---

### 5.3 Documentation
**Estimated Time:** 2 hours

**Files to Create/Update:**
- README.md with installation & usage
- API.md with endpoint documentation
- DEPLOYMENT.md with setup instructions
- CODE_STYLE.md with conventions
- CHANGELOG.md

---

## Phase 6: Advanced Features (Priority: LOW)

### 6.1 LLM-Powered Prompt Interpretation
**Estimated Time:** 3-4 hours

**Options:**
1. Use Claude API (via artifacts - already available!)
2. Use local Ollama (llama3.2, qwen2.5)
3. Use local llama.cpp

**Implementation:**
```python
class LLMPromptInterpreter(PromptInterpreter):
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def interpret(self, current_prompt: str, modification: str) -> str:
        prompt_to_llm = f"""
        Current image prompt: "{current_prompt}"
        User wants to: "{modification}"
        
        Generate an updated prompt that incorporates this change.
        Return ONLY the new prompt, nothing else.
        """
        return self.llm.generate(prompt_to_llm)
```

---

### 6.2 Inpainting Support
**Estimated Time:** 4-6 hours

**Requirements:**
- Mask drawing UI
- FLUX inpainting pipeline
- API endpoints for masked generation

---

### 6.3 Settings Panel
**Estimated Time:** 2-3 hours

**Features:**
- Model selection (future multi-model support)
- Default parameters
- Output directory configuration
- Theme toggle
- Clear all data

---

## Testing Checklist

### Unit Tests
- [ ] Generation engine functions
- [ ] Prompt interpreter logic
- [ ] Session state serialization
- [ ] API endpoint responses
- [ ] Parameter validation

### Integration Tests
- [ ] Full generation workflow (CLI)
- [ ] Full generation workflow (API)
- [ ] WebSocket communication
- [ ] Session persistence across restarts

### UI Tests
- [ ] All buttons functional
- [ ] Keyboard shortcuts work
- [ ] Responsive on mobile
- [ ] Error states display correctly
- [ ] Progress updates smooth

### Performance Tests
- [ ] Generation completes in < 30s
- [ ] API responds in < 100ms
- [ ] No memory leaks over long sessions
- [ ] History scrolls at 60fps

---

## Deployment Checklist

### Development
- [ ] All dependencies in requirements.txt
- [ ] Environment variables documented
- [ ] Setup script works on fresh install
- [ ] README has clear instructions

### Production
- [ ] API runs as systemd service
- [ ] Logs configured properly
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Rate limiting enabled

---

## File Generation Order for Claude Code

**This is the recommended order to generate files:**

1. **Project structure** (mkdir commands)
2. **requirements.txt**
3. **src/core/generator.py** (Core engine)
4. **src/core/prompt_interpreter.py**
5. **src/utils/image_utils.py**
6. **src/cli/main.py** (Test CLI first)
7. **src/web/api.py** (FastAPI server)
8. **src/web/websocket.py**
9. **src/web/static/index.html**
10. **src/web/static/css/style.css** (After reading frontend-design skill!)
11. **src/web/static/js/app.js**
12. **README.md**
13. **setup.py** (for installation)
14. **tests/** (Unit tests)

---

## Key Decisions for Claude Code

### Backend Framework
**Recommendation:** FastAPI
- Fast, modern, async support
- Automatic API docs (OpenAPI)
- Great WebSocket support
- Type hints with Pydantic

**Alternative:** Flask
- Simpler, more mature
- More examples available
- No async (needs extensions)

### Frontend Approach
**Recommendation:** Vanilla JS + HTML/CSS
- No build step needed
- Simple deployment
- Fast iteration
- Full control over design

**Alternative:** React
- Better state management
- Component reusability
- Larger bundle size
- Requires build step

### Prompt Interpretation v1
**Recommendation:** Rule-based
- Simple, predictable
- No external dependencies
- Fast
- Upgrade to LLM later

### Database
**Recommendation:** JSON files (v1)
- Simple
- No setup required
- Easy to inspect
- Sufficient for local use

**Future:** SQLite
- Better for multi-user
- Query capabilities
- Relational data

---

## Common Issues & Solutions

### Issue: Out of Memory
**Solutions:**
- Reduce image size (1024→768)
- Lower steps (28→20)
- Use model CPU offloading
- Clear GPU cache between generations

### Issue: Slow Generation
**Solutions:**
- Use torch.compile()
- Enable xformers
- Reduce steps
- Use FLUX.1-schnell instead

### Issue: WebSocket Disconnects
**Solutions:**
- Implement reconnection logic
- Send periodic pings
- Increase timeout values
- Handle disconnect gracefully

### Issue: CORS Errors
**Solutions:**
- Configure CORS middleware
- Allow localhost origins
- Set proper headers
- Use same port for dev

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Generate images from prompts
- ✅ Refine images conversationally
- ✅ Session persistence
- ✅ Basic web UI
- ✅ Real-time progress

### v1.0 Release
- ✅ All core features working
- ✅ Polished UI (following frontend-design skill)
- ✅ Clear documentation
- ✅ Basic tests passing
- ✅ No critical bugs

### v1.1 Enhancements
- ✅ LLM-powered interpretation
- ✅ Settings panel
- ✅ Keyboard shortcuts
- ✅ Export functionality
- ✅ Mobile responsive

---

## Time Estimates

**Total Implementation Time:** 30-40 hours

**Breakdown:**
- Phase 1 (Core): 4-6 hours
- Phase 2 (CLI): 2 hours
- Phase 3 (API): 5-6 hours
- Phase 4 (Frontend): 12-15 hours
- Phase 5 (Polish): 4-5 hours
- Phase 6 (Advanced): 3-6 hours (optional)

**Realistic Timeline:**
- Week 1: Phases 1-2 (Core + CLI)
- Week 2: Phase 3 (API)
- Week 3: Phase 4 (Frontend)
- Week 4: Phase 5-6 (Polish + Advanced)

---

## Next Steps for Claude Code

1. **Read the frontend-design skill** (`/mnt/skills/public/frontend-design/SKILL.md`)
2. **Create project structure** following PROJECT_SPECIFICATION.md
3. **Start with Phase 1.1** (Project setup)
4. **Implement iteratively** following this guide
5. **Test frequently** after each component
6. **Commit regularly** to track progress

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**For:** Claude Code to implement the full system
