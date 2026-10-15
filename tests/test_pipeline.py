import math
import time

import pytest
from pydantic import ValidationError
from test_projects import create
from vizion.db import Project, transaction
from vizion.examples import example_storyboard
from vizion.media import captions_for_scene, write_vtt
from vizion.schema import Storyboard, expression_function
from vizion.worker import claim_job, process_job, update_job


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').getcwd()",
        "x.__class__",
        "[x for x in range(100)]",
        "2**1000",
        "2**(2**8)",
        "open('secret')",
        "sin(x, 2)",
        "1e999",
    ],
)
def test_expressions_cannot_execute_code_or_unbounded_powers(expression):
    with pytest.raises(ValueError):
        expression_function(expression)


def test_valid_functions_and_storyboard_budgets():
    assert expression_function("sin(x) + x**2")(2) == pytest.approx(math.sin(2) + 4)
    plan = example_storyboard()
    assert 65 <= sum(len(scene.narration.split()) for scene in plan.scenes) <= 190
    raw = plan.model_dump()
    raw["scenes"][0]["narration"] = "Repeated content. " * 100
    with pytest.raises(ValidationError):
        Storyboard.model_validate(raw)


@pytest.mark.parametrize("expression, low, high", [("sqrt(x)", -2, 2), ("1/x", -2, 2), ("exp(1000)", 0, 1)])
def test_invalid_graph_domains_fail_before_rendering(expression, low, high):
    raw = example_storyboard().model_dump()
    graph = next(scene for scene in raw["scenes"] if scene["kind"] == "graph")
    graph.update(expression=expression, x_min=low, x_max=high)
    with pytest.raises(ValidationError, match="graph domain"):
        Storyboard.model_validate(raw)


def test_expired_job_leases_recover_and_old_workers_are_fenced(logged_in):
    project = create(logged_in)
    first = claim_job()
    assert first.id == project["id"] and first.status == "planning"
    assert claim_job() is None
    with transaction() as db:
        db.get(Project, first.id).lease_until = time.time() - 5
    second = claim_job()
    assert second.lease_owner != first.lease_owner and second.attempts == 2
    assert not update_job(first, progress=90)
    assert update_job(second, progress=30)


def test_example_plan_runs_through_the_real_worker_and_remains_editable(logged_in):
    project = create(logged_in)
    process_job(claim_job())
    stored = logged_in.get(f"/api/projects/{project['id']}").json()
    assert stored["status"] == "draft"
    assert stored["storyboard"]["title"] == "Why a parabola curves"
    assert "example" in stored["provider"]


def test_cancel_fences_the_active_worker(logged_in):
    project = create(logged_in)
    claimed = claim_job()
    logged_in.post(f"/api/projects/{project['id']}/cancel")
    assert not update_job(claimed, status="completed")


def test_captions_follow_the_measured_audio_clock(tmp_path):
    cues = captions_for_scene(" ".join(["word"] * 32), 14.5, 2)
    assert cues[0][0] == 2
    assert cues[-1][1] == pytest.approx(16.5)
    assert all(cues[i][1] == cues[i + 1][0] for i in range(len(cues) - 1))
    path = tmp_path / "captions.vtt"
    write_vtt(cues, path)
    assert path.read_text().startswith("WEBVTT\n\n00:00:02.000")
