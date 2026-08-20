"""Deterministic Advanced SubStation Alpha caption generation."""

from dataclasses import dataclass
from pathlib import Path

from shorts_automation.domain.models import StructuredDraft


@dataclass(frozen=True)
class CaptionStyle:
    """Rendering-safe caption dimensions and typography."""

    canvas_width: int
    canvas_height: int
    safe_margin_pixels: int
    font_name: str


def _ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def _escape_caption(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    words = escaped.replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > 28:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return r"\N".join(lines)


def build_ass(draft: StructuredDraft, style: CaptionStyle) -> str:
    """Build a complete ASS document with one timed event per draft scene."""
    font_size = max(36, round(style.canvas_height * 0.052))
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {style.canvas_width}
PlayResY: {style.canvas_height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, \
Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, \
Alignment, MarginL, MarginR, MarginV, Encoding
Style: Mobile,{style.font_name},{font_size},&H00FFFFFF,&H000000FF,&H00101010,&H80000000,\
-1,0,0,0,100,100,0,0,1,4,1,2,{style.safe_margin_pixels},{style.safe_margin_pixels},\
{style.safe_margin_pixels},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    elapsed = 0.0
    events: list[str] = []
    for scene in draft.scenes:
        end = elapsed + scene.duration_seconds
        events.append(
            f"Dialogue: 0,{_ass_time(elapsed)},{_ass_time(end)},Mobile,,0,0,0,,"
            f"{_escape_caption(scene.caption)}"
        )
        elapsed = end
    return header + "\n".join(events) + "\n"


def write_ass(draft: StructuredDraft, style: CaptionStyle, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ass(draft, style), encoding="utf-8")
    return output_path
