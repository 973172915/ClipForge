# ClipForge · 短视频自动生成管线

> 输入一个主题，自动产出带配音、字幕、素材画面的竖版短视频。
> 基于 **LangGraph + Edge-TTS + MoviePy + Pexels** 的端到端内容生产管线。

## ✨ 功能

- 📝 一句话生成结构化分镜脚本（LLM + Pydantic schema 校验）
- 🎙️ 自动配音并返回字级时间戳（Edge-TTS）
- 🖼️ 按镜头关键词自动检索免费素材（Pexels API）
- 🎬 自动合成竖版视频并烧录字幕（MoviePy + FFmpeg）
- 🖼️ 自动生成封面图
- 🔀 LangGraph 工作流编排，节点可插拔、可观测

## 🏗️ 架构

```
generate_script → synth_audio → fetch_materials → compose_video → make_cover
       LLM           Edge-TTS      Pexels API         MoviePy        Pillow
```

每个节点独立可测，失败可降级。详见 `clipforge/pipeline/graph.py`。

## 🚀 快速开始

```bash
# 1. 环境（Python 3.12）
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置
copy .env.example .env
# 编辑 .env 填入 LLM_API_KEY 和 PEXELS_API_KEY

# 3. 启动（API + UI）
python run.py
```

- Web UI：http://localhost:8501
- API 文档：http://localhost:8000/docs

### Docker

```bash
docker compose up --build
```

## 📡 API

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "为什么年轻人开始反向旅游", "style": "科普", "target_duration": 30}'
```

返回：

```json
{
  "title": "...",
  "video_path": "output/xxxx/final.mp4",
  "cover_path": "output/xxxx/cover.jpg",
  "scene_count": 6
}
```

## 🧩 技术亮点

| 点 | 说明 |
|----|------|
| 结构化输出校验 | LLM 输出用 Pydantic 强校验，失败自动重试并反馈错误 |
| 字级时间戳 | 复用 Edge-TTS 的 WordBoundary 事件，字幕零误差对齐 |
| 工作流编排 | LangGraph 显式状态机，支持 trace 与可视化 |
| 全链路降级 | 素材下载失败自动切纯色底；LLM 解析失败自动重试 |
| 零成本运行 | TTS / 素材 / 编排全部免费，仅 LLM 调用按 token 计费 |

## 📁 目录结构

```
clipforge/
├── app/
│   ├── api/main.py          # FastAPI
│   └── ui/streamlit_app.py  # Streamlit UI
├── clipforge/
│   ├── config.py
│   ├── modules/             # 各能力模块
│   │   ├── script_gen.py
│   │   ├── tts.py
│   │   ├── material.py
│   │   ├── compose.py
│   │   └── cover.py
│   └── pipeline/            # LangGraph 编排
│       ├── graph.py
│       ├── nodes.py
│       └── state.py
├── output/                  # 生成的视频与中间产物
├── requirements.txt
├── Dockerfile
└── run.py                   # 一键启动
```

## ⚠️ 使用说明

- 请遵守目标平台的内容政策，AIGC 内容请按平台要求打标。
- Pexels 素材遵循其授权协议，可商用但不可再分发原始素材。
- 本项目仅供学习与个人创作使用。
