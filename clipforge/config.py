"""全局配置：所有密钥走环境变量，不硬编码。"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM（OpenAI 兼容接口）
    llm_base_url: str = "https://tokenhub.tencentmaas.com/v1"
    llm_api_key: str = ""
    llm_model: str = "ep-1v02bui1"

    # Pexels 素材库
    pexels_api_key: str = ""

    # TTS：edge（云端，免费）或 piper（本地，树莓派也能跑）
    tts_backend: str = "edge"
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    piper_model_path: str | None = None      # Piper onnx 模型路径
    piper_whisper_size: str = "base"         # 反向对齐用的 Whisper 规格

    # 可观测性：LangSmith（可选）
    langsmith_api_key: str = ""
    langsmith_project: str = "clipforge"

    # 路径
    assets_dir: Path = BASE_DIR / "assets"
    output_dir: Path = BASE_DIR / "output"

    # 视频参数
    video_width: int = 1080
    video_height: int = 1920
    fps: int = 30


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
