"""TTS 抽象基类：统一不同后端的接口。"""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSEngine(ABC):
    """所有 TTS 后端实现此接口。

    返回的字级时间戳用于字幕对齐：
        [{"start": 0.12, "end": 0.35, "text": "你"}, ...]
    """

    @abstractmethod
    def synthesize_with_timestamps(
        self, text: str, out_path: str | Path
    ) -> tuple[str, list[dict]]:
        """合成语音并返回 (音频路径, 字级时间戳列表)。"""
        raise NotImplementedError
