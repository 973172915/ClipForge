"""Piper TTS 后端：本地推理，CPU 友好（树莓派也能跑）。

依赖：
    pip install piper-tts faster-whisper

模型下载（一次性）：
    # 从 https://huggingface.co/rhasspy/piper-voices 下载
    # 中文推荐: zh_CN-huayan-medium.onnx + .onnx.json
    # 放到 settings.assets_dir / "piper_models/" 下

时间戳说明：
    Piper 不返回字级时间戳，这里用 faster-whisper 反向对齐补上。
"""
import subprocess
from pathlib import Path

from clipforge.config import settings
from clipforge.modules.tts_base import TTSEngine


class PiperTTSEngine(TTSEngine):
    def __init__(
        self,
        model_path: str | Path | None = None,
        whisper_model_size: str = "base",
    ):
        self.model_path = Path(model_path) if model_path else (
            settings.assets_dir / "piper_models" / "zh_CN-huayan-medium.onnx"
        )
        self.whisper_model_size = whisper_model_size
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Piper 模型未找到：{self.model_path}\n"
                f"请从 https://huggingface.co/rhasspy/piper-voices 下载 "
                f"zh_CN-huayan-medium.onnx 和对应的 .onnx.json 文件。"
            )

    def _synth_audio(self, text: str, out_path: Path) -> None:
        """调用 piper 命令行合成音频。"""
        cmd = [
            "piper",
            "--model", str(self.model_path),
            "--output_file", str(out_path),
        ]
        proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Piper 合成失败：{proc.stderr.decode(errors='ignore')}")

    def _align_timestamps(self, audio_path: Path) -> list[dict]:
        """用 faster-whisper 反向对齐拿字级时间戳。"""
        from faster_whisper import WhisperModel

        model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(
            str(audio_path), language="zh", word_timestamps=True
        )
        words: list[dict] = []
        for seg in segments:
            for w in seg.words:
                words.append({
                    "start": float(w.start),
                    "end": float(w.end),
                    "text": w.word.strip() or w.word,
                })
        return words

    def synthesize_with_timestamps(
        self, text: str, out_path: str | Path
    ) -> tuple[str, list[dict]]:
        out_path = Path(out_path).with_suffix(".wav")  # Piper 输出 wav
        self._synth_audio(text, out_path)
        segments = self._align_timestamps(out_path)
        return str(out_path), segments
