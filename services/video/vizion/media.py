import os
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

from vizion.planner import PipelineError
from vizion.settings import settings


class Cancelled(Exception):
    pass


def ffmpeg_executable():
    binary = shutil.which("ffmpeg")
    if binary:
        return binary
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run_command(command, directory: Path, cancelled=lambda: False, timeout=300, input_text=None, env=None):
    log_path = directory / "process.log"
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=directory,
            stdout=log,
            stderr=log,
            stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if input_text is not None:
            try:
                process.stdin.write(input_text.encode("utf-8"))
                process.stdin.close()
            except BrokenPipeError:
                pass
        started = time.monotonic()
        try:
            while process.poll() is None:
                if cancelled():
                    raise Cancelled()
                if time.monotonic() - started > timeout:
                    raise PipelineError("A media operation exceeded its time limit. Try a shorter lesson.")
                time.sleep(0.25)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        if process.returncode:
            # Logs stay server-side; never expose filesystem paths, credentials, or raw provider responses.
            import logging

            logging.getLogger(__name__).error(
                "Media operation failed: %s", log_path.read_text(encoding="utf-8", errors="replace")[-3000:]
            )
            raise PipelineError(
                "The renderer could not complete this scene. Your storyboard is saved for revision."
            )


def narration(text: str, destination: Path, cancelled=lambda: False):
    directory = destination.parent
    provider = settings.tts_provider
    if provider == "piper" or (provider == "auto" and Path(settings.piper_model).exists()):
        run_command(
            [
                sys.executable,
                "-m",
                "piper",
                "-m",
                str(Path(settings.piper_model).resolve()),
                "-f",
                str(destination.resolve()),
            ],
            directory,
            cancelled,
            timeout=90,
            input_text=text,
        )
    elif os.name == "nt" and provider in {"auto", "windows"}:
        # Windows' installed voice provides an offline local development path. Production uses Piper.
        script = directory / "speak.ps1"
        (directory / "narration.txt").write_text(text, encoding="utf-8")
        script.write_text(
            """Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = -1
$speaker.SetOutputToWaveFile((Join-Path $PSScriptRoot 'voice.wav'))
$speaker.Speak([System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'narration.txt')))
$speaker.Dispose()
""",
            encoding="utf-8",
        )
        run_command(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script.resolve())],
            directory,
            cancelled,
            timeout=90,
        )
        if destination.name != "voice.wav":
            (directory / "voice.wav").replace(destination)
    elif shutil.which("espeak-ng") and provider in {"auto", "espeak"}:
        run_command(
            ["espeak-ng", "-s", "150", "-v", "en-us", "-w", str(destination.resolve()), "--stdin"],
            directory,
            cancelled,
            timeout=90,
            input_text=text,
        )
    else:
        raise PipelineError("No local narration voice is installed. Configure PIPER_MODEL on the worker.")
    with wave.open(str(destination), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    if not 1 < duration < 55:
        raise PipelineError(
            "A scene's narration is outside the supported duration. Shorten its narration and retry."
        )
    return duration


def captions_for_scene(text: str, duration: float, offset: float):
    words = text.split()
    chunks = [" ".join(words[i : i + 9]) for i in range(0, len(words), 9)]
    total = sum(len(chunk) for chunk in chunks) or 1
    elapsed = 0
    cues = []
    for chunk in chunks:
        start = offset + elapsed
        elapsed += duration * len(chunk) / total
        cues.append((start, min(offset + duration, offset + elapsed), chunk))
    return cues


def write_vtt(cues, path: Path):
    def timestamp(seconds):
        millis = round(seconds * 1000)
        return f"{millis // 3600000:02}:{millis // 60000 % 60:02}:{millis // 1000 % 60:02}.{millis % 1000:03}"

    content = "WEBVTT\n\n" + "\n\n".join(
        f"{timestamp(start)} --> {timestamp(end)}\n{text.replace('-->', '→')}" for start, end, text in cues
    )
    path.write_text(content + "\n", encoding="utf-8")
