"""封面生成：纯色渐变底 + 标题文字。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from clipforge.config import settings


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ["msyhbd.ttc", "msyh.ttc", "simhei.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_cover(title: str, out_path: str | Path) -> str:
    w, h = settings.video_width, settings.video_height
    img = Image.new("RGB", (w, h), (18, 24, 43))
    draw = ImageDraw.Draw(img)
    # 简单渐变
    for y in range(h):
        ratio = y / h
        color = (int(18 + 30 * ratio), int(24 + 20 * ratio), int(43 + 60 * ratio))
        draw.line([(0, y), (w, y)], fill=color)

    font = _load_font(96)
    # 居中折行
    max_chars = 10
    lines = [title[i:i + max_chars] for i in range(0, len(title), max_chars)]
    line_h = 120
    start_y = h // 2 - len(lines) * line_h // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) / 2, start_y + i * line_h), line, font=font, fill="white")

    out_path = Path(out_path)
    img.save(out_path, quality=90)
    return str(out_path)
