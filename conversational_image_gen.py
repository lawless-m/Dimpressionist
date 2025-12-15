#!/usr/bin/env python3
"""
Conversational Image Generator
Allows iterative refinement of images through natural language commands.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import torch
from diffusers import FluxPipeline, FluxImg2ImgPipeline
from PIL import Image

class ConversationalImageGen:
    def __init__(self, output_dir="./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.session_file = self.output_dir / "session.json"
        self.current_image = None
        self.current_prompt = ""
        self.current_seed = None
        self.generation_count = 0
        self.history = []
        
        print("🎨 Loading FLUX.1-dev model... (this may take a minute)")
        self.txt2img_pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16
        )
        self.txt2img_pipe.to("cuda")
        
        self.img2img_pipe = FluxImg2ImgPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16
        )
        self.img2img_pipe.to("cuda")
        
        print("✅ Model loaded! Ready to generate.\n")
        
        # Load previous session if exists
        self.load_session()
    
    def load_session(self):
        """Load previous session if it exists"""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                self.current_prompt = data.get('current_prompt', '')
                self.current_seed = data.get('current_seed')
                self.generation_count = data.get('generation_count', 0)
                self.history = data.get('history', [])
                last_image = data.get('current_image')
                if last_image and Path(last_image).exists():
                    self.current_image = last_image
                    print(f"📂 Loaded previous session. Last image: {last_image}")
                    print(f"   Last prompt: {self.current_prompt}\n")
    
    def save_session(self):
        """Save current session state"""
        data = {
            'current_prompt': self.current_prompt,
            'current_seed': self.current_seed,
            'current_image': self.current_image,
            'generation_count': self.generation_count,
            'history': self.history
        }
        with open(self.session_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_from_scratch(self, prompt, steps=28, seed=None):
        """Generate a new image from text prompt"""
        if seed is None:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
        
        self.current_seed = seed
        generator = torch.Generator("cuda").manual_seed(seed)
        
        print(f"🎨 Generating: '{prompt}'")
        print(f"   Seed: {seed}, Steps: {steps}")
        
        image = self.txt2img_pipe(
            prompt,
            guidance_scale=3.5,
            num_inference_steps=steps,
            height=1024,
            width=1024,
            generator=generator
        ).images[0]
        
        # Save image
        self.generation_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{self.generation_count:03d}_{timestamp}.png"
        filepath = self.output_dir / filename
        image.save(filepath)
        
        self.current_image = str(filepath)
        self.current_prompt = prompt
        
        # Add to history
        self.history.append({
            'type': 'new',
            'prompt': prompt,
            'seed': seed,
            'steps': steps,
            'image': str(filepath)
        })
        
        self.save_session()
        print(f"✅ Saved to: {filepath}\n")
        
        return image
    
    def refine_image(self, modification, strength=0.6, steps=28):
        """Refine current image based on modification request"""
        if self.current_image is None:
            print("❌ No current image to refine. Generate one first!")
            return None
        
        # Load current image
        image = Image.open(self.current_image)
        
        # Build new prompt incorporating the modification
        new_prompt = self.build_refined_prompt(modification)
        
        print(f"🔧 Refining: '{modification}'")
        print(f"   New prompt: '{new_prompt}'")
        print(f"   Strength: {strength}, Steps: {steps}")
        
        generator = torch.Generator("cuda").manual_seed(self.current_seed)
        
        refined = self.img2img_pipe(
            prompt=new_prompt,
            image=image,
            strength=strength,
            guidance_scale=3.5,
            num_inference_steps=steps,
            generator=generator
        ).images[0]
        
        # Save refined image
        self.generation_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{self.generation_count:03d}_{timestamp}_refined.png"
        filepath = self.output_dir / filename
        refined.save(filepath)
        
        self.current_image = str(filepath)
        self.current_prompt = new_prompt
        
        # Add to history
        self.history.append({
            'type': 'refinement',
            'modification': modification,
            'prompt': new_prompt,
            'strength': strength,
            'steps': steps,
            'image': str(filepath)
        })
        
        self.save_session()
        print(f"✅ Saved to: {filepath}\n")
        
        return refined
    
    def build_refined_prompt(self, modification):
        """
        Intelligently build a new prompt based on modification request.
        This is a simple implementation - could be enhanced with an LLM.
        """
        mod_lower = modification.lower()
        
        # Simple keyword-based modifications
        # Check for color changes
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 
                  'pink', 'black', 'white', 'brown', 'grey', 'gray']
        
        for color in colors:
            if color in mod_lower:
                # Try to replace existing colors in prompt
                for old_color in colors:
                    if old_color in self.current_prompt.lower():
                        return self.current_prompt.replace(old_color, color)
        
        # Check for "make X Y" or "change X to Y" patterns
        if "make" in mod_lower or "change" in mod_lower:
            # Append the modification to the prompt
            return f"{self.current_prompt}, {modification}"
        
        # Check for additions
        if "add" in mod_lower:
            return f"{self.current_prompt}, with {modification.replace('add', '').strip()}"
        
        # Check for removals
        if "remove" in mod_lower or "without" in mod_lower:
            # This is tricky without NLP, just note it
            return f"{self.current_prompt}, {modification}"
        
        # Default: append the modification
        return f"{self.current_prompt}, {modification}"
    
    def show_history(self):
        """Display generation history"""
        if not self.history:
            print("No history yet!")
            return
        
        print("\n📜 Generation History:")
        print("=" * 60)
        for i, entry in enumerate(self.history, 1):
            print(f"\n{i}. {entry['type'].upper()}")
            if entry['type'] == 'new':
                print(f"   Prompt: {entry['prompt']}")
                print(f"   Seed: {entry['seed']}, Steps: {entry['steps']}")
            else:
                print(f"   Modification: {entry['modification']}")
                print(f"   Result prompt: {entry['prompt']}")
                print(f"   Strength: {entry['strength']}, Steps: {entry['steps']}")
            print(f"   Image: {entry['image']}")
        print("=" * 60 + "\n")
    
    def clear_session(self):
        """Clear current session"""
        self.current_image = None
        self.current_prompt = ""
        self.current_seed = None
        self.history = []
        if self.session_file.exists():
            self.session_file.unlink()
        print("✅ Session cleared!\n")

def print_help():
    """Print help message"""
    print("""
