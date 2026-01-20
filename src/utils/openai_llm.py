from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

from utils.logger import logger
from utils.env_loader import load_env


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str | None
    base_url: str
    model: str
    max_input_chars: int
    max_output_tokens: int


def get_openai_settings() -> OpenAISettings:
    load_env()
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
    max_input_chars = int(os.environ.get("OPENAI_MAX_INPUT_CHARS") or "30000")
    max_output_tokens = int(os.environ.get("OPENAI_MAX_OUTPUT_TOKENS") or "600")
    return OpenAISettings(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        model=model,
        max_input_chars=max_input_chars,
        max_output_tokens=max_output_tokens,
    )


def chat_completions(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    timeout_s: int = 30,
) -> str:
    settings = get_openai_settings()
    if not settings.api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY")

    url = f"{settings.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model or settings.model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": settings.max_output_tokens,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    if resp.status_code in {401, 403}:
        raise RuntimeError(f"OpenAI 鉴权失败: status={resp.status_code}")
    if resp.status_code == 429:
        raise RuntimeError("OpenAI 触发限流(429)")
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("OpenAI 返回为空 choices")
    content = (choices[0].get("message") or {}).get("content") or ""
    content = str(content).strip()
    if not content:
        raise RuntimeError("OpenAI 返回内容为空")
    return content


def heuristic_summarize_markdown(markdown_text: str, max_chars: int = 1600) -> str:
    text = (markdown_text or "").strip()
    if not text:
        return "未找到 README 内容。"
    lines = [ln.rstrip() for ln in text.splitlines()]
    def is_noise(ln: str) -> bool:
        s = ln.strip()
        if not s:
            return True
        low = s.lower()
        if low.startswith("<"):
            return True
        if "![[" in low:
            return True
        if low.startswith("[![") or "badge" in low or "shields.io" in low:
            return True
        if "actions/workflows" in low:
            return True
        return False

    picked: list[str] = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("#") and not is_noise(s):
            picked.append(s)
        if len(picked) >= 8:
            break
    body = ""
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if is_noise(s):
            continue
        if s.startswith("#"):
            continue
        if len(s) < 12:
            continue
        body = s
        break
    summary = []
    if picked:
        summary.append("## 摘要（简化）")
        summary.extend(picked[:6])
    if body:
        summary.append("")
        summary.append(body[: max_chars // 2])
    return "\n".join(summary).strip() + "\n"


def summarize_readme_markdown(readme_md: str, repo_full_name: str) -> tuple[str, str]:
    settings = get_openai_settings()
    truncated = (readme_md or "")[: settings.max_input_chars]
    if not truncated.strip():
        return "未找到 README 内容。\n", "missing"
    if not settings.api_key:
        logger.info("OPENAI_API_KEY 未设置，使用启发式总结")
        return heuristic_summarize_markdown(truncated), "heuristic"

    system = (
        "你是资深开源项目分析助手。请用中文总结仓库 README，输出 Markdown。"
        "要求：简洁、结构化、信息密度高；不要复述徽章图片；不要输出超长代码块。"
    )
    user = (
        f"仓库：{repo_full_name}\n\n"
        "请输出以下结构（可为空则省略）：\n"
        "1) 一句话介绍\n"
        "2) 适用场景/主要功能（3-8 条要点）\n"
        "3) 快速开始（仅 3-6 行，含关键命令/入口，不要贴大段）\n"
        "4) 关键概念/组件（如有）\n"
        "README 原文：\n"
        f"{truncated}"
    )
    try:
        content = chat_completions(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        return content.strip() + "\n", "openai"
    except Exception as e:
        logger.warning(f"OpenAI 总结失败，回退启发式：{repo_full_name} ({e})")
        return heuristic_summarize_markdown(truncated), "heuristic"
