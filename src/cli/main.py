#!/usr/bin/env python3
"""
CLI interface for Dimpressionist - Conversational Image Generator.

Features:
- Interactive REPL for image generation
- Natural language refinements
- Rich terminal output with progress bars
- Session persistence
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown
from rich.text import Text

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import ConversationalImageGenerator, GenerationConfig
from src.utils import get_config

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║           🎨 Dimpressionist                               ║
║       Conversational Image Generator                      ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner.strip(), border_style="blue"))
    console.print()


def print_help():
    """Print help information."""
    help_text = """
## Commands

### Generate New Image
```
new <prompt>              Generate a new image
new <prompt> --steps 50   Specify inference steps (10-100)
new <prompt> --seed 42    Use specific seed
```

### Refine Current Image
```
<modification>            Natural language refinement
refine <mod> --strength 0.7   Specify refinement strength (0.1-1.0)
```

**Examples:**
- `make the ball red`
- `add clouds in the sky`
- `change to watercolor style`
- `remove the background`

### Utility Commands
```
history    Show generation history
current    Show current image info
clear      Clear session
help       Show this help
exit       Exit program
```

### Tips
- **Lower strength** (0.3-0.5): Subtle changes
- **Higher strength** (0.7-0.9): Major changes
- **Seeds**: Use `current` to see seed of successful images
"""
    console.print(Markdown(help_text))


def print_history(generator: ConversationalImageGenerator):
    """Print generation history as a table."""
    history = generator.get_history()

    if not history:
        console.print("[yellow]No generations yet. Use 'new <prompt>' to start![/yellow]")
        return

    table = Table(title="Generation History", show_header=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", width=10)
    table.add_column("Prompt / Modification", width=40)
    table.add_column("Seed", width=12)
    table.add_column("Image", width=30)

    for i, entry in enumerate(history, 1):
        type_str = "[green]NEW[/green]" if entry.type == "new" else "[cyan]REFINE[/cyan]"
        prompt_text = entry.modification if entry.type == "refinement" else entry.prompt
        if len(prompt_text) > 38:
            prompt_text = prompt_text[:35] + "..."

        image_name = Path(entry.image_path).name
        if len(image_name) > 28:
            image_name = image_name[:25] + "..."

        current_marker = " ←" if entry.id == generator.session.current_generation_id else ""

        table.add_row(
            str(i),
            type_str,
            prompt_text,
            str(entry.seed),
            image_name + current_marker
        )

    console.print(table)
    console.print()


def print_current(generator: ConversationalImageGenerator):
    """Print current image info."""
    current = generator.get_current()

    if not current:
        console.print("[yellow]No current image. Use 'new <prompt>' to generate one![/yellow]")
        return

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Image", str(current.image_path))
    table.add_row("Prompt", current.prompt)
    table.add_row("Seed", str(current.seed))
    table.add_row("Steps", str(current.steps))
    table.add_row("Type", current.type.upper())

    if current.modification:
        table.add_row("Modification", current.modification)
    if current.strength:
        table.add_row("Strength", str(current.strength))
    if current.generation_time:
        table.add_row("Time", f"{current.generation_time:.1f}s")

    console.print(Panel(table, title="Current Image", border_style="green"))
    console.print()


def parse_generation_args(parts: list[str]) -> tuple[str, dict]:
    """Parse generation command arguments."""
    prompt_parts = []
    kwargs = {}

    i = 0
    while i < len(parts):
        if parts[i] == '--steps' and i + 1 < len(parts):
            kwargs['steps'] = int(parts[i + 1])
            i += 2
        elif parts[i] == '--seed' and i + 1 < len(parts):
            kwargs['seed'] = int(parts[i + 1])
            i += 2
        elif parts[i] == '--strength' and i + 1 < len(parts):
            kwargs['strength'] = float(parts[i + 1])
            i += 2
        elif parts[i] == '--guidance' and i + 1 < len(parts):
            kwargs['guidance_scale'] = float(parts[i + 1])
            i += 2
        else:
            prompt_parts.append(parts[i])
            i += 1

    return ' '.join(prompt_parts), kwargs


def generate_with_progress(
    generator: ConversationalImageGenerator,
    prompt: str,
    config: GenerationConfig,
    is_refinement: bool = False
):
    """Generate an image with progress display."""
    action = "Refining" if is_refinement else "Generating"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"[cyan]{action}...", total=config.steps)

        def progress_callback(step: int, total: int, elapsed: float):
            progress.update(task, completed=step, total=total)
            eta = (elapsed / max(step, 1)) * (total - step)
            progress.update(
                task,
                description=f"[cyan]{action}... Step {step}/{total} (ETA: {eta:.1f}s)"
            )

        generator.set_progress_callback(progress_callback)

        try:
            if is_refinement:
                result = generator.refine(prompt, config)
            else:
                result = generator.generate_new(prompt, config)

            progress.update(task, completed=config.steps)

        finally:
            generator.set_progress_callback(None)

    # Display result
    console.print()
    console.print(f"[green]✓[/green] Saved: [bold]{result.image_path}[/bold]")
    console.print(f"  Prompt: {result.prompt}")
    console.print(f"  Seed: {result.seed}")
    if result.entry.generation_time:
        console.print(f"  Time: {result.entry.generation_time:.1f}s")
    console.print()

    return result


def run_interactive(generator: ConversationalImageGenerator):
    """Run the interactive REPL."""
    config = get_config()

    print_banner()
    console.print("Type [bold]help[/bold] for commands or [bold]exit[/bold] to quit.\n")

    # Show session info if resuming
    if generator.get_current():
        console.print("[dim]Resumed previous session.[/dim]")
        print_current(generator)

    while True:
        try:
            user_input = console.input("[bold cyan]🎨 > [/bold cyan]").strip()

            if not user_input:
                continue

            # Parse command
            parts = user_input.split()
            cmd = parts[0].lower()

            # Exit commands
            if cmd in ['exit', 'quit', 'q']:
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            # Help
            if cmd in ['help', 'h', '?']:
                print_help()
                continue

            # History
            if cmd == 'history':
                print_history(generator)
                continue

            # Current
            if cmd == 'current':
                print_current(generator)
                continue

            # Clear
            if cmd == 'clear':
                generator.clear_session()
                console.print("[green]✓[/green] Session cleared!")
                continue

            # New generation
            if cmd == 'new':
                if len(parts) < 2:
                    console.print("[red]Error:[/red] Please provide a prompt after 'new'")
                    continue

                prompt, kwargs = parse_generation_args(parts[1:])
                if not prompt:
                    console.print("[red]Error:[/red] Please provide a prompt")
                    continue

                gen_config = GenerationConfig(
                    steps=kwargs.get('steps', config.default_steps),
                    guidance_scale=kwargs.get('guidance_scale', config.default_guidance_scale),
                    seed=kwargs.get('seed'),
                    width=config.default_width,
                    height=config.default_height
                )

                generate_with_progress(generator, prompt, gen_config, is_refinement=False)
                continue

            # Explicit refinement
            if cmd == 'refine':
                if not generator.get_current():
                    console.print("[red]Error:[/red] No current image to refine. Use 'new <prompt>' first!")
                    continue

                if len(parts) < 2:
                    console.print("[red]Error:[/red] Please provide a modification after 'refine'")
                    continue

                modification, kwargs = parse_generation_args(parts[1:])
                if not modification:
                    console.print("[red]Error:[/red] Please provide a modification")
                    continue

                gen_config = GenerationConfig(
                    steps=kwargs.get('steps', config.default_steps),
                    guidance_scale=kwargs.get('guidance_scale', config.default_guidance_scale),
                    strength=kwargs.get('strength', config.default_strength),
                    width=config.default_width,
                    height=config.default_height
                )

                generate_with_progress(generator, modification, gen_config, is_refinement=True)
                continue

            # Assume it's a refinement request
            if generator.get_current():
                gen_config = GenerationConfig(
                    steps=config.default_steps,
                    guidance_scale=config.default_guidance_scale,
                    strength=config.default_strength,
                    width=config.default_width,
                    height=config.default_height
                )
                generate_with_progress(generator, user_input, gen_config, is_refinement=True)
            else:
                console.print("[red]Error:[/red] No current image to refine. Use 'new <prompt>' to generate one first!")

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print_exception()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dimpressionist - Conversational Image Generator"
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='./outputs',
        help='Output directory for generated images'
    )
    parser.add_argument(
        '--no-load',
        action='store_true',
        help='Start without loading models (for testing)'
    )

    args = parser.parse_args()

    # Initialize generator
    console.print("[dim]Initializing Dimpressionist...[/dim]")

    try:
        generator = ConversationalImageGenerator(
            output_dir=args.output_dir,
            load_models=not args.no_load
        )
    except Exception as e:
        console.print(f"[red]Failed to initialize:[/red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Make sure you have a CUDA-capable GPU and the required dependencies installed.")
        sys.exit(1)

    # Run interactive mode
    run_interactive(generator)


if __name__ == "__main__":
    main()
