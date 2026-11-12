"""脚本生成：调用 LLM 产出结构化分镜。"""
import json
from typing import List

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from clipforge.config import settings


class SceneModel(BaseModel):
    narration: str = Field(..., description="该镜头的解说词，口语化中文")
    keyword: str = Field(..., description="用于检索素材的英文关键词")
    duration_hint: float = Field(3.0, gt=0, le=15)


class ScriptModel(BaseModel):
    title: str
    scenes: List[SceneModel]


SYSTEM_PROMPT = """你是一名短视频编导。根据用户给出的主题和风格，产出一个竖版短视频的分镜脚本。
要求：
1. 开头 3 秒必须有强 hook，抓住注意力。
2. 每个镜头解说词控制在 15-40 字，口语化、有节奏感。
3. keyword 用英文单词或短语，便于在图库检索画面素材。
4. 总时长接近目标时长，每个镜头 duration_hint 单位为秒。
只输出 JSON，不要 markdown 代码块，格式如下：
{{"title": "...", "scenes": [{{"narration": "...", "keyword": "...", "duration_hint": 4.0}}]}}
"""


def generate_script(
    topic: str,
    style: str,
    target_duration: int,
    on_usage=None,
) -> tuple[ScriptModel, dict]:
    """生成脚本。

    返回 (脚本对象, usage 字典)。on_usage 回调会在每次调用后收到 usage。
    """
    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    user_prompt = f"主题：{topic}\n风格：{style}\n目标时长：{target_duration} 秒"

    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "attempts": 0}
    last_err = None
    for attempt in range(3):
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt + (f"\n（上次解析失败：{last_err}，请严格输出合法 JSON）" if last_err else "")},
            ],
            temperature=0.8,
        )
        if resp.usage:
            total_usage["prompt_tokens"] += resp.usage.prompt_tokens
            total_usage["completion_tokens"] += resp.usage.completion_tokens
            total_usage["total_tokens"] += resp.usage.total_tokens
        total_usage["attempts"] = attempt + 1
        if on_usage:
            on_usage(resp.usage)
        raw = resp.choices[0].message.content.strip()
        # 去掉可能的 ```json 包裹
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        try:
            return ScriptModel.model_validate_json(raw), total_usage
        except (ValidationError, json.JSONDecodeError) as e:
            last_err = str(e)[:200]
            continue

    raise ValueError(f"脚本生成失败，多次解析均不通过：{last_err}")
