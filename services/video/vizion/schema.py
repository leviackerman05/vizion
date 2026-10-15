"""The video contract. Model output is data, never executable source."""

import ast
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "abs": abs,
}


def expression_function(expression: str):
    """Interpret a bounded arithmetic AST without eval, attributes, or arbitrary calls."""
    if len(expression) > 100:
        raise ValueError("A function expression must be at most 100 characters")
    try:
        root = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid function expression") from exc
    if len(list(ast.walk(root))) > 40:
        raise ValueError("Function expression is too complex")

    def visit(node, x):
        if isinstance(node, ast.Expression):
            return visit(node.body, x)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if not math.isfinite(node.value) or abs(node.value) > 1000:
                raise ValueError("Numeric constants must be finite and within 1000")
            return node.value
        if isinstance(node, ast.Name) and node.id in ("x", "pi", "e"):
            return {"x": x, "pi": math.pi, "e": math.e}[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand, x)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
        ):
            left, right = visit(node.left, x), visit(node.right, x)
            if isinstance(node.op, ast.Pow):
                if abs(right) > 8 or abs(left) > 10000:
                    raise ValueError("Exponent or base exceeds rendering limits")
                result = left**right
            elif isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            else:
                result = left / right
            if isinstance(result, complex) or not math.isfinite(result) or abs(result) > 1e8:
                raise ValueError("Expression is outside numeric limits")
            return result
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in SAFE_FUNCTIONS and len(node.args) == 1 and not node.keywords:
                return SAFE_FUNCTIONS[node.func.id](visit(node.args[0], x))
        raise ValueError("Use arithmetic, x, pi, e, sin, cos, sqrt, exp, log, or abs only")

    # Validate all nodes independently, including branches with undefined sample domains.
    allowed = (
        ast.Expression,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.UnaryOp,
        ast.UAdd,
        ast.USub,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Call,
    )
    for node in ast.walk(root):
        if not isinstance(node, allowed):
            raise ValueError("Unsupported function syntax")
        if isinstance(node, ast.Name) and node.id not in {"x", "pi", "e", *SAFE_FUNCTIONS}:
            raise ValueError("Unknown name in function expression")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name)
            or node.func.id not in SAFE_FUNCTIONS
            or len(node.args) != 1
            or node.keywords
        ):
            raise ValueError("Unsupported function call")
        if isinstance(node, ast.Constant) and (
            type(node.value) not in (int, float) or not math.isfinite(node.value) or abs(node.value) > 1000
        ):
            raise ValueError("Invalid numeric constant")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if not isinstance(node.right, (ast.Constant, ast.UnaryOp)):
                raise ValueError("Use a constant exponent")
            exponent = visit(node.right, 1)
            if abs(exponent) > 8:
                raise ValueError("Use an exponent between -8 and 8")

    return lambda x: visit(root, float(x))


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SceneSpec(StrictModel):
    kind: Literal["concept", "steps", "graph", "comparison", "number_line", "geometry"]
    title: str = Field(min_length=1, max_length=60)
    narration: str = Field(min_length=20, max_length=650)
    labels: list[str] = Field(min_length=1, max_length=5)
    equation: str = Field(max_length=90)
    expression: str = Field(max_length=100)
    x_min: float = Field(ge=-10, le=9)
    x_max: float = Field(ge=-9, le=10)
    values: list[float] = Field(max_length=8)
    highlight_index: int = Field(ge=-1, le=7)

    @model_validator(mode="after")
    def validate_scene(self):
        if any(not label.strip() or len(label) > 65 for label in self.labels):
            raise ValueError("Each label must have 1–65 characters")
        if any(not math.isfinite(v) or abs(v) > 10000 for v in self.values):
            raise ValueError("Values must be finite and within 10000")
        if self.x_max - self.x_min < 1:
            raise ValueError("The graph range must span at least one unit")
        if self.kind == "graph":
            function = expression_function(self.expression)
            try:
                for index in range(33):
                    x = self.x_min + (self.x_max - self.x_min) * index / 32
                    result = function(x)
                    if not math.isfinite(result) or abs(result) > 1e8:
                        raise ValueError("Function values exceed numeric rendering limits")
            except (ArithmeticError, ValueError, TypeError) as exc:
                raise ValueError(
                    "Choose a graph domain where the function is real, finite, and bounded"
                ) from exc
        if self.kind == "comparison" and len(self.labels) != 2:
            raise ValueError("A comparison needs exactly two labels")
        if self.kind == "number_line" and not self.values:
            raise ValueError("A number line needs values")
        if self.highlight_index >= len(self.values) and self.highlight_index != -1:
            raise ValueError("The highlighted index must exist in values")
        return self


class Storyboard(StrictModel):
    title: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=10, max_length=200)
    scenes: list[SceneSpec] = Field(min_length=3, max_length=6)

    @model_validator(mode="after")
    def validate_length(self):
        words = sum(len(scene.narration.split()) for scene in self.scenes)
        if not 65 <= words <= 190:
            raise ValueError("The complete narration must contain 65–190 words")
        return self


class ProjectCreate(StrictModel):
    topic: str = Field(min_length=8, max_length=1500)
    audience: Literal["beginner", "intermediate"] = "beginner"
    example: bool = False
