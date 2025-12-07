# Web UI Design Specification

## Design Philosophy

Building a **distinctive, production-grade interface** that avoids generic AI aesthetics. The interface should feel like a professional creative tool, not a generic web app.

---

## Aesthetic Direction Options

Choose ONE of these directions and execute it with precision:

### Option A: "Studio Dark" (Recommended)
**Concept:** Professional creative studio environment - dark, focused, high-contrast

**Visual Language:**
- **Colors:** Deep charcoal/near-black background (#0a0a0a, #121212), crisp white text, single vibrant accent (electric blue, neon green, or warm amber)
- **Typography:** 
  - Display: "Space Mono" or "JetBrains Mono" (monospace for technical feel)
  - Body: "Inter" alternative like "Archivo" or "Manrope"
- **Layout:** Asymmetric, canvas-focused, floating panels
- **Details:** Subtle grain texture, glow effects on active elements, soft shadows
- **Motion:** Smooth fade-ins, subtle scale transforms, loading shimmer effects

### Option B: "Editorial Minimal"
**Concept:** Magazine-quality, sophisticated, lots of whitespace

**Visual Language:**
- **Colors:** Off-white backgrounds (#f8f7f5), deep blacks, muted sage or terracotta accent
- **Typography:**
  - Display: "Cormorant Garamond" or "Playfair Display"
  - Body: "Crimson Text" or "Source Serif"
- **Layout:** Magazine-style grid, generous margins, unexpected typography scale
- **Details:** Subtle borders, elegant dividers, typographic hierarchy
- **Motion:** Minimal but intentional - page transitions, gentle reveals

### Option C: "Retro Terminal"
**Concept:** 1980s computer terminal meets modern design

**Visual Language:**
- **Colors:** CRT green (#00ff00) or amber (#ffaa00) on black, scanline effects
- **Typography:**
  - Monospace: "VT323" or "Courier Prime"
- **Layout:** Grid-based, terminal-inspired panels
- **Details:** Scanlines, CRT glow, pixelated cursors, ASCII art borders
- **Motion:** Typewriter effects, cursor blinks, matrix-style reveals

---

## Core Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                      │
│  ┌─────────────┐  Conversational Image Generator            │
│  │ [Logo/Icon] │  Session: Active • 12 images generated     │
│  └─────────────┘                                  [Settings] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌─────────────────────────────────────┐ │
│  │   History    │  │                                       │ │
│  │   Sidebar    │  │        Main Canvas                    │ │
│  │              │  │                                       │ │
│  │  [thumb 1]   │  │    ┌──────────────────────────┐     │ │
│  │  [thumb 2]   │  │    │                          │     │ │
│  │  [thumb 3]   │  │    │   Current Image          │     │ │
│  │  [thumb 4]   │  │    │   Display                │     │ │
│  │  [thumb 5]   │  │    │                          │     │ │
│  │  [thumb 6]   │  │    │   1024 x 1024            │     │ │
│  │              │  │    │                          │     │ │
│  │  + New       │  │    └──────────────────────────┘     │ │
│  │              │  │                                       │ │
│  │  [Clear]     │  │    Current prompt: "a blue ball..."  │ │
│  └──────────────┘  │    Seed: 42 • Steps: 28              │ │
│                     └─────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Prompt Input                                            ││
│  │  ┌─────────────────────────────────────────────────┐    ││
│  │  │ Type your prompt or modification...              │    ││
│  │  │                                                  │    ││
│  │  └─────────────────────────────────────────────────┘    ││
│  │  [Generate New]  [Refine Current]  ⚙️ Parameters        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Header Bar
**Content:**
- Logo/branding (left)
- Session status (center) - "Active • 12 generated • 45s avg"
- Settings button (right)

**Styling:**
- Sticky/fixed position
- Semi-transparent backdrop blur
- Height: 60px
- Subtle bottom border

**Interactions:**
- Settings button opens modal/slide-out panel
- Click logo to return to main view

---

### 2. History Sidebar
**Content:**
- Scrollable thumbnail list
- Current image highlighted
- "New" button at bottom
- "Clear Session" button

**Thumbnail Design:**
- Size: 120x120px (square crop)
- Rounded corners (4px)
- Border on hover/selected
- Timestamp overlay (bottom)
- Type indicator (icon: ✨ new, 🔧 refined)

**Interactions:**
- Click thumbnail → Load that image
- Hover → Show full prompt tooltip
- Right-click → Context menu (delete, export, etc.)
- Smooth scroll to latest

**Styling:**
- Width: 180px
- Dark background
- Sticky/fixed position
- Vertical scrolling

---

### 3. Main Canvas
**Content:**
- Large current image display
- Image metadata below
- Generation status/progress

**Image Display:**
- Max size: Fit to viewport (maintain aspect ratio)
- Centered
- Subtle shadow/border
- Zoom on click (optional)

**Metadata Display:**
- Current prompt (truncated with expand)
- Seed, steps, generation time
- Small icons for quick actions (download, share, etc.)

**Loading State:**
- Progress bar (0-100%)
- Current step indicator
- Estimated time remaining
- Partial preview (if possible)

**Empty State:**
- Welcoming message
- Quick start tips
- Sample prompts

---

### 4. Prompt Input Panel
**Content:**
- Large text input (textarea)
- Action buttons (Generate/Refine)
- Parameters toggle

**Input Field:**
- Height: 80px (multi-line)
- Placeholder text changes based on context:
  - Empty session: "Describe the image you want to create..."
  - With current image: "How would you like to refine this image?"
- Character counter (optional)
- Auto-grow height (up to limit)

**Action Buttons:**
- "Generate New" - Primary action (blue/accent color)
- "Refine Current" - Secondary (only enabled when image exists)
- Parameters toggle - Opens parameter panel

**Keyboard Shortcuts:**
- Enter → Generate/Refine (with Shift for new line)
- Ctrl/Cmd + Enter → Force Generate New
- Ctrl/Cmd + K → Clear input

---

### 5. Parameters Panel
**Content:** (Collapsible/expandable)
- Steps slider (10-100, default 28)
- Guidance scale (1.0-5.0, default 3.5)
- Refinement strength (0.1-1.0, default 0.6)
- Seed input (manual or random)
- Advanced options (collapsible)

**Design:**
- Slide-out from right OR accordion below prompt
- Clear visual feedback for values
- Reset to defaults button
- Presets (Quick, Balanced, Quality)

---

### 6. Settings Modal
**Content:**
- Output directory selection
- Default parameters
- Theme toggle (if supporting multiple)
- Model selection (future)
- Clear all history
- About/version info

**Design:**
- Centered modal with backdrop
- Tabbed interface for organization
- Save/Cancel buttons
- Keyboard: Esc to close

---

## Key User Flows

### Flow 1: First Generation
1. User lands on empty canvas
2. Reads welcome message
3. Types prompt in input
4. Clicks "Generate New"
5. Sees progress bar with status
6. Image appears on canvas
7. Thumbnail added to history

### Flow 2: Iterative Refinement
1. User has current image
2. Types modification ("make the ball red")
3. Clicks "Refine Current" (or just Enter)
4. System determines this is refinement
5. Shows progress (img2img)
6. Updated image appears
7. History shows refinement chain

### Flow 3: History Navigation
1. User clicks thumbnail in history
2. Canvas smoothly transitions to that image
3. Prompt input updates to show that prompt
4. User can continue from that point

### Flow 4: Parameter Adjustment
1. User opens parameters panel
2. Adjusts steps/guidance/strength
3. Values saved for next generation
4. Visual feedback on changes

---

## Visual Design Details

### Color System (Studio Dark Example)
```css
:root {
  /* Base */
  --color-bg-primary: #0a0a0a;
  --color-bg-secondary: #171717;
  --color-bg-tertiary: #242424;
  
  /* Text */
  --color-text-primary: #ffffff;
  --color-text-secondary: #a3a3a3;
  --color-text-muted: #525252;
  
  /* Accent */
  --color-accent: #3b82f6;  /* Blue */
  --color-accent-hover: #2563eb;
  
  /* Status */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  
  /* Borders */
  --color-border: #2a2a2a;
  --color-border-hover: #3a3a3a;
}
```

### Typography Scale
```css
/* Display */
--font-size-xl: 2rem;      /* 32px - Page title */
--font-size-lg: 1.5rem;    /* 24px - Section headers */
--font-size-md: 1.125rem;  /* 18px - Prompts */
--font-size-base: 1rem;    /* 16px - Body text */
--font-size-sm: 0.875rem;  /* 14px - Metadata */
--font-size-xs: 0.75rem;   /* 12px - Tiny labels */

/* Line heights */
--line-height-tight: 1.2;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

### Spacing System
```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
--space-2xl: 3rem;     /* 48px */
```

### Animation Timings
```css
--transition-fast: 150ms;
--transition-base: 250ms;
--transition-slow: 400ms;
--easing: cubic-bezier(0.4, 0.0, 0.2, 1);
```

---

## Micro-interactions

### Image Generation Progress
```
State 1: Idle
→ User clicks Generate
State 2: Preparing (spinner, "Loading model...")
→ Model loaded
State 3: Generating (progress bar, "Step 15/28")
→ Each step updates progress
State 4: Complete (fade in image with success animation)
```

### Button Interactions
- Hover: Scale 1.02, brightness increase
- Active: Scale 0.98
- Loading: Spinner inside button, disabled state

### Thumbnail Interactions
- Hover: Border glow, slight scale
- Click: Brief flash, smooth canvas transition
- Selected: Persistent border/glow

### Input Focus
- Focus: Border color change, subtle glow
- Typing: Character count appears
- Submit: Input briefly disabled during generation

---

## Responsive Breakpoints

### Desktop (1280px+)
- Full three-column layout
- Sidebar visible
- Large canvas

### Tablet (768px - 1279px)
- Collapsible sidebar
- Slightly smaller canvas
- Stacked parameter panel

### Mobile (< 768px)
- Single column
- Bottom sheet for history
- Full-width canvas
- Simplified parameters

---

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Arrow keys for history navigation
- Shortcuts for common actions
- Focus indicators visible

### Screen Reader Support
- Semantic HTML
- ARIA labels on icons
- Status announcements
- Image alt text (generated prompts)

### Visual Accessibility
- High contrast mode support
- Adjustable text size
- Reduced motion option
- Clear focus states

---

## Progressive Enhancement

### Core Experience (No JS)
- Basic form submission
- Static page loads
- All functionality works (slower)

### Enhanced Experience (JS)
- Real-time updates
- Live progress
- Smooth animations
- WebSocket updates

### Premium Experience (Modern browsers)
- WebGL previews
- Advanced animations
- Service worker caching
- Offline functionality

---

## Technical Implementation Notes

### State Management
```javascript
// Global state structure
{
  session: {
    id: string,
    currentImage: Image | null,
    history: Image[],
    isGenerating: boolean
  },
  ui: {
    sidebarOpen: boolean,
    parametersOpen: boolean,
    selectedImageId: string | null
  },
  parameters: {
    steps: number,
    guidanceScale: number,
    strength: number,
    seed: number | null
  }
}
```

### WebSocket Events
```javascript
// Client → Server
{ type: 'generate', data: { prompt, params } }
{ type: 'refine', data: { modification, params } }
{ type: 'cancel' }

// Server → Client
{ type: 'progress', data: { step, totalSteps, eta } }
{ type: 'preview', data: { imageData } }  // Optional
{ type: 'complete', data: { image, metadata } }
{ type: 'error', data: { message } }
```

### Image Display Strategy
- Load thumbnails progressively
- Lazy load full-res images
- Use WebP with PNG fallback
- Implement virtual scrolling for long history

---

## Performance Targets

### Initial Load
- First paint: < 1s
- Interactive: < 2s
- Full load: < 3s

### Generation
- API response: < 100ms
- Progress updates: Every 500ms
- Image display: < 500ms after complete

### Interactions
- Button response: < 100ms
- History scroll: 60fps
- Canvas transition: < 300ms

---

## Error States & Edge Cases

### Network Errors
- "Lost connection" banner with retry
- Queue actions when offline
- Resume when reconnected

### Generation Failures
- Clear error message
- Suggested fixes
- Fallback to previous state

### Long Sessions
- Auto-save every 5 minutes
- Warning at 100+ images
- Pagination in history

### Invalid Input
- Real-time validation
- Helpful error messages
- Suggest corrections

---

## Testing Checklist

### Visual
- [ ] All fonts load correctly
- [ ] Colors match design system
- [ ] Animations smooth (60fps)
- [ ] Responsive on all breakpoints
- [ ] Dark mode (if applicable)

### Functional
- [ ] All buttons work
- [ ] Keyboard shortcuts work
- [ ] History navigation smooth
- [ ] Progress updates correctly
- [ ] Session persistence

### Performance
- [ ] Initial load under 3s
- [ ] Smooth scrolling
- [ ] No memory leaks
- [ ] Images load efficiently

### Accessibility
- [ ] Keyboard navigable
- [ ] Screen reader compatible
- [ ] Sufficient contrast
- [ ] Clear focus indicators

---

## Future Enhancements

### Phase 2
- Drag-and-drop image upload
- Side-by-side comparison view
- Favorites/collections
- Export presets (ZIP, PDF)

### Phase 3
- Collaborative sessions
- Comments on images
- Version control (branches)
- Public gallery option

### Phase 4
- Mobile apps (PWA)
- Voice commands
- Gesture controls
- VR preview mode

---

## Design Assets Needed

### Icons
- Generate (✨ sparkles)
- Refine (🔧 wrench or ✏️ pencil)
- New (➕ plus)
- Clear (🗑️ trash)
- Settings (⚙️ gear)
- Download (⬇️ arrow down)
- History (📜 scroll)

### Illustrations
- Empty state graphic
- Error state graphic
- Loading animation
- Success celebration

### Logo
- App icon (square)
- Wordmark (horizontal)
- Favicon (16x16, 32x32)

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**For:** Claude Code implementation with frontend-design skill
