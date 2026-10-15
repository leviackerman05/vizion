"""
Geometric proof template - visual proofs using shapes.

Layout is pre-designed:
- Theorem statement at top
- Main diagram centered
- Labels positioned relative to shapes (no overlaps)
- Step-by-step reveal of proof elements
"""

from app.templates import AnimationTemplate, TemplateMetadata


class GeometricProofTemplate(AnimationTemplate):
    """Template for geometric visual proofs."""
    
    metadata = TemplateMetadata(
        name="geometric_proof",
        description="Visual proof using shapes with guaranteed layout",
        required_params=["theorem", "shapes"],
        optional_params=["proof_steps"]
    )
    
    @classmethod
    def generate_code(cls, params):
        """Generate Manim code for geometric proof."""
        
        theorem = params["theorem"]
        shapes = params["shapes"]
        proof_steps = params.get("proof_steps", [])
        
        # Build shape creation code
        shape_lines = []
        label_lines = []
        
        for i, shape in enumerate(shapes):
            shape_type = shape.get("type", "Square")
            color = shape.get("color", "BLUE")
            label = shape.get("label", "")
            position = shape.get("position", [0, 0, 0])
            
            if shape_type == "Square":
                side = shape.get("side", 2)
                shape_lines.append(
                    f"        shape{i} = Square(side_length={side}, color={color}, fill_opacity=0.5, stroke_width=4)"
                )
            elif shape_type == "Circle":
                radius = shape.get("radius", 1)
                shape_lines.append(
                    f"        shape{i} = Circle(radius={radius}, color={color}, fill_opacity=0.5, stroke_width=4)"
                )
            elif shape_type == "Triangle":
                vertices = shape.get("vertices", [[0,0,0], [2,0,0], [1,2,0]])
                shape_lines.append(
                    f"        shape{i} = Polygon(*{vertices}, color={color}, fill_opacity=0.5, stroke_width=4)"
                )
            elif shape_type == "Rectangle":
                width = shape.get("width", 2)
                height = shape.get("height", 1)
                shape_lines.append(
                    f"        shape{i} = Rectangle(width={width}, height={height}, color={color}, fill_opacity=0.5, stroke_width=4)"
                )
            
            # Position the shape
            if position != [0, 0, 0]:
                shape_lines.append(f"        shape{i}.shift({position[0]}*RIGHT + {position[1]}*UP)")
            
            # Add label
            if label:
                label_lines.append(
                    f'        label{i} = MathTex(r"{label}").scale(0.7).next_to(shape{i}, DOWN, buff=0.3)'
                )
        
        # Build shapes group
        shapes_list = [f"shape{i}" for i in range(len(shapes))]
        shapes_group = f"VGroup({', '.join(shapes_list)})"
        
        # Build labels group if any
        labels_with_text = [(i, s.get('label')) for i, s in enumerate(shapes) if s.get('label')]
        
        # Build label animation code - generate explicit Write() calls for each label
        if labels_with_text:
            write_calls = ', '.join([f"Write(label{i})" for i, _ in labels_with_text])
            label_animation = f"self.play({write_calls})"
        else:
            label_animation = "# No labels"
        
        # Build proof steps code
        steps_code = []
        for i, step in enumerate(proof_steps):
            step_text = step.get("text", "")
            if step_text:
                steps_code.append(f'''
        step{i} = Text("{step_text}").scale(0.6).to_edge(DOWN, buff=0.5)
        self.play(Write(step{i}))
        self.wait(2)
        self.play(FadeOut(step{i}))''')
        
        # Build shape creation animation string
        shape_creates_str = ', '.join([f"Create(shape{i})" for i in range(len(shapes))])
        
        code = f'''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Theorem statement - fixed at top
        theorem = MathTex(r"{theorem}").scale(0.9).to_edge(UP, buff=0.3)
        self.play(Write(theorem))
        self.wait(1)
        
        # Create shapes
{chr(10).join(shape_lines)}
        
        # Organize shapes in a group and center
        shapes_group = {shapes_group}
        shapes_group.move_to(ORIGIN)
        
        # Create labels
{chr(10).join(label_lines)}
        
        # Animate shapes
        self.play({shape_creates_str})
        self.wait(0.5)
        
        # Show labels
        {label_animation}
        {'self.wait(1)' if labels_with_text else ''}
        
{chr(10).join(steps_code) if steps_code else '        # No additional proof steps'}
        
        self.wait(2)
'''
        return code
