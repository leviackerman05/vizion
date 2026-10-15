import json
import os
import sys
from pathlib import Path

from vizion.media import captions_for_scene, ffmpeg_executable, narration, run_command, write_vtt
from vizion.planner import PipelineError
from vizion.schema import Storyboard
from vizion.settings import settings


def render_lesson(plan: Storyboard, directory: Path, notify=lambda *_: None, cancelled=lambda: False):
    directory.mkdir(parents=True, exist_ok=True)
    clips, captions, elapsed = [], [], 0
    renderer = Path(__file__).with_name("render_scene.py").resolve()
    ffmpeg = ffmpeg_executable()
    # No provider, database, or storage credentials are passed to the rendering subprocess.
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "HOME",
            "USERPROFILE",
            "LANG",
            "LC_ALL",
            "FONTCONFIG_PATH",
        }
    }
    environment["PYTHONIOENCODING"] = "utf-8"
    for index, scene in enumerate(plan.scenes):
        scene_dir = directory / f"scene-{index + 1:02}"
        scene_dir.mkdir(exist_ok=True)
        notify(
            5 + round(index / len(plan.scenes) * 85),
            f"Recording narration for scene {index + 1} of {len(plan.scenes)}",
            "narrating",
        )
        voice = scene_dir / "voice.wav"
        duration = narration(scene.narration, voice, cancelled)
        if elapsed + duration > 120:
            raise PipelineError(
                "This lesson exceeds two minutes of narration. Shorten the storyboard and retry."
            )
        payload_path = scene_dir / "scene.json"
        payload_path.write_text(
            json.dumps(
                {
                    "scene": scene.model_dump(),
                    "duration": duration,
                    "index": index + 1,
                    "total": len(plan.scenes),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        environment["VIZION_SCENE_PATH"] = str(payload_path.resolve())
        notify(
            10 + round(index / len(plan.scenes) * 85),
            f"Animating scene {index + 1} of {len(plan.scenes)}",
            "rendering",
        )
        width = round(settings.render_height * 16 / 9 / 2) * 2
        run_command(
            [
                sys.executable,
                "-m",
                "manim",
                "render",
                "--renderer=cairo",
                "--disable_caching",
                "-r",
                f"{width},{settings.render_height}",
                "--fps",
                str(settings.render_fps),
                "--media_dir",
                str((scene_dir / "media").resolve()),
                "--output_file",
                "scene.mp4",
                str(renderer),
                "LessonScene",
            ],
            scene_dir,
            cancelled,
            env=environment,
        )
        matches = list((scene_dir / "media" / "videos").rglob("scene.mp4"))
        if len(matches) != 1:
            raise PipelineError("The scene renderer did not produce its expected video file.")
        muxed = scene_dir / "narrated.mp4"
        run_command(
            [
                ffmpeg,
                "-y",
                "-i",
                str(matches[0].resolve()),
                "-i",
                str(voice.resolve()),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-af",
                "apad=pad_dur=1",
                "-t",
                str(duration),
                "-movflags",
                "+faststart",
                str(muxed.resolve()),
            ],
            scene_dir,
            cancelled,
        )
        clips.append(muxed)
        captions.extend(captions_for_scene(scene.narration, duration, elapsed))
        elapsed += duration
    notify(94, "Assembling the narrated lesson and captions", "assembling")
    concat_file = directory / "concat.txt"
    # Only server-generated numeric scene paths enter the concat file.
    concat_file.write_text(
        "\n".join(f"file 'scene-{i + 1:02}/narrated.mp4'" for i in range(len(clips))), encoding="utf-8"
    )
    output = directory / "lesson.mp4"
    run_command(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            str(concat_file.resolve()),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output.resolve()),
        ],
        directory,
        cancelled,
    )
    vtt = directory / "captions.vtt"
    write_vtt(captions, vtt)
    return output, vtt, round(elapsed, 2)
