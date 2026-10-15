"""Trusted Manim scene. The only per-job input is validated JSON, never generated code."""

import json
import math
import os
import textwrap
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Axes,
    Circle,
    Create,
    Dot,
    FadeIn,
    Indicate,
    LaggedStart,
    Line,
    Polygon,
    RoundedRectangle,
    Scene,
    Text,
    VGroup,
    VMobject,
    config,
    linear,
)

from vizion.schema import SceneSpec, expression_function

BG, PANEL, WHITE, MUTED, TEAL, GOLD = "#0B1019", "#151E2C", "#EEF3FA", "#91A1B9", "#79E1C5", "#F2C982"
FONT = "Arial" if os.name == "nt" else "DejaVu Sans"


def label(text, size=28, color=WHITE, width=11):
    obj = Text(text, font=FONT, font_size=size, color=color, disable_ligatures=True)
    if obj.width > width:
        obj.scale_to_fit_width(width)
    return obj


class LessonScene(Scene):
    def construct(self):
        payload = json.loads(Path(os.environ["VIZION_SCENE_PATH"]).read_text(encoding="utf-8"))
        spec = SceneSpec.model_validate(payload["scene"])
        duration = float(payload["duration"])
        config.background_color = BG
        self.camera.background_color = BG
        brand = label("VIZION   /   EXPLAINED VISUALLY", 14, TEAL).to_corner(UP + LEFT, buff=0.45)
        counter = label(f"{payload['index']:02} / {payload['total']:02}", 16, MUTED).to_corner(
            UP + RIGHT, buff=0.45
        )
        heading = label(spec.title, 39, width=12.5).move_to(UP * 2.65)
        rule = Line(LEFT * 6.15, RIGHT * 6.15, color=PANEL).move_to(UP * 2.1)
        self.add(brand, counter, heading, rule)

        # Captions follow the measured audio clock, independent of visual animation lengths.
        words = spec.narration.split()
        chunks = [" ".join(words[i : i + 9]) for i in range(0, len(words), 9)]
        weight = sum(map(len, chunks)) or 1
        thresholds, running = [], 0
        for chunk in chunks:
            running += len(chunk) / weight * duration
            thresholds.append(running)
        captions = label(chunks[0], 23, width=11.7).move_to(DOWN * 3.12)
        current = [0]

        def sync_caption(mobject):
            index = next((i for i, end in enumerate(thresholds) if self.time < end), len(chunks) - 1)
            if index != current[0]:
                mobject.become(label(chunks[index], 23, width=11.7).move_to(DOWN * 3.12))
                current[0] = index

        captions.add_updater(sync_caption)
        caption_bg = RoundedRectangle(
            width=12.4, height=0.72, corner_radius=0.14, fill_color=PANEL, fill_opacity=0.85, stroke_opacity=0
        ).move_to(DOWN * 3.12)
        self.add(caption_bg, captions)
        self.bring_to_front(captions)

        if spec.kind == "graph":
            self.graph(spec, duration)
        elif spec.kind == "number_line":
            self.number_line(spec, duration)
        elif spec.kind == "geometry":
            self.geometry(spec, duration)
        elif spec.kind == "comparison":
            self.comparison(spec, duration)
        elif spec.kind == "steps":
            self.steps(spec, duration)
        else:
            self.concept(spec, duration)
        remaining = duration - self.time
        if remaining > 0:
            self.wait(remaining)
        captions.clear_updaters()

    def equation(self, spec, y=-1.7):
        if spec.equation:
            equation = label(spec.equation, 35, GOLD).move_to(UP * y)
            self.play(FadeIn(equation, shift=UP * 0.15), run_time=0.6)

    def concept(self, spec, duration):
        labels = spec.labels
        card_width = min(2.65, (12 - 0.4 * (len(labels) - 1)) / len(labels))
        cards = VGroup()
        for text in labels:
            box = RoundedRectangle(
                width=card_width,
                height=1.65,
                corner_radius=0.2,
                fill_color=PANEL,
                fill_opacity=1,
                stroke_color=TEAL,
                stroke_width=1.3,
            )
            caption = label("\n".join(textwrap.wrap(text, 19)), 24, width=card_width - 0.4).move_to(box)
            if caption.height > 1.25:
                caption.scale_to_fit_height(1.25)
            cards.add(VGroup(box, caption))
        cards.arrange(RIGHT, buff=0.4).move_to(UP * 0.3)
        self.play(
            LaggedStart(*[FadeIn(card, shift=UP * 0.25) for card in cards], lag_ratio=0.25), run_time=1.2
        )
        if len(cards) > 1:
            arrows = [
                Arrow(a.get_right(), b.get_left(), buff=0.08, color=GOLD, stroke_width=2)
                for a, b in zip(cards, list(cards)[1:])
            ]
            self.play(*[Create(arrow) for arrow in arrows], run_time=0.7)
        self.equation(spec)
        for card in cards:
            self.play(Indicate(card[0], color=TEAL, scale_factor=1.035), run_time=min(1.1, duration / 8))

    def steps(self, spec, duration):
        rows = VGroup()
        for index, text in enumerate(spec.labels):
            number = Circle(radius=0.23, color=TEAL, fill_color=TEAL, fill_opacity=0.12)
            numeral = label(str(index + 1), 19, TEAL).move_to(number)
            caption = label(text, 27, width=9.2).next_to(number, RIGHT, buff=0.35)
            rows.add(VGroup(number, numeral, caption))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(UP * 0.15)
        interval = max(0.7, (duration - 2.5) / len(rows))
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0, interval - 0.6))
        self.equation(spec, -2.05)

    def comparison(self, spec, duration):
        columns = VGroup()
        for index, text in enumerate(spec.labels):
            color = TEAL if index == 0 else GOLD
            card = RoundedRectangle(
                width=5.4,
                height=2.7,
                corner_radius=0.22,
                fill_color=PANEL,
                fill_opacity=1,
                stroke_color=color,
                stroke_width=1.5,
            )
            caption = label("\n".join(textwrap.wrap(text, 25)), 29, color, width=4.7).move_to(card)
            columns.add(VGroup(card, caption))
        columns.arrange(RIGHT, buff=0.65).move_to(UP * 0.15)
        self.play(
            LaggedStart(*[FadeIn(column, shift=UP * 0.2) for column in columns], lag_ratio=0.5), run_time=1.5
        )
        self.equation(spec, -2)
        for column in columns:
            self.play(Indicate(column[0], scale_factor=1.025), run_time=1)
            self.wait(min(1.5, duration / 8))

    def number_line(self, spec, duration):
        cells = VGroup()
        size = min(1.25, 9.5 / len(spec.values))
        for index, value in enumerate(spec.values):
            box = RoundedRectangle(
                width=size,
                height=1.15,
                corner_radius=0.12,
                fill_color=PANEL,
                fill_opacity=1,
                stroke_color=MUTED,
                stroke_width=1,
            )
            number = label(f"{value:g}", 31, width=size * 0.8).move_to(box)
            idx = label(str(index), 16, MUTED).next_to(box, DOWN, buff=0.18)
            cells.add(VGroup(box, number, idx))
        cells.arrange(RIGHT, buff=0.18).move_to(UP * 0.15)
        self.play(
            LaggedStart(*[FadeIn(cell, shift=UP * 0.15) for cell in cells], lag_ratio=0.15), run_time=1.3
        )
        description = label(spec.labels[0], 25, MUTED).move_to(UP * 1.4)
        self.play(FadeIn(description), run_time=0.5)
        if len(spec.labels) > 1:
            detail = label("  ·  ".join(spec.labels[1:]), 21, MUTED, width=11.5).move_to(DOWN * 1.15)
            self.play(FadeIn(detail), run_time=0.4)
        if spec.highlight_index >= 0:
            selected = cells[spec.highlight_index]
            self.play(
                selected[0].animate.set_stroke(TEAL, width=3).set_fill(TEAL, opacity=0.15), run_time=0.6
            )
            marker = Arrow(UP * 1.2, UP * 0.7, color=TEAL).next_to(selected[0], UP, buff=0.12)
            self.play(FadeIn(marker), run_time=0.5)
        self.equation(spec, -1.8)

    def graph(self, spec, duration):
        function = expression_function(spec.expression)
        xs = np.linspace(spec.x_min, spec.x_max, 161)
        ys = [function(float(x)) for x in xs]
        if any(not math.isfinite(y) for y in ys):
            raise ValueError("Function must be finite throughout its graph domain")
        low, high = min(0, min(ys)), max(0, max(ys))
        span = max(1, high - low)
        low, high = low - span * 0.1, high + span * 0.15
        axes = Axes(
            x_range=[spec.x_min, spec.x_max, max(1, (spec.x_max - spec.x_min) / 6)],
            y_range=[low, high, max(1, (high - low) / 5)],
            x_length=8.6,
            y_length=3.7,
            axis_config={"color": MUTED, "stroke_width": 1.4, "include_tip": False},
            tips=False,
        ).move_to(UP * 0.05 + LEFT * 0.35)
        curve = VMobject(color=TEAL, stroke_width=4)
        curve.set_points_smoothly([axes.c2p(x, y) for x, y in zip(xs, ys)])
        x_label = label(spec.labels[0], 18, MUTED, width=1.3).next_to(axes.x_axis, RIGHT, buff=0.15)
        y_label = (
            label(spec.labels[1] if len(spec.labels) > 1 else "Output", 16, MUTED, width=2)
            .next_to(axes.y_axis, LEFT, buff=0.3)
            .align_to(axes, UP)
        )
        tick_labels = VGroup()
        for x in np.linspace(spec.x_min, spec.x_max, 5):
            tick_labels.add(label(f"{x:g}", 14, MUTED, width=0.6).next_to(axes.c2p(x, 0), DOWN, buff=0.14))
        step = max(1, round(span / 4))
        for y in range(math.ceil(low / step) * step, math.floor(high / step) * step + 1, step):
            if y != 0:
                anchor_x = max(spec.x_min, min(spec.x_max, 0))
                tick_labels.add(
                    label(f"{y:g}", 14, MUTED, width=0.6).next_to(axes.c2p(anchor_x, y), LEFT, buff=0.13)
                )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), FadeIn(tick_labels), run_time=0.8)
        self.play(Create(curve), run_time=min(4, duration * 0.25), rate_func=linear)
        for x in np.linspace(spec.x_min, spec.x_max, 5)[1:-1]:
            point = Dot(axes.c2p(x, function(float(x))), radius=0.065, color=GOLD)
            self.play(FadeIn(point), run_time=0.25)
        self.equation(spec, -2.1)

    def geometry(self, spec, duration):
        p, q, r = np.array([-1.5, -1.2, 0]), np.array([1.5, -1.2, 0]), np.array([-1.5, 1.05, 0])
        square_a = Polygon(p, q, q + DOWN * 3, p + DOWN * 3, color=TEAL, fill_opacity=0.2)
        square_b = Polygon(r, p, p + LEFT * 2.25, r + LEFT * 2.25, color=GOLD, fill_opacity=0.2)
        outward = np.array([2.25, 3, 0])
        square_c = Polygon(q, r, r + outward, q + outward, color="#8D9EEF", fill_opacity=0.2)
        triangle = Polygon(p, q, r, color=WHITE, fill_opacity=0.08)
        objects = VGroup(square_a, square_b, square_c, triangle)
        texts = VGroup(
            *[
                label(text, 32, color).move_to(square)
                for text, color, square in [
                    ("a²", TEAL, square_a),
                    ("b²", GOLD, square_b),
                    ("c²", "#8D9EEF", square_c),
                ]
            ]
        )
        VGroup(objects, texts).scale_to_fit_height(3.65).move_to(UP * 0.15)
        self.play(Create(triangle), run_time=0.7)
        self.play(
            LaggedStart(*[Create(square) for square in [square_a, square_b, square_c]], lag_ratio=0.3),
            run_time=2,
        )
        self.play(FadeIn(texts), run_time=0.6)
        self.equation(spec, -2.1)
