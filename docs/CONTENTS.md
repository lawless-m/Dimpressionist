# Dimpressionist - Planning Documents

## 📋 Document Overview

This package contains comprehensive planning and specification documents for building **Dimpressionist**, a self-hosted conversational image generation system. The system allows iterative refinement of AI-generated images through natural language, similar to ChatGPT's DALL-E integration but running locally with FLUX.1-dev.

**Key Advantage:** Self-hosted with FLUX.1-dev means no content guardrails or restrictions - complete creative freedom.

---

## 🎯 What You're Building

A complete image generation system with:
- **CLI interface** - Command-line tool for quick generation
- **Web interface** - Modern, beautiful web UI with real-time updates
- **Conversational refinement** - Modify images by saying "make the ball red"
- **Session persistence** - Resume work anytime
- **No restrictions** - Generate whatever you want locally

**Target Hardware:** RTX 3090 (24GB VRAM) - perfect specs!

---

## 📁 Files in This Package

### 1. **conversational_image_gen.py** 
**Status:** Working prototype  
**Purpose:** Basic CLI implementation to validate the concept  
**Use:** Test this first to understand the workflow  
**Note:** This is a proof of concept; Claude Code will build the production version

### 2. **PROJECT_SPECIFICATION.md** ⭐ START HERE
**What it covers:**
- Complete system architecture
- Component breakdown (Core, CLI, Web API, Frontend)
- Data models and file structure
- Technology stack decisions
- Hardware requirements and optimizations
- Development phases roadmap
- Testing strategy
- Known limitations

**Who reads this:** Everyone - this is the master blueprint

### 3. **WEB_UI_DESIGN.md** ⭐ CRITICAL FOR FRONTEND
**What it covers:**
- Complete UI/UX specifications
- Three aesthetic direction options (Studio Dark, Editorial Minimal, Retro Terminal)
- Layout structure with ASCII diagrams
- Component specifications (Header, Sidebar, Canvas, Input Panel)
- User flows and interactions
- Color systems, typography, spacing
- Micro-interactions and animations
- Responsive design breakpoints
- Accessibility requirements

**Who reads this:** Anyone implementing the frontend  
**Note:** Must be used with the `frontend-design` skill available in `/mnt/skills/public/frontend-design/`

### 4. **API_SPECIFICATION.md** ⭐ CRITICAL FOR BACKEND
**What it covers:**
- Complete REST API documentation
- All endpoints with request/response examples
- WebSocket interface for real-time progress
- Error handling and codes
- Rate limiting
- Authentication (future)
- Client examples (JS, Python, cURL)
- Performance expectations

**Who reads this:** Anyone implementing backend or API clients

### 5. **IMPLEMENTATION_GUIDE.md** ⭐ FOR CLAUDE CODE
**What it covers:**
- Step-by-step implementation plan
- Detailed task breakdown by phase
- Time estimates per component
- File generation order
- Testing checklists
- Common issues and solutions
- Success criteria
- Key technology decisions

**Who reads this:** Claude Code when implementing  
**Special notes:** 
- Prioritized phases (CRITICAL, HIGH, MEDIUM, LOW)
- Specific order to generate files
- Testing requirements for each phase

### 6. **README.md**
**What it covers:**
- Quick overview of the prototype
- Installation instructions
- Basic usage examples
- Feature highlights

**Who reads this:** Quick reference for the prototype

### 7. **requirements.txt**
**What it contains:**
- All Python dependencies
- Specific versions for stability

**Use:** `pip install -r requirements.txt`

---

## 🚀 How to Use These Documents

### For Initial Understanding:
1. Read **PROJECT_SPECIFICATION.md** first (30 mins)
   - Understand the overall system
   - Review architecture diagrams
   - Check hardware requirements
   
2. Try the **conversational_image_gen.py** prototype (30 mins)
   - Install dependencies: `pip install -r requirements.txt`
   - Run: `python conversational_image_gen.py`
   - Generate a few images to understand the workflow
   - Test refinement: "make the ball red"

### For Planning the Build:
3. Review **IMPLEMENTATION_GUIDE.md** (1 hour)
   - Understand development phases
   - Note time estimates
   - Review file generation order
   - Check success criteria

### For Claude Code Implementation:

#### Backend Development:
1. Read **PROJECT_SPECIFICATION.md** - Architecture section
2. Read **API_SPECIFICATION.md** - Complete API reference
3. Follow **IMPLEMENTATION_GUIDE.md** - Phases 1-3
4. Reference **conversational_image_gen.py** for core logic

#### Frontend Development:
1. **CRITICAL:** Read `/mnt/skills/public/frontend-design/SKILL.md` FIRST
2. Read **WEB_UI_DESIGN.md** - Complete UI specifications
3. Choose ONE aesthetic direction and commit to it
4. Follow **IMPLEMENTATION_GUIDE.md** - Phase 4
5. Reference **API_SPECIFICATION.md** for API integration

---

## 📊 Development Roadmap

### Week 1: Core Backend
- **Day 1-2:** Project setup + Core generation engine
- **Day 3:** Prompt interpreter
- **Day 4-5:** CLI interface + Testing
- **Deliverable:** Working CLI tool

### Week 2: Web API
- **Day 1-2:** FastAPI server + REST endpoints
- **Day 3:** WebSocket progress streaming
- **Day 4-5:** API testing + Documentation
- **Deliverable:** Functional API server

### Week 3: Web Frontend
- **Day 1:** Read frontend-design skill + Choose aesthetic
- **Day 2-3:** HTML/CSS structure + Styling
- **Day 4-5:** JavaScript application + API integration
- **Deliverable:** Working web interface

