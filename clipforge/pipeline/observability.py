"""可观测性工具：步骤耗时、Token 成本、结构化日志。

设计原则：
- 零侵入：节点函数签名不变，通过装饰器注入
- 双通道：本地 JSON trace 文件 + 可选 LangSmith 云端追踪
"""
import json
import logging
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from clipforge.config import settings

logger = logging.getLogger("clipforge")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class StepTrace:
    """记录单个节点的执行指标。"""

    def __init__(self, name: str):
        self.name = name
        self.started_at: float | None = None
        self.duration_ms: int | None = None
        self.status: str = "pending"
        self.error: str | None = None
        self.meta: dict[str, Any] = {}

    def start(self) -> None:
        self.started_at = time.perf_counter()
        self.status = "running"
        logger.info(f"[{self.name}] 开始")

    def finish_ok(self, meta: dict[str, Any] | None = None) -> None:
        self._close("success", meta)

    def finish_err(self, err: str) -> None:
        self.meta["error"] = err
        self._close("failed", None)

    def _close(self, status: str, meta: dict[str, Any] | None) -> None:
        assert self.started_at is not None
        self.duration_ms = int((time.perf_counter() - self.started_at) * 1000)
        self.status = status
        if meta:
            self.meta.update(meta)
        icon = "OK " if status == "success" else "ERR"
        logger.info(f"[{self.name}] {icon} 耗时={self.duration_ms}ms {self.meta}")


class PipelineTrace:
    """一次完整管线的追踪容器。"""

    def __init__(self, job_id: str | None = None, topic: str = ""):
        self.job_id = job_id or uuid.uuid4().hex[:8]
        self.topic = topic
        self.steps: list[StepTrace] = []
        self.total_tokens: int = 0
        self.started_at: float = time.time()

    @contextmanager
    def step(self, name: str):
        tr = StepTrace(name)
        self.steps.append(tr)
        tr.start()
        try:
            yield tr
            if tr.status == "running":
                tr.finish_ok()
        except Exception as e:
            tr.finish_err(str(e))
            raise

    def add_tokens(self, n: int) -> None:
        self.total_tokens += n

    def summary(self) -> dict[str, Any]:
        total_ms = sum(s.duration_ms or 0 for s in self.steps)
        return {
            "job_id": self.job_id,
            "topic": self.topic,
            "total_ms": total_ms,
            "total_tokens": self.total_tokens,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "meta": s.meta,
                }
                for s in self.steps
            ],
        }

    def save(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "trace.json"
        path.write_text(json.dumps(self.summary(), ensure_ascii=False, indent=2))
        return path


# ---- LangSmith（可选） ----

def setup_langsmith() -> bool:
    """如果配置了 LANGSMITH_API_KEY 就启用，返回是否启用成功。"""
    api_key = getattr(settings, "langsmith_api_key", "")
    if not api_key:
        logger.info("LangSmith 未配置，跳过云端追踪")
        return False
    import os
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", api_key)
    project = getattr(settings, "langsmith_project", "clipforge")
    os.environ.setdefault("LANGCHAIN_PROJECT", project)
    logger.info(f"LangSmith 已启用，项目={project}")
    return True
