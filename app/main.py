from manim import *

class RedCircleToSquare(Scene):
    def construct(self):
        # Create a red circle
        circle = Circle(color=RED)

        # Animate the creation of the circle
        self.play(Create(circle))

        # Change the shape to a square
        self.play(Transform(circle, Square(color=RED)))

        # Hold the final state for a second
        self.wait(1)