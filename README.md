# Dimpressionist

A self-hosted conversational image generation system using FLUX.1-dev. Generate images and refine them through natural language, like ChatGPT's DALL-E integration but running locally.

**Key Advantage:** Self-hosted with FLUX.1-dev means no content guardrails - complete creative freedom.

## Features

- **CLI Interface** - Rich terminal UI with progress bars
- **Web Interface** - Modern dark-themed web UI with real-time updates
- **Conversational Refinement** - Modify images by saying "make the ball red"
- **Session Persistence** - Resume work anytime
- **Full History** - Track all generations with thumbnails
- **Seed Control** - Reproducible results

## Requirements

- Python 3.10+
- NVIDIA GPU with 12GB+ VRAM (RTX 3090 recommended)
- ~24GB disk space for FLUX.1-dev model
- CUDA 12.1+

## Installation

```bash
# Clone the repository
git clone https://github.com/lawless-m/Dimpressionist.git
cd Dimpressionist

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### CLI Interface

```bash
python run_cli.py
```

Commands:
- `new <prompt>` - Generate a new image
- `<modification>` - Refine current image (e.g., "make the ball red")
- `history` - Show generation history
- `current` - Show current image info
- `clear` - Clear session
- `help` - Show all commands
- `exit` - Quit

### Web Interface

```bash
python run_server.py
```

Then open http://localhost:3141 in your browser.

## Usage Examples

### Creating a Scene
```
🎨 > new a medieval castle on a hill at sunset
🎨 > add a dragon flying in the sky
🎨 > make the dragon red
🎨 > change to oil painting style
```

### Character Design
```
🎨 > new a cat wearing a wizard hat --seed 42
🎨 > make the hat purple
🎨 > add a magic wand
🎨 > change background to mystical forest
```

## Parameters

- `--steps` (10-100, default 28) - Inference steps
- `--seed` - Specific seed for reproducibility
- `--strength` (0.1-1.0, default 0.6) - Refinement strength
  - 0.3: Subtle changes
  - 0.6: Moderate changes (default)
  - 0.8: Major changes

## Project Structure

```
Dimpressionist/
├── src/
│   ├── core/           # Core generation engine
│   │   ├── generator.py
│   │   ├── prompt_interpreter.py
│   │   └── session.py
│   ├── cli/            # CLI interface
│   │   └── main.py
│   ├── web/            # Web server and frontend
│   │   ├── api.py
│   │   ├── websocket.py
│   │   └── static/
│   └── utils/          # Utilities
│       ├── config.py
│       └── image_utils.py
├── tests/              # Unit tests
├── outputs/            # Generated images
├── docs/               # Documentation
├── run_cli.py          # CLI entry point
├── run_server.py       # Server entry point
└── requirements.txt
```

## API Endpoints

The web server provides a REST API:

- `POST /api/v1/generate/new` - Generate new image
- `POST /api/v1/generate/refine` - Refine current image
- `GET /api/v1/session/current` - Get session state
- `GET /api/v1/session/history` - Get generation history
- `POST /api/v1/session/clear` - Clear session
- `GET /api/v1/images/{name}` - Get image
- `WS /api/v1/ws` - WebSocket for progress updates

See `docs/API_SPECIFICATION.md` for full documentation.

## Configuration

Environment variables:
- `DIMP_OUTPUT_DIR` - Output directory (default: ./outputs)
- `DIMP_HOST` - Server host (default: 0.0.0.0)
- `DIMP_PORT` - Server port (default: 3141)
- `DIMP_DEVICE` - Device (default: cuda)

## Testing

```bash
# Install pytest
pip install pytest

# Run tests
pytest tests/
```

## Troubleshooting

**Out of memory:**
- Reduce image size (change default from 1024 to 768)
- Reduce steps (20-28 is usually sufficient)
- Use FLUX.1-schnell instead

**Slow generation:**
- Enable torch.compile() in generator.py
- Reduce steps
- Use FLUX.1-schnell for faster 4-step generation

**Model download fails:**
- Ensure ~24GB free disk space
- Check internet connection
- Model downloads on first run

## Documentation

See the `docs/` folder for detailed documentation:
- `PROJECT_SPECIFICATION.md` - Architecture overview
- `API_SPECIFICATION.md` - REST API reference
- `IMPLEMENTATION_GUIDE.md` - Development guide
- `WEB_UI_DESIGN.md` - Frontend design specs

## License

This tool uses FLUX.1-dev which has a non-commercial license.
Check [Black Forest Labs](https://blackforestlabs.ai/) for commercial licensing.

## Credits

- FLUX.1 by Black Forest Labs
- Built with Hugging Face Diffusers
- FastAPI for web framework
- Rich for CLI interface
