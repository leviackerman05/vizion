
import os
import json
from dotenv import load_dotenv
from app.template_engine import extract_parameters, generate_from_template

load_dotenv()

def test_extraction():
    prompt = "Prove Pythagorean theorem"
    print(f"Testing prompt: '{prompt}'")
    
    # Test extraction directly
    print("\n--- Testing Extraction ---")
    params = extract_parameters("geometric_proof", prompt)
    print(json.dumps(params, indent=2))
    
    # Test full generation
    print("\n--- Testing Generation ---")
    code, status = generate_from_template(prompt)
    print(f"Status: {status}")
    if code:
        print("Code generated successfully")
        print(code)

if __name__ == "__main__":
    test_extraction()
