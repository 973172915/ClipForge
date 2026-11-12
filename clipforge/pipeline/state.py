"""管线共享状态定义。"""
from typing import Any, TypedDict


class Scene(TypedDict):
    """单个分镜。"""
    narration: str      # 该镜头的解说词
    keyword: str        # 用于检索素材的关键词（英文）
    duration_hint: float  # 预估时长（秒）


class PipelineState(TypedDict, total=False):
    """端到端管线状态，各节点读写同一份。"""

    # 输入
    topic: str
    style: str                 # 科普 / 产品 / 情感 ...
    target_duration: int       # 目标时长（秒）

    # 中间产物
    title: str
    scenes: list[Scene]
    audio_path: str
    subtitle_segments: list[dict]   # [{start, end, text}]
    material_paths: list[str]       # 下载的素材视频/图片路径
    cover_path: str

    # 输出
    video_path: str
    error: str

    # 内部：可观测性追踪器（不参与业务逻辑）
    _trace: Any
    _job_id: str
