def detect_intent(user_prompt: str) -> str:
    prompt = user_prompt.lower()

    if any(keyword in prompt for keyword in ["prove", "identity", "sum", "pythagorean"]):
        return "math_proof"

    if any(keyword in prompt for keyword in ["graph", "plot", "curve", "function"]):
        return "graph_function"

    if any(keyword in prompt for keyword in ["simulate", "projectile", "falling", "gravity", "velocity", "motion"]):
        return "physics_simulation"

    if any(keyword in prompt for keyword in ["step by step", "explain", "teach", "instruction", "binary search", "factor"]):
        return "step_by_step_process"

    if any(keyword in prompt for keyword in ["timeline", "history", "events", "sequence"]):
        return "timeline_animation"

    if any(keyword in prompt for keyword in ["derive", "derivation", "formula", "build equation"]):
        return "formula_building"

    if any(keyword in prompt for keyword in ["recipe", "cook", "prepare", "ingredients", "dish", "how to make"]):
        return "recipe_instruction"

    return "concept_explanation"  # Default fallback
