"""视频合成：素材 + 配音 + 字幕 → 成片。

兼容 MoviePy 2.x（新版已移除 moviepy.editor 子模块）。
"""
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
)

from clipforge.config import settings


def _wrap_text(text: str, max_chars: int = 16) -> str:
    """简单按字数折行，适配竖屏宽度。"""
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return "\n".join(lines)


def compose(
    audio_path: str,
    material_paths: list[str],
    subtitle_segments: list[dict],
    out_path: str | Path,
) -> str:
    """把素材循环拼接覆盖音频时长，烧录字幕。"""
    audio = AudioFileClip(audio_path)
    total_dur = audio.duration
    w, h = settings.video_width, settings.video_height

    # 按顺序铺素材，不够就循环
    clips = []
    idx = 0
    cursor = 0.0
    while cursor < total_dur:
        src = material_paths[idx % len(material_paths)] if material_paths else None
        if src and Path(src).exists():
            clip = VideoFileClip(src).without_audio()
        else:
            clip = ColorClip(size=(w, h), color=(20, 20, 30)).with_duration(total_dur)

        clip = clip.resized(height=h)
        new_w = clip.w
        if new_w > w:
            clip = clip.cropped(x1=(new_w - w) // 2, y1=0, width=w, height=h)
        elif new_w < w:
            clip = CompositeVideoClip([clip.with_position("center")], size=(w, h))

        remaining = total_dur - cursor
        seg_dur = min(clip.duration or total_dur, remaining, 6.0)
        clip = clip.with_duration(seg_dur).with_start(cursor)
        clips.append(clip)
        cursor += seg_dur
        idx += 1

    base = CompositeVideoClip(clips, size=(w, h)).with_duration(total_dur)

    # 叠加字幕
    txt_clips = []
    for seg in subtitle_segments:
        tc = (
            TextClip(
                text=_wrap_text(seg["text"]),
                font="C:/Windows/Fonts/msyhbd.ttc",
                font_size=56,
                text_color="white",
                stroke_color="black",
                stroke_width=1.5,
                size=(int(w * 0.9), None),
                method="caption",
            )
            .with_position(("center", int(h * 0.75)))
            .with_start(seg["start"])
            .with_duration(max(seg["end"] - seg["start"], 0.3))
        )
        txt_clips.append(tc)

    final = CompositeVideoClip([base, *txt_clips], size=(w, h)).with_audio(audio)
    out_path = Path(out_path)
    final.write_videofile(
        str(out_path),
        fps=settings.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        logger=None,
    )
    return str(out_path)
