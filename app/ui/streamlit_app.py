"""Streamlit Web UI。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import streamlit as st

from clipforge.pipeline.graph import export_mermaid, run_pipeline

st.set_page_config(page_title="ClipForge", page_icon="🎬", layout="wide")
st.title("🎬 ClipForge · 短视频自动生成")
st.caption("输入一个主题，自动产出带配音、字幕、素材画面的竖版短视频。")

tab_gen, tab_arch = st.tabs(["🚀 生成", "📐 架构图"])

with tab_gen:
    with st.sidebar:
        st.header("参数")
        style = st.selectbox("风格", ["科普", "产品介绍", "情感共鸣", "新闻资讯"], index=0)
        duration = st.slider("目标时长（秒）", 15, 90, 30, step=5)

    topic = st.text_input("视频主题", value="为什么年轻人开始反向旅游")
    go = st.button("🚀 开始生成", type="primary", use_container_width=True)

    if go:
        if not topic.strip():
            st.warning("请输入主题")
            st.stop()

        status = st.status("生成中...", expanded=True)
        with status:
            st.write("① 解析主题...")
            try:
                result = run_pipeline(topic.strip(), style, duration)
            except Exception as e:
                status.update(label="失败", state="error")
                st.error(f"生成失败：{e}")
                st.stop()
            status.update(label="完成！", state="complete", expanded=False)

        st.success(f"标题：{result['title']}（{result['scene_count']} 个分镜）")

        # 视频与下载
        col1, col2 = st.columns([2, 1])
        with col1:
            if result.get("video_path") and Path(result["video_path"]).exists():
                st.video(result["video_path"])
                with open(result["video_path"], "rb") as f:
                    st.download_button("⬇️ 下载视频", f, file_name="clipforge.mp4")
            else:
                st.error("未找到视频文件")
        with col2:
            if result.get("cover_path") and Path(result["cover_path"]).exists():
                st.image(result["cover_path"], caption="封面")

        # 可观测性面板
        st.subheader("📊 运行指标")
        m = result["metrics"]
        c1, c2, c3 = st.columns(3)
        c1.metric("总耗时", f"{m['total_ms']/1000:.1f}s")
        c2.metric("Token 消耗", f"{m['total_tokens']:,}")
        c3.metric("步骤数", len(m["steps"]))

        with st.expander("🔍 各步骤详情"):
            for s in m["steps"]:
                icon = "✅" if s["status"] == "success" else "❌"
                st.markdown(
                    f"{icon} **{s['name']}** — {s['duration_ms']}ms "
                    f"`{json.dumps(s['meta'], ensure_ascii=False)}`"
                )

        with st.expander("📄 原始 trace.json"):
            st.json(m)

with tab_arch:
    st.subheader("LangGraph 工作流")
    st.caption("粘贴到 https://mermaid.live 预览")
    st.code(export_mermaid(), language="mermaid")
