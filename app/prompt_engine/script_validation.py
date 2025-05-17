import re

def check_for_invalid_manim_methods(script_code: str) -> list:
    """
    Scans the script for known invalid or hallucinated Manim methods.
    Returns a list of violations found in the code.
    """
    known_invalid_methods = [
        "add_coordinate_labels",
        "move_arrow_to",
        "highlight_segment",
        "draw_text_box",
        "make_axis_grid",
        "mark_origin",
        "animate_point_path",
    ]

    violations = []
    for method in known_invalid_methods:
        pattern = rf"\\b{method}\\b"
        if re.search(pattern, script_code):
            violations.append(method)

    return violations
