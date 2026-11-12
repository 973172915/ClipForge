"""素材获取：从 Pexels 检索并下载竖版视频片段。"""
from pathlib import Path

import requests

from clipforge.config import settings

PEXELS_SEARCH = "https://api.pexels.com/videos/search"


def search_video(keyword: str, per_page: int = 5) -> list[dict]:
    """返回候选视频列表（按清晰度降序）。"""
    resp = requests.get(
        PEXELS_SEARCH,
        headers={"Authorization": settings.pexels_api_key},
        params={"query": keyword, "per_page": per_page, "orientation": "portrait"},
        timeout=15,
    )
    resp.raise_for_status()
    results = []
    for item in resp.json().get("videos", []):
        # 选一个接近竖屏的文件
        files = sorted(item["video_files"], key=lambda f: f.get("height", 0), reverse=True)
        if files:
            results.append({"url": files[0]["link"], "duration": item.get("duration", 0)})
    return results


def download(url: str, out_path: str | Path) -> str:
    out_path = Path(out_path)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return str(out_path)


def fetch_material(keyword: str, out_dir: Path, idx: int) -> str | None:
    """检索并下载第一个可用素材，失败返回 None（由上层降级处理）。"""
    try:
        candidates = search_video(keyword)
        if not candidates:
            return None
        out_dir.mkdir(parents=True, exist_ok=True)
        return download(candidates[0]["url"], out_dir / f"material_{idx}.mp4")
    except Exception:
        return None
