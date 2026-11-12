"""TTS 工厂：根据配置返回对应后端。

在 .env 里设置 TTS_BACKEND=edge 或 piper 即可切换。
"""
from clipforge.config import settings
from clipforge.modules.tts_base import TTSEngine


def get_tts_engine() -> TTSEngine:
    backend = getattr(settings, "tts_backend", "edge").lower()
    if backend == "piper":
        from clipforge.modules.tts_piper import PiperTTSEngine
        return PiperTTSEngine(
            model_path=getattr(settings, "piper_model_path", None),
            whisper_model_size=getattr(settings, "piper_whisper_size", "base"),
        )
    if backend == "edge":
        from clipforge.modules.tts_edge import EdgeTTSEngine
        return EdgeTTSEngine(voice=settings.tts_voice)
    raise ValueError(f"未知的 TTS 后端：{backend}（支持 edge / piper）")


# 兼容旧接口：直接函数调用
def synthesize_with_timestamps(text: str, out_path):
    return get_tts_engine().synthesize_with_timestamps(text, out_path)
