# Conversational Image Generator

A command-line tool for iterative image generation using FLUX.1-dev. Generate images and refine them conversationally, like ChatGPT's DALL-E integration but self-hosted.

## Features

- Generate images from text prompts
- Iteratively refine images with natural language ("make the ball red")
- Session persistence - resume where you left off
- Full generation history tracking
- Seed control for reproducibility
- Optimized for RTX 3090 (24GB VRAM)

## Requirements

- Python 3.10+
- NVIDIA GPU with 12GB+ VRAM (RTX 3090 recommended)
- ~24GB disk space for FLUX.1-dev model

## Installation

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate pillow

# Make the script executable
chmod +x conversational_image_gen.py
```

## Usage

Start the conversational interface:

```bash
python conversational_image_gen.py
```

### Commands

#### Generate a new image:
```
> new a blue ball on green grass
> new a sunset over mountains --steps 50
> new a cat wearing a top hat --seed 12345
```

#### Refine the current image:
```
> make the ball red
> add clouds in the sky
> change to watercolor style
> remove the background
> refine make it photorealistic --strength 0.7
```

#### Utility commands:
```
> history      # Show all generations in this session
> current      # Show current image info
> clear        # Clear session and start fresh
> help         # Show all commands
> exit         # Quit
```

## How It Works

1. **Initial Generation**: Use `new <prompt>` to generate an image from scratch using text-to-image
2. **Refinement**: Just type natural language modifications, and it uses img2img to refine the current image
3. **Context Tracking**: Maintains prompt history and seed for consistency
4. **Session Persistence**: Your current image and history are saved between sessions

### Refinement Strength

The `--strength` parameter controls how much the image changes:
- **0.3**: Subtle changes (adjust colors, lighting)
- **0.6**: Moderate changes (default, good for most modifications)
- **0.8**: Major changes (significant composition changes)

## Examples

### Example Session 1: Creating a Scene
```
> new a medieval castle on a hill at sunset
> add a dragon flying in the sky
> make the dragon red
> add more dramatic clouds
> change to oil painting style
```

### Example Session 2: Character Design
```
> new a cat wearing a wizard hat --seed 42
> make the hat purple
> add a magic wand
> change background to mystical forest
> refine make it more detailed --strength 0.5
```

## Output

All generated images are saved in `./outputs/` with timestamps:
- `gen_001_20241111_143022.png` - Initial generations
- `gen_002_20241111_143045_refined.png` - Refinements

Session state is saved in `./outputs/session.json`

## Tips

1. **Be specific** in initial prompts for better control later
2. **Use lower strength** (0.3-0.5) for subtle changes
3. **Use higher strength** (0.7-0.9) for major composition changes
4. **Track your seeds** - use `current` to see the seed of successful images
5. **Experiment with steps** - 20-30 is usually enough, 50+ for maximum quality

## Prompt Enhancement Ideas

The basic version uses simple keyword matching for refinements. You could enhance it by:
1. Adding an LLM to interpret modifications intelligently
2. Using embeddings to understand semantic changes
3. Implementing inpainting for precise regional edits
4. Adding style transfer capabilities

## Troubleshooting

**Out of memory errors:**
- Reduce image size in the script (change 1024 to 768 or 512)
- Use FLUX.1-schnell instead (faster, less VRAM)
- Enable model CPU offloading

**Slow generation:**
- Reduce steps (20-28 is usually sufficient)
- Use FLUX.1-schnell for 4-step generation

**Model download fails:**
- Ensure you have ~24GB free disk space
- Check your internet connection
- The model will auto-download on first run

## Advanced Usage

### Custom Output Directory
Edit the script and change:
```python
gen = ConversationalImageGen(output_dir="./my_images")
```

### Change Default Parameters
Modify these in the script:
- `steps=28` - Inference steps (20-50)
- `guidance_scale=3.5` - How closely to follow prompt (3.0-4.0)
- `strength=0.6` - Default refinement strength (0.0-1.0)

## License

This tool uses FLUX.1-dev which has a non-commercial license for dev weights.
Check Black Forest Labs licensing for commercial use.

## Credits

- FLUX.1 by Black Forest Labs
- Built with Hugging Face Diffusers
