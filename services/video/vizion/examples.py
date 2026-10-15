from vizion.schema import SceneSpec, Storyboard


def example_storyboard() -> Storyboard:
    """An explicitly selected example, available without sending anything to an API."""

    def scene(kind, title, narration, labels, **extra):
        return SceneSpec(
            kind=kind,
            title=title,
            narration=narration,
            labels=labels,
            **{
                "equation": "",
                "expression": "",
                "x_min": -4,
                "x_max": 4,
                "values": [],
                "highlight_index": -1,
                **extra,
            },
        )

    return Storyboard(
        title="Why a parabola curves",
        objective="Understand how squaring an input produces a parabola.",
        scenes=[
            scene(
                "concept",
                "One rule. A whole curve.",
                "How does a simple rule create a curved graph? Start with a number, multiply it by itself, and plot the result. This rule is called squaring.",
                ["Choose an input", "Square it", "Plot the output"],
                equation="f(x) = x²",
            ),
            scene(
                "number_line",
                "Small inputs, growing outputs",
                "For inputs zero, one, two, and three, the squared outputs are zero, one, four, and nine. Notice that equal input steps create larger and larger output steps.",
                ["Squared outputs for x = 0, 1, 2, 3"],
                values=[0, 1, 4, 9],
                highlight_index=2,
            ),
            scene(
                "graph",
                "The shape of squaring",
                "Plot those pairs on axes. Negative inputs also have positive squares, so the curve mirrors itself across the vertical axis. The result is a parabola, with its lowest point at zero.",
                ["Input x", "Output x²"],
                equation="f(x) = x²",
                expression="x**2",
                x_min=-3,
                x_max=3,
            ),
            scene(
                "comparison",
                "Same step. Different growth.",
                "A straight line adds the same amount each step. Squaring adds progressively more as positive inputs grow. That changing rate of growth explains why a parabola bends.",
                ["Linear: equal increases", "Quadratic: growing increases"],
                equation="x → x²",
            ),
        ],
    )