### Week 4: Polish & Features
- **Day 1-2:** Error handling + Performance optimization
- **Day 3:** Testing + Bug fixes
- **Day 4:** Documentation
- **Day 5:** LLM-powered interpretation (optional)
- **Deliverable:** Production-ready v1.0

**Total Time:** 30-40 hours of focused development

---

## 🎨 Key Design Decisions Made

### Backend:
- **Framework:** FastAPI (fast, modern, async)
- **Model:** FLUX.1-dev (best quality)
- **Storage:** JSON files initially (simple, no DB setup)
- **Prompt Interpretation:** Rule-based v1 → LLM-powered v2

### Frontend:
- **Approach:** Vanilla JS (no build step)
- **Aesthetic:** Studio Dark (or choose from 3 options)
- **Layout:** Canvas-focused with history sidebar
- **Updates:** Real-time via WebSocket

### Architecture:
- **Deployment:** Local-first (no cloud)
- **Multi-user:** Not initially (can add later)
- **Sessions:** Persistent to JSON
- **Images:** Stored in local filesystem

---

## 🎯 Success Metrics

### MVP (Minimum Viable Product):
- ✅ Generate images from prompts
- ✅ Refine conversationally
- ✅ Session persistence
- ✅ Basic web UI
- ✅ Real-time progress

### v1.0 Release:
- ✅ Polished, distinctive UI
- ✅ Complete API
- ✅ Comprehensive docs
- ✅ Tests passing
- ✅ No critical bugs

### Quality Targets:
- Generation time: < 30s (RTX 3090)
- API response: < 100ms
- UI interactions: < 100ms
- History scroll: 60fps
- Uptime: 99%+

---

## 🔧 Technical Requirements

### Development Environment:
- **OS:** Debian Linux (Windows 11 for development also works)
- **Python:** 3.10+
- **GPU:** NVIDIA RTX 3090 (24GB VRAM)
- **CUDA:** 12.1+
- **Storage:** ~50GB free

### Dependencies:
```bash
# Core
torch>=2.0.0
diffusers>=0.30.0
transformers>=4.40.0

# Backend
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0

# Utils
pillow>=10.0.0
rich>=13.0.0  # For CLI
```

---

## 🚨 Important Notes

### Before Starting:
1. **Read PROJECT_SPECIFICATION.md first** - It's the blueprint
2. **For frontend:** Read the frontend-design skill before writing any HTML/CSS
3. **For backend:** Review API_SPECIFICATION.md for endpoint contracts
4. **Test frequently:** Each component should work before moving on

### During Development:
1. **Follow the phases** in IMPLEMENTATION_GUIDE.md
2. **Don't skip testing** - Each phase has test requirements
3. **Commit regularly** - Track progress
4. **Ask questions** - Better to clarify than guess

### Anti-patterns to Avoid:
- ❌ Generic AI aesthetics (Inter font, purple gradients)
- ❌ Skipping the frontend-design skill
- ❌ Building everything before testing anything
- ❌ Hardcoding paths and values
- ❌ Ignoring error handling

---

## 📚 Additional Resources

### For Learning:
- FLUX documentation: https://blackforestlabs.ai/
- Diffusers docs: https://huggingface.co/docs/diffusers
- FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/
- Frontend design principles: See frontend-design skill

### For Troubleshooting:
- Check IMPLEMENTATION_GUIDE.md "Common Issues" section
- Review API_SPECIFICATION.md for error codes
- Test with prototype CLI first
- Use Rich library for debugging output

---

## 🎉 What Makes This Special

### Unique Features:
1. **Conversational refinement** - Not just generate and done
2. **Session continuity** - Resume anytime, track full history
3. **Distinctive design** - Following frontend-design best practices
4. **Local & private** - Your images, your machine, your control
5. **No restrictions** - Generate what you want within legal bounds

### Compared to Alternatives:
- **vs Midjourney:** No Discord, no content restrictions, unlimited generations
- **vs ComfyUI:** Simpler interface, conversational workflow
- **vs Automatic1111:** More focused UX, built-in refinement
- **vs DALL-E:** Local, private, no censorship, no costs after setup

---

## 📝 Notes for Claude Code

### Critical First Steps:
1. Create project structure from PROJECT_SPECIFICATION.md
2. Install dependencies from requirements.txt
3. Test FLUX.1-dev loads on RTX 3090
4. Implement core generation engine (Phase 1.2)
5. Build CLI to validate (Phase 2)

### When Building Frontend:
1. **READ `/mnt/skills/public/frontend-design/SKILL.md` FIRST**
2. Choose ONE aesthetic from WEB_UI_DESIGN.md
3. Commit to it fully - bold choices
4. Avoid generic patterns
5. Test on actual browser constantly

### Testing Strategy:
- Unit test each component as you build it
- Integration test full workflows
- Manual test web UI extensively
- Performance test on RTX 3090

---

## ✅ Ready to Build?

### Checklist Before Starting:
- [ ] Read PROJECT_SPECIFICATION.md
- [ ] Tried the prototype CLI
- [ ] Reviewed IMPLEMENTATION_GUIDE.md
- [ ] Understand the architecture
- [ ] Know which phase to start with
- [ ] Have hardware requirements met
- [ ] Dependencies list reviewed

### First Commands:
```bash
# Setup
mkdir conversational-image-gen
cd conversational-image-gen
python -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Test model loads
python -c "from diffusers import FluxPipeline; print('OK')"
```

**Now hand this over to Claude Code and let's build something amazing!** 🚀

---

**Package Version:** 1.0  
**Created:** December 2025  
**Target Hardware:** RTX 3090 (24GB VRAM)  
**Estimated Build Time:** 30-40 hours  
**Difficulty:** Intermediate  
**Result:** Production-ready conversational image generator