Conversational Image Generator - Commands:
==========================================

GENERATE NEW IMAGE:
  new <prompt>              Generate a new image from scratch
  new <prompt> --steps N    Generate with N inference steps (default: 28)
  new <prompt> --seed N     Generate with specific seed

REFINE CURRENT IMAGE:
  <modification>            Refine current image with natural language
                           Examples: "make the ball red"
                                    "add a sunset in background"
                                    "change to watercolor style"
  
  refine <mod> --strength N Refine with specific strength (0.0-1.0)
                           0.3 = subtle, 0.6 = moderate, 0.8 = major
                           
UTILITY:
  history                   Show generation history
  current                   Show current image info
  clear                     Clear current session
  help                      Show this message
  exit                      Exit program

Examples:
  > new a blue ball on green grass
  > make the ball red
  > add clouds in the sky
  > change to sunset lighting
""")

def main():
    print("=" * 60)
    print("  🎨 Conversational Image Generator")
    print("=" * 60)
    print("\nType 'help' for commands or 'exit' to quit.\n")
    
    gen = ConversationalImageGen()
    
    while True:
        try:
            user_input = input("🎨 > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() in ['help', 'h', '?']:
                print_help()
                continue
            
            if user_input.lower() == 'history':
                gen.show_history()
                continue
            
            if user_input.lower() == 'current':
                if gen.current_image:
                    print(f"\n📷 Current image: {gen.current_image}")
                    print(f"   Prompt: {gen.current_prompt}")
                    print(f"   Seed: {gen.current_seed}\n")
                else:
                    print("\n❌ No current image. Generate one first!\n")
                continue
            
            if user_input.lower() == 'clear':
                gen.clear_session()
                continue
            
            # Parse commands
            parts = user_input.split()
            
            if parts[0].lower() == 'new':
                # Generate new image
                prompt_parts = []
                steps = 28
                seed = None
                
                i = 1
                while i < len(parts):
                    if parts[i] == '--steps' and i + 1 < len(parts):
                        steps = int(parts[i + 1])
                        i += 2
                    elif parts[i] == '--seed' and i + 1 < len(parts):
                        seed = int(parts[i + 1])
                        i += 2
                    else:
                        prompt_parts.append(parts[i])
                        i += 1
                
                prompt = ' '.join(prompt_parts)
                if prompt:
                    gen.generate_from_scratch(prompt, steps=steps, seed=seed)
                else:
                    print("❌ Please provide a prompt after 'new'")
            
            elif parts[0].lower() == 'refine':
                # Explicit refinement command
                mod_parts = []
                strength = 0.6
                steps = 28
                
                i = 1
                while i < len(parts):
                    if parts[i] == '--strength' and i + 1 < len(parts):
                        strength = float(parts[i + 1])
                        i += 2
                    elif parts[i] == '--steps' and i + 1 < len(parts):
                        steps = int(parts[i + 1])
                        i += 2
                    else:
                        mod_parts.append(parts[i])
                        i += 1
                
                modification = ' '.join(mod_parts)
                if modification:
                    gen.refine_image(modification, strength=strength, steps=steps)
                else:
                    print("❌ Please provide a modification after 'refine'")
            
            else:
                # Assume it's a refinement request
                if gen.current_image:
                    gen.refine_image(user_input)
                else:
                    print("❌ No current image to refine. Use 'new <prompt>' to generate one first!")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
