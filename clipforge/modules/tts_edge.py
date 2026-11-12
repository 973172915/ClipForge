"""Edge-TTS 后端：云端合成，自带字级时间戳。"""
import asyncio
from pathlib import Path

import edge_tts

from clipforge.config import settings
from clipforge.modules.tts_base import TTSEngine


class EdgeTTSEngine(TTSEngine):
    def __init__(self, voice: str | None = None):
        self.voice = voice or settings.tts_voice

    async def _synth(self, text: str, out_path: Path) -> list[dict]:
        communicate = edge_tts.Communicate(text, self.voice)
        segments: list[dict] = []
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    offset = chunk["offset"] / 1e7
                    duration = chunk["duration"] / 1e7
                    segments.append({
                        "start": offset,
                        "end": offset + duration,
                        "text": chunk["text"],
                    })
        return segments

    def synthesize_with_timestamps(
        self, text: str, out_path: str | Path
    ) -> tuple[str, list[dict]]:
        out_path = Path(out_path)
        segments = asyncio.run(self._synth(text, out_path))
        return str(out_path), segments
