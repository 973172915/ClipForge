"""FastAPI 接口。"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from clipforge.pipeline.graph import run_pipeline

app = FastAPI(title="ClipForge", description="短视频自动生成管线", version="0.1.0")


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    style: str = "科普"
    target_duration: int = Field(30, ge=10, le=120)


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        result = run_pipeline(req.topic, req.style, req.target_duration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # 剥离 metrics 里的冗余字段，保持响应精简
    return JSONResponse({
        "job_id": result["job_id"],
        "title": result["title"],
        "video_path": result["video_path"],
        "cover_path": result["cover_path"],
        "scene_count": result["scene_count"],
        "metrics": result["metrics"],
    })


@app.get("/api/graph/mermaid")
def graph_mermaid():
    from clipforge.pipeline.graph import export_mermaid
    return {"mermaid": export_mermaid()}


@app.get("/api/health")
def health():
    return {"status": "ok"}
