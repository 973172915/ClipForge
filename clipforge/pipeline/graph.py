"""LangGraph 主编排：脚本 → 配音 → 素材 → 合成 → 封面。

每次运行会生成 trace.json，包含每步耗时、token 消耗等指标。
"""
from langgraph.graph import END, StateGraph

from clipforge.config import settings
from clipforge.pipeline.nodes import (
    node_compose_video,
    node_fetch_materials,
    node_generate_script,
    node_make_cover,
    node_synth_audio,
)
from clipforge.pipeline.observability import PipelineTrace, setup_langsmith
from clipforge.pipeline.state import PipelineState


def build_graph():
    g = StateGraph(PipelineState)

    g.add_node("generate_script", node_generate_script)
    g.add_node("synth_audio", node_synth_audio)
    g.add_node("fetch_materials", node_fetch_materials)
    g.add_node("compose_video", node_compose_video)
    g.add_node("make_cover", node_make_cover)

    g.set_entry_point("generate_script")
    g.add_edge("generate_script", "synth_audio")
    g.add_edge("synth_audio", "fetch_materials")
    g.add_edge("fetch_materials", "compose_video")
    g.add_edge("compose_video", "make_cover")
    g.add_edge("make_cover", END)

    return g.compile()


app = build_graph()
_langsmith_ready = False


def run_pipeline(topic: str, style: str = "科普", target_duration: int = 30) -> dict:
    """对外入口，返回最终产物路径 + 可观测性摘要。"""
    global _langsmith_ready
    if not _langsmith_ready:
        setup_langsmith()
        _langsmith_ready = True

    trace = PipelineTrace(topic=topic)
    init_state: PipelineState = {
        "topic": topic,
        "style": style,
        "target_duration": target_duration,
        "_trace": trace,
    }
    result = None
    try:
        result = app.invoke(init_state)
    finally:
        trace_path = trace.save(settings.output_dir / trace.job_id)

    return {
        "job_id": trace.job_id,
        "title": result.get("title") if result else None,
        "video_path": result.get("video_path") if result else None,
        "cover_path": result.get("cover_path") if result else None,
        "scene_count": len(result.get("scenes", [])) if result else 0,
        "metrics": trace.summary(),
        "trace_path": str(trace_path),
    }


def export_mermaid() -> str:
    """导出 Mermaid 流程图代码，可粘贴到 https://mermaid.live 预览。"""
    return app.get_graph().draw_mermaid()
