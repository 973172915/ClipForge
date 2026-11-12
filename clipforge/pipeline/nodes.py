"""各节点实现：每个函数接收并返回 PipelineState。

可观测性通过 _trace（PipelineTrace 实例）注入到 state 中，
节点内部用它记录耗时、token 消耗等指标。
"""
import uuid
from pathlib import Path

from clipforge.config import settings
from clipforge.modules import material, tts
from clipforge.modules.compose import compose
from clipforge.modules.cover import make_cover
from clipforge.modules.script_gen import generate_script
from clipforge.pipeline.observability import PipelineTrace
from clipforge.pipeline.state import PipelineState


def _work_dir(state: PipelineState) -> Path:
    job_id = state.get("_job_id") or uuid.uuid4().hex[:8]
    state["_job_id"] = job_id
    d = settings.output_dir / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def node_generate_script(state: PipelineState) -> PipelineState:
    trace: PipelineTrace = state["_trace"]
    with trace.step("generate_script") as step:
        script, usage = generate_script(
            state["topic"],
            state.get("style", "科普"),
            state.get("target_duration", 30),
        )
        trace.add_tokens(usage["total_tokens"])
        step.finish_ok({"attempts": usage["attempts"], "tokens": usage["total_tokens"]})
    return {
        "title": script.title,
        "scenes": [s.dict() for s in script.scenes],
    }


def node_synth_audio(state: PipelineState) -> PipelineState:
    trace: PipelineTrace = state["_trace"]
    work_dir = _work_dir(state)
    with trace.step("synth_audio") as step:
        full_text = "".join(s["narration"] for s in state["scenes"])
        engine = tts.get_tts_engine()
        audio_path, segments = engine.synthesize_with_timestamps(
            full_text, work_dir / "voice"
        )
        step.finish_ok({
            "backend": engine.__class__.__name__,
            "chars": len(full_text),
            "words": len(segments),
        })
    return {"audio_path": audio_path, "subtitle_segments": segments}


def node_fetch_materials(state: PipelineState) -> PipelineState:
    trace: PipelineTrace = state["_trace"]
    work_dir = _work_dir(state)
    mat_dir = work_dir / "materials"
    paths: list[str] = []
    failed: list[str] = []
    with trace.step("fetch_materials") as step:
        for i, scene in enumerate(state["scenes"]):
            p = material.fetch_material(scene["keyword"], mat_dir, i)
            if p:
                paths.append(p)
            else:
                failed.append(scene["keyword"])
        step.finish_ok({
            "downloaded": len(paths),
            "failed_keywords": failed,
        })
    return {"material_paths": paths}


def node_compose_video(state: PipelineState) -> PipelineState:
    trace: PipelineTrace = state["_trace"]
    work_dir = _work_dir(state)
    with trace.step("compose_video") as step:
        out = compose(
            audio_path=state["audio_path"],
            material_paths=state["material_paths"],
            subtitle_segments=state["subtitle_segments"],
            out_path=work_dir / "final.mp4",
        )
        size_mb = Path(out).stat().st_size / 1024 / 1024
        step.finish_ok({"size_mb": round(size_mb, 2)})
    return {"video_path": out}


def node_make_cover(state: PipelineState) -> PipelineState:
    trace: PipelineTrace = state["_trace"]
    work_dir = _work_dir(state)
    with trace.step("make_cover") as step:
        cover = make_cover(state["title"], work_dir / "cover.jpg")
    return {"cover_path": cover}
