import os
import subprocess

PROMPT_FILE = "output/image_prompts.txt"
OUTPUT_DIR = "images/"
MODEL_NAME = "stable-diffusion-1.5"  # or whatever you're using in InvokeAI

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(PROMPT_FILE, "r") as f:
    for line in f:
        if not line.strip():
            continue
        # Format: page2_image1: prompt text
        name, prompt = line.split(":", 1)
        name = name.strip()
        prompt = prompt.strip()

        output_path = os.path.join(OUTPUT_DIR, f"{name}.jpg")

        print(f"Generating {output_path}...")

        subprocess.run([
            "python",
            "scripts/invoke.py",  # or wherever your invoke CLI is
            "--model", MODEL_NAME,
            "--prompt", prompt,
            "--outdir", OUTPUT_DIR,
            "--filename", f"{name}.jpg"
        ])
