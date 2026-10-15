from sentence_transformers import SentenceTransformer, util

# Mapping of intent → purpose
INTENT_DESCRIPTIONS = {
    "math_proof": "a mathematical identity or equation that needs visual proof or step-by-step derivation",
    "graph_function": "a function that should be plotted using Axes and labeled curves",
    "concept_explanation": "a general abstract topic that needs to be visualized using shapes or diagrams",
    "physics_simulation": "a physical scenario involving motion, force, or particles",
    "step_by_step_process": "an algorithm or logical process to be animated in sequence",
    "timeline_animation": "a sequence of historical or ordered events on a timeline",
    "formula_building": "a mathematical formula being derived over steps",
    "recipe_instruction": "a cooking recipe or food preparation tutorial",
}

model = SentenceTransformer("all-MiniLM-L6-v2")
INTENT_LABELS = list(INTENT_DESCRIPTIONS.keys())
INTENT_TEXTS = list(INTENT_DESCRIPTIONS.values())
intent_embeddings = model.encode(INTENT_TEXTS, convert_to_tensor=True)

def detect_intent(user_prompt: str) -> str:
    query_embedding = model.encode(user_prompt, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, intent_embeddings)[0]
    best_match_idx = scores.argmax().item()
    return INTENT_LABELS[best_match_idx]
