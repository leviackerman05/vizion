"""
Function graph template - plots one or more mathematical functions.

Layout is pre-designed to avoid overlaps:
- Title at top
- Axes centered and scaled
- Function labels positioned above axes
- Legend in top-right corner
"""

from app.templates import AnimationTemplate, TemplateMetadata


class FunctionGraphTemplate(AnimationTemplate):
    """Template for plotting mathematical functions."""
    
    metadata = TemplateMetadata(
        name="function_graph",
        description="Plot one or more mathematical functions with proper layout",
        required_params=["functions"],
        optional_params=["title", "x_range", "y_range", "show_grid"]
    )
    
    @classmethod
    def generate_code(cls, params):
        """Generate Manim code for function graph."""
        
        functions = params["functions"]
        title = params.get("title", "Function Graph")
        x_range = params.get("x_range", [-5, 5, 1])
        y_range = params.get("y_range", [-5, 5, 1])
        show_grid = params.get("show_grid", False)
        
        # Build function plotting code
        function_lines = []
        label_lines = []
        
        for i, func in enumerate(functions):
            expr = func.get("expr", "x")
            label = func.get("label", f"f{i+1}(x)")
            color = func.get("color", ["BLUE", "RED", "GREEN", "YELLOW", "PURPLE"][i % 5])
            
            function_lines.append(
                f"        graph{i} = axes.plot(lambda x: {expr}, color={color}, stroke_width=4)"
            )
            label_lines.append(
                f'        label{i} = MathTex(r"{label}").scale(0.6).set_color({color})'
            )
        
        # Build legend
        legend_items = [f"label{i}" for i in range(len(functions))]
        legend_group = f"VGroup({', '.join(legend_items)}).arrange(DOWN, buff=0.2, aligned_edge=LEFT)"
        
        code = f'''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Title - fixed at top
        title = Text("{title}").scale(0.8).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.5)
        
        # Axes - centered and scaled to fit
        axes = Axes(
            x_range={x_range},
            y_range={y_range},
            x_length=7,
            y_length=5,
            axis_config={{"color": WHITE, "stroke_width": 2}}
        ).scale(0.75)
        
        x_label = axes.get_x_axis_label("x")
        y_label = axes.get_y_axis_label("y")
        
        self.play(Create(axes), Write(x_label), Write(y_label))
        self.wait(0.5)
        
        # Functions
{chr(10).join(function_lines)}
        
        # Labels - positioned in top-right legend
{chr(10).join(label_lines)}
        
        legend = {legend_group}
        legend.scale(0.8).to_corner(UR, buff=0.5)
        
        # Animate graphs
        self.play(*[Create(graph{i}) for i in range({len(functions)})])
        self.wait(0.5)
        
        # Show legend
        self.play(FadeIn(legend))
        self.wait(2)
'''
        return code
