from script_gen import generate_script
import subprocess
import re

def main():
    prompt = input("📝 Enter your prompt: ")
    output_file = "generated_scene.py"
    model = "gemini-2.0-flash"  # Or "llama3" if still using Ollama for testing

    generate_script(prompt, model=model, output_path=output_file)

    with open(output_file, "r") as f:
        script_content = f.read()

    if "class GeneratedScene" not in script_content:
        script_content = script_content.replace("class MyScene", "class GeneratedScene")
        with open(output_file, "w") as f:
            f.write(script_content)
        print("✅ Updated script to use 'GeneratedScene' class.")

    # Automatically extract the class name from the script
    class_name_match = re.search(r'class (\w+)', script_content)
    if class_name_match:
        class_name = class_name_match.group(1)
        print(f"✅ Found class name: {class_name}")
    else:
        class_name = "GeneratedScene"
        print("❌ No class name found, using default 'GeneratedScene'")

    subprocess.run(["manim", "-pql", output_file, class_name])

if __name__ == "__main__":
    main()
