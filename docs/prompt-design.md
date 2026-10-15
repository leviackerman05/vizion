# Lesson planning

`services/video/vizion/prompts.py` contains the versioned system prompt; `schema.py` is its executable output contract. Every successful plan records provider, model, and prompt version. Topic text is untrusted subject matter, separate from system instructions.

The old code asked the model for executable source and repaired arbitrary output. This MVP requests a lesson plan with a constrained visual vocabulary, rendered by checked-in scenes. Prompt changes improve pedagogy and visual choices without granting execution access.

The prompt requires one objective, motivating examples, correct arithmetic/units, natural narration, and a takeaway. Target: 90-140 words; schema bounds: 65-190. Every scene type and JSON key is specified. It asks for actual numbers and relationships: binary search must display numeric arrays and the correct middle index, rather than a card saying 'sorted list'. Broad requests are narrowed honestly.

Validation feedback includes errors without raw input values and preserves the topic across up to three requests. Credential/provider/quota failures give actionable errors. A built-in example requires explicit selection.

## Change checks

After prompt/schema changes, generate and review a varied set: parabola, binary search, Newton's first law, compound interest, and Pythagorean theorem. Check factual correctness, correspondence between narration and visuals, domain/index arithmetic, readability, and timing. Render at least one real narrated lesson before release. Valid JSON alone does not establish teaching quality.

Initial real-provider checks produced a valid parabola plan and a 122-word binary-search lesson. The latter compared indices 3, 5, then 4 in `[2, 4, 6, 8, 10, 12, 14]` to find 10. These are smoke checks, not a broad benchmark. Add reviewed regression examples and topic-specific numerical checks before expanding rendering freedom.
