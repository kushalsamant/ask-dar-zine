import os

# Define your directory tree
structure = {
    "ASK Daily Architectural Research Zine": [
        "ask_zine_autogen.py",
        "config/vol_01.yaml",
        "models/phi-2.gguf",           # placeholder, you’ll drop actual model here
        "output/thesis.txt",
        "output/caption.txt",
        "output/case_study.txt",
        "output/qna.txt",
        "output/footnotes.txt",
        "output/image_prompts.txt",
        "images/page2_image1.jpg"      # placeholder, real image will come later
    ]
}

# Create structure
for root, files in structure.items():
    for path in files:
        full_path = os.path.join(root, path)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)

        # Create placeholder file if it doesn't exist
        if not os.path.exists(full_path):
            with open(full_path, "w") as f:
                if full_path.endswith(".yaml"):
                    f.write('volume: "01"\ntheme: "Assemblage, Friction & the City"\nsubhead: "How Mess Makes Meaning"\ncase_study: random\nstyle: manifesto\npages: 5\nlanguage: english\n')
                elif full_path.endswith(".txt"):
                    f.write(f"Placeholder for {os.path.basename(full_path)}\n")
                elif full_path.endswith(".gguf"):
                    f.write("PLACEHOLDER: Drop your Phi-2 .gguf model here.\n")
                elif full_path.endswith(".py"):
                    f.write("# Placeholder for ask_zine_autogen.py script\n")
                elif full_path.endswith(".jpg"):
                    f.write("FAKE IMAGE FILE. Replace with actual SD output.\n")

print("✅ Project structure created.")
