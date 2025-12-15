# Quick Reference Card

## 🎯 Project Summary
**Name:** Dimpressionist  
**Purpose:** Self-hosted image generation with conversational refinement  
**Model:** FLUX.1-dev (no content guardrails!)
**Hardware:** RTX 3090 (24GB VRAM)  
**Build Time:** 30-40 hours

**Key Advantage:** Self-hosted means no content restrictions - FLUX.1-dev has no built-in filters or prompt blocking. Generate what you want within legal bounds.

---

## 📁 Key Files Priority

1. **CONTENTS.md** ⭐ - Start here, navigation guide
2. **PROJECT_SPECIFICATION.md** ⭐ - Master blueprint
3. **IMPLEMENTATION_GUIDE.md** ⭐ - Step-by-step build plan
4. **WEB_UI_DESIGN.md** - Complete UI specs
5. **API_SPECIFICATION.md** - API documentation
6. **conversational_image_gen.py** - Working prototype

---

## 🚀 Quick Start for Claude Code

```bash
# 1. Extract and read
unzip conversational-image-gen-planning.zip
cat CONTENTS.md

# 2. Read in order
1. PROJECT_SPECIFICATION.md  (architecture)
2. IMPLEMENTATION_GUIDE.md   (build plan)
3. /mnt/skills/public/frontend-design/SKILL.md  (CRITICAL for UI)

# 3. Start building (follow IMPLEMENTATION_GUIDE.md phases)
Phase 1: Core Backend (4-6 hours)
Phase 2: CLI Interface (2 hours)
Phase 3: Web API (5-6 hours)
Phase 4: Web Frontend (12-15 hours) - Read frontend-design skill FIRST!
Phase 5: Polish (4-5 hours)
```

---

## 🎨 Design Requirements

**Frontend Must:**
- ✅ Read `/mnt/skills/public/frontend-design/SKILL.md` BEFORE coding
- ✅ Choose ONE aesthetic direction (Studio Dark recommended)
- ✅ Avoid: Inter, Roboto, Arial fonts
- ✅ Avoid: Generic purple gradients
- ✅ Include: Bold typography, smooth animations, distinctive style

**Backend Must:**
- ✅ FastAPI for API server
- ✅ WebSocket for progress updates
- ✅ Session persistence (JSON)
- ✅ Real-time progress streaming

---

## 📊 Implementation Order

**Week 1:**
- Day 1-2: Core generator + Session management
- Day 3: Prompt interpreter
- Day 4-5: CLI interface

**Week 2:**
- Day 1-2: FastAPI + REST endpoints
- Day 3: WebSocket progress
- Day 4-5: API testing

**Week 3:**
- Day 1: Read frontend-design skill + Choose aesthetic
- Day 2-3: HTML/CSS
- Day 4-5: JavaScript + Integration

**Week 4:**
- Day 1-2: Error handling + Polish
- Day 3-4: Testing
- Day 5: Optional features (LLM interpretation)

---

## ✅ Key Features

**Core:**
- [x] Text-to-image generation
- [x] Image-to-image refinement
- [x] Conversational modification ("make it red")
- [x] Session persistence
- [x] Generation history

**Interfaces:**
- [x] CLI (interactive REPL)
- [x] Web API (REST + WebSocket)
- [x] Web UI (modern, distinctive)

**Advanced:**
- [ ] LLM-powered prompt interpretation
- [ ] Inpainting (masked edits)
- [ ] Batch generation
- [ ] Multiple model support

---

## 🎯 Success Criteria

**MVP:**
✅ Generate images from text  
✅ Refine with natural language  
✅ Basic web interface  
✅ Session persistence  
✅ Real-time progress  

**v1.0:**
✅ Polished UI (following frontend-design)  
✅ Complete API  
✅ Comprehensive docs  
✅ No critical bugs  

---

## 🔧 Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- PyTorch + Diffusers
- FLUX.1-dev

**Frontend:**
- Vanilla JavaScript
- HTML5 + CSS3
- WebSocket API
- No build tools needed

**Storage:**
- JSON (session state)
- PNG (images)
- Filesystem (simple)

---

## 🚨 Critical Notes

**MUST DO:**
1. Read frontend-design skill before frontend work
2. Test FLUX loads on GPU first
3. Follow implementation phases in order
4. Commit after each component works

**DON'T:**
- Skip reading planning docs
- Use generic AI aesthetics
- Build everything before testing
- Hardcode values
- Ignore error handling

---

## 📞 When You Need Help

**Architecture questions?** → PROJECT_SPECIFICATION.md  
**API contract questions?** → API_SPECIFICATION.md  
**UI design questions?** → WEB_UI_DESIGN.md + frontend-design skill  
**Build order questions?** → IMPLEMENTATION_GUIDE.md  
**Quick overview?** → CONTENTS.md

---

## 💡 What Makes This Special

1. **Conversational refinement** - Unique workflow
2. **No restrictions** - Local generation
3. **Beautiful UI** - Following design principles
4. **Session continuity** - Never lose progress
5. **Real-time updates** - See generation progress

---

## ⚡ Performance Targets

- Generation: < 30s (RTX 3090)
- API response: < 100ms
- UI interaction: < 100ms
- History scroll: 60fps

---

**Ready to build? Start with CONTENTS.md!**
