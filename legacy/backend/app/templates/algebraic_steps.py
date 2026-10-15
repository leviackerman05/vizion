"""
Algebraic steps template - shows step-by-step equation transformations.

Layout is pre-designed:
- Title at top
- Each step centered vertically
- Smooth transitions between steps
- Annotations on the side if needed
"""

from app.templates import AnimationTemplate, TemplateMetadata


class AlgebraicStepsTemplate(AnimationTemplate):
    """Template for step-by-step algebraic derivations."""
    
    metadata = TemplateMetadata(
        name="algebraic_steps",
        description="Show step-by-step equation solving with smooth transitions",
        required_params=["steps"],
        optional_params=["title", "show_annotations"]
    )
    
    @classmethod
    def generate_code(cls, params):
        """Generate Manim code for algebraic steps."""
        
        steps = params["steps"]
        title = params.get("title", "Step-by-Step Solution")
        show_annotations = params.get("show_annotations", True)
        
        # Build step transition code
        step_lines = []
        
        for i, step in enumerate(steps):
            equation = step.get("equation", "")
            annotation = step.get("annotation", "")
            
            if i == 0:
                # First step - just display
                step_lines.append(f'''
        # Step {i+1}
        eq{i} = MathTex(r"{equation}").scale(1.2)
        self.play(Write(eq{i}))
        self.wait(1)''')
                
                if show_annotations and annotation:
                    step_lines.append(f'''
        note{i} = Text("{annotation}").scale(0.5).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note{i}))
        self.wait(1)
        self.play(FadeOut(note{i}))''')
            else:
                # Transform from previous step
                step_lines.append(f'''
        # Step {i+1}
        eq{i} = MathTex(r"{equation}").scale(1.2)
        self.play(Transform(eq0, eq{i}))
        self.wait(1)''')
                
                if show_annotations and annotation:
                    step_lines.append(f'''
        note{i} = Text("{annotation}").scale(0.5).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note{i}))
        self.wait(1)
        self.play(FadeOut(note{i}))''')
        
        # Final highlight
        final_step = len(steps) - 1
        step_lines.append(f'''
        # Highlight final answer
        box = SurroundingRectangle(eq0, color=YELLOW, buff=0.2, stroke_width=4)
        self.play(Create(box))
        self.wait(2)''')
        
        code = f'''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Title - fixed at top
        title = Text("{title}").scale(0.8).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.5)
        
{chr(10).join(step_lines)}
'''
        return code
