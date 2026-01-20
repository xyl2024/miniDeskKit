from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from utils.logger import logger


TRENDING_URL = "https://github.com/trending"
SCHEMA_VERSION = 5
VALID_SINCE_VALUES = {"daily", "weekly", "monthly"}


@dataclass(frozen=True)
class TrendingOptions:
    since: str = "daily"
    language: str | None = None


def normalize_since(since: str | None) -> str:
    s = (since or "").strip().lower()
    if s in VALID_SINCE_VALUES:
        return s
    return "daily"


def _today() -> date:
    return datetime.now().date()


def date_str(d: date | str | None = None) -> str:
    if d is None:
        d = _today()
    if isinstance(d, str):
        return d
    return d.strftime("%Y-%m-%d")


def cache_dir() -> Path:
    path = Path(".cache") / "github_trending"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_stem(d: date | str | None, options: TrendingOptions | None) -> str:
    ds = date_str(d)
    if options is None:
        return ds
    since = normalize_since(options.since)
    language = (options.language or "").strip()
    suffix_parts = [f"since-{since}"]
    if language:
        safe_lang = re.sub(r"[^a-zA-Z0-9._-]+", "_", language)
        suffix_parts.append(f"lang-{safe_lang}")
    return ds + "__" + "__".join(suffix_parts)


def daily_cache_paths(
    d: date | str | None = None, options: TrendingOptions | None = None
) -> tuple[Path, Path]:
    stem = _cache_stem(d, options)
    md_path = cache_dir() / f"{stem}.md"
    json_path = cache_dir() / f"{stem}.json"
    return md_path, json_path


def daily_readme_dir(d: date | str | None = None) -> Path:
    ds = date_str(d)
    path = cache_dir() / "readme" / ds
    path.mkdir(parents=True, exist_ok=True)
    return path


def daily_readme_summary_dir(d: date | str | None = None) -> Path:
    ds = date_str(d)
    path = cache_dir() / "readme_summary" / ds
    path.mkdir(parents=True, exist_ok=True)
    return path


def daily_readme_html_dir(d: date | str | None = None) -> Path:
    ds = date_str(d)
    path = cache_dir() / "readme_html" / ds
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_readme_path(full_name: str, d: date | str | None = None) -> Path:
    safe = (full_name or "unknown").strip().replace("/", "__")
    return daily_readme_dir(d) / f"{safe}.md"


def repo_readme_summary_path(full_name: str, d: date | str | None = None) -> Path:
    safe = (full_name or "unknown").strip().replace("/", "__")
    return daily_readme_summary_dir(d) / f"{safe}.md"


def repo_readme_html_path(full_name: str, d: date | str | None = None) -> Path:
    safe = (full_name or "unknown").strip().replace("/", "__")
    return daily_readme_html_dir(d) / f"{safe}.html"


def _load_cached_payload_from_path(json_path: Path) -> dict[str, Any] | None:
    if not json_path.exists():
        return None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception as e:
        logger.warning(f"Failed to load trending cache: {json_path} ({e})")
    return None


def load_cached_payload(
    d: date | str | None = None, options: TrendingOptions | None = None
) -> dict[str, Any] | None:
    _, json_path = daily_cache_paths(d, options)
    payload = _load_cached_payload_from_path(json_path)
    if payload is not None:
        return payload
    if options is not None:
        _, legacy_json_path = daily_cache_paths(d, None)
        return _load_cached_payload_from_path(legacy_json_path)
    return None


def has_success_cache(d: date | str | None = None, options: TrendingOptions | None = None) -> bool:
    md_path, json_path = daily_cache_paths(d, options)
    legacy_md_path, legacy_json_path = daily_cache_paths(d, None)
    if options is None:
        if not (md_path.exists() and json_path.exists()):
            return False
    else:
        if not (md_path.exists() and json_path.exists()):
            if not (legacy_md_path.exists() and legacy_json_path.exists()):
                return False
            md_path, json_path = legacy_md_path, legacy_json_path

    payload = _load_cached_payload_from_path(json_path)
    if not payload:
        return False
    version = payload.get("schema_version")
    if not isinstance(version, int) or version < SCHEMA_VERSION:
        return False
    if options is not None:
        cache_since = normalize_since(payload.get("since") if isinstance(payload, dict) else None)
        want_since = normalize_since(options.since)
        if cache_since != want_since:
            return False
        cache_language = payload.get("language")
        want_language = options.language
        if (cache_language or None) != (want_language or None):
            return False
    items = payload.get("items")
    return isinstance(items, list) and len(items) > 0


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    _atomic_write_text(path, text + "\n")


def load_cached_items(
    d: date | str | None = None, options: TrendingOptions | None = None
) -> list[dict[str, Any]] | None:
    payload = load_cached_payload(d, options)
    if not payload:
        return None
    version = payload.get("schema_version")
    if not isinstance(version, int) or version < SCHEMA_VERSION:
        logger.info(
            f"Trending 缓存版本过旧，忽略: date={payload.get('date')}, schema_version={version}"
        )
        return None
    if options is not None:
        cache_since = normalize_since(payload.get("since") if isinstance(payload, dict) else None)
        want_since = normalize_since(options.since)
        if cache_since != want_since:
            return None
        cache_language = payload.get("language")
        want_language = options.language
        if (cache_language or None) != (want_language or None):
            return None
    items = payload.get("items")
    if isinstance(items, list):
        return items
    return None


def summaries_complete(d: date | str | None = None, options: TrendingOptions | None = None) -> bool:
    payload = load_cached_payload(d, options)
    if not payload:
        return False
    v = payload.get("summaries_complete")
    if isinstance(v, bool):
        return v
    return True


def load_latest_cached_items() -> list[dict[str, Any]] | None:
    candidates = sorted(cache_dir().glob("*.json"), reverse=True)
    for json_path in candidates:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            version = payload.get("schema_version")
            if not isinstance(version, int) or version < SCHEMA_VERSION:
                continue
            items = payload.get("items")
            if isinstance(items, list) and items:
                return items
        except Exception:
            continue
    return None


def build_repo_markdown(item: dict[str, Any]) -> str:
    full_name = str(item.get("full_name") or "")
    url = str(item.get("url") or "")
    description = str(item.get("description") or "")
    language = str(item.get("language") or "")
    stars = item.get("stars")
    forks = item.get("forks")
    stars_today = item.get("stars_today")
    readme_md = item.get("readme_md")

    lines: list[str] = []
    if full_name:
        lines.append(f"# {full_name}")
    if url:
        lines.append(url)
        lines.append("")

    meta_parts: list[str] = []
    if language:
        meta_parts.append(f"Language: {language}")
    if isinstance(stars, int):
        meta_parts.append(f"Stars: {stars:,}")
    if isinstance(forks, int):
        meta_parts.append(f"Forks: {forks:,}")
    if isinstance(stars_today, int):
        meta_parts.append(f"Stars today: {stars_today:,}")
    if meta_parts:
        lines.append(" - " + "\n - ".join(meta_parts))
        lines.append("")

    if description:
        lines.append(description)
        lines.append("")

    lines.append("## README")
    lines.append("")
    if isinstance(readme_md, str) and readme_md.strip():
        lines.append(readme_md.strip())
        lines.append("")
    else:
        lines.append("_README 未获取到（可能是无 README / 触发了 GitHub API 限流 / 网络错误）_")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_daily_markdown(
    d: date | str | None,
    options: TrendingOptions,
    items: list[dict[str, Any]],
) -> str:
    ds = date_str(d)
    url = TRENDING_URL
    params: list[str] = []
    since = normalize_since(options.since)
    if since:
        params.append(f"since={since}")
    if options.language:
        params.append(f"language={options.language}")
    if params:
        url = url + "?" + "&".join(params)

    lines: list[str] = []
    lines.append(f"# GitHub Trending ({ds}, {since})")
    lines.append("")
    lines.append(f"Source: {url}")
    lines.append("")

    lines.append("| # | Repo | Language | Stars | Forks | Stars today |")
    lines.append("|---:|---|---|---:|---:|---:|")
    for item in items:
        rank = item.get("rank")
        full_name = str(item.get("full_name") or "")
        repo_url = str(item.get("url") or "")
        language = str(item.get("language") or "")
        stars = item.get("stars")
        forks = item.get("forks")
        stars_today = item.get("stars_today")

        repo_cell = full_name
        if repo_url and full_name:
            repo_cell = f"[{full_name}]({repo_url})"

        def fmt_int(v: Any) -> str:
            return f"{v:,}" if isinstance(v, int) else ""

        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank or ""),
                    repo_cell,
                    language,
                    fmt_int(stars),
                    fmt_int(forks),
                    fmt_int(stars_today),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    for item in items:
        lines.append(build_repo_markdown(item).rstrip())
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _parse_compact_number(text: str) -> int | None:
    s = (text or "").strip().lower().replace(",", "")
    if not s:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([km])?", s)
    if not m:
        digits = re.sub(r"[^\d]", "", s)
        return int(digits) if digits else None
    value = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        value *= 1000
    elif suffix == "m":
        value *= 1000000
    return int(round(value))


def _extract_repo_stats(article) -> tuple[int | None, int | None]:
    stars = None
    forks = None
    for a in article.select("a"):
        href = a.get("href") or ""
        text = a.get_text(strip=True)
        if not text:
            continue
        if href.endswith("/stargazers") and stars is None:
            stars = _parse_compact_number(text)
        elif href.endswith("/forks") and forks is None:
            forks = _parse_compact_number(text)
    return stars, forks


def parse_trending_html(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, Any]] = []
    for idx, article in enumerate(soup.select("article.Box-row"), start=1):
        a = article.select_one("h2 a")
        href = (a.get("href") if a else "") or ""
        full_name = href.strip("/").strip()
        if not full_name and a:
            full_name = a.get_text(" ", strip=True).replace(" / ", "/")

        url = f"https://github.com/{full_name}" if full_name else ""
        desc_el = article.select_one("p")
        description = desc_el.get_text(" ", strip=True) if desc_el else ""

        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        language = lang_el.get_text(strip=True) if lang_el else ""

        stars, forks = _extract_repo_stats(article)

        today_el = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = None
        if today_el:
            today_text = today_el.get_text(" ", strip=True)
            today_digits = re.sub(r"[^\d,\.kmKM]", "", today_text).strip()
            stars_today = _parse_compact_number(today_digits)

        item: dict[str, Any] = {
            "rank": idx,
            "full_name": full_name,
            "url": url,
            "language": language,
            "stars": stars,
            "forks": forks,
            "stars_today": stars_today,
            "description": description,
            "readme_md": None,
            "readme_html": None,
            "readme_source": "none",
        }
        item["readme"] = build_repo_markdown(item)
        items.append(item)
    return items


def _build_github_session() -> requests.Session:
    session = requests.Session()
    headers = {
        "User-Agent": "miniDeskKit/0.1",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    session.headers.update(headers)
    return session


def fetch_repo_readme_md(
    session: requests.Session,
    full_name: str,
    timeout_s: int = 12,
    max_chars: int = 1_000_000,
) -> str | None:
    if not full_name:
        return None
    api_url = f"https://api.github.com/repos/{full_name}/readme"
    resp = session.get(
        api_url,
        headers={"Accept": "application/vnd.github.v3.raw"},
        timeout=timeout_s,
    )
    if resp.status_code == 404:
        logger.info(f"README 不存在: {full_name}")
        return None
    if resp.status_code in {403, 429}:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            raise RuntimeError("GitHub API 限流，请稍后再试或设置 GITHUB_TOKEN")
        logger.warning(
            f"README 获取被限制: {full_name}, status={resp.status_code}, remaining={remaining}"
        )
        return None
    resp.raise_for_status()
    text = resp.text or ""
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n---\n\n_README 过大，已截断显示_"
    return text


def render_markdown_to_html(
    session: requests.Session,
    markdown_text: str,
    context: str,
    timeout_s: int = 12,
    max_chars: int = 2_000_000,
) -> str | None:
    if not markdown_text.strip():
        return None
    api_url = "https://api.github.com/markdown"
    payload = {"text": markdown_text, "mode": "gfm", "context": context}
    resp = session.post(
        api_url,
        json=payload,
        headers={"Accept": "text/html"},
        timeout=timeout_s,
    )
    if resp.status_code in {403, 429}:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            raise RuntimeError("GitHub API 限流，请稍后再试或设置 GITHUB_TOKEN")
        logger.warning(
            f"README 渲染被限制: {context}, status={resp.status_code}, remaining={remaining}"
        )
        return None
    resp.raise_for_status()
    html = resp.text or ""
    if len(html) > max_chars:
        return html[:max_chars] + "<hr><p><em>README HTML 过大，已截断显示</em></p>"
    return html


def build_repo_html(item: dict[str, Any]) -> str:
    full_name = str(item.get("full_name") or "")
    url = str(item.get("url") or "")
    description = str(item.get("description") or "")
    language = str(item.get("language") or "")
    stars = item.get("stars")
    forks = item.get("forks")
    stars_today = item.get("stars_today")
    readme_html = item.get("readme_html")

    parts: list[str] = []
    if full_name:
        parts.append(f"<h2>{full_name}</h2>")
    if url:
        parts.append(f'<p><a href="{url}">{url}</a></p>')

    meta_parts: list[str] = []
    if language:
        meta_parts.append(f"Language: {language}")
    if isinstance(stars, int):
        meta_parts.append(f"Stars: {stars:,}")
    if isinstance(forks, int):
        meta_parts.append(f"Forks: {forks:,}")
    if isinstance(stars_today, int):
        meta_parts.append(f"Stars today: {stars_today:,}")
    if meta_parts:
        parts.append("<p>" + " &nbsp; | &nbsp; ".join(meta_parts) + "</p>")

    if description:
        parts.append(f"<p>{description}</p>")

    parts.append("<hr>")
    if isinstance(readme_html, str) and readme_html.strip():
        parts.append(readme_html)
    else:
        parts.append("<p><em>README 未获取到（可能无 README / 限流 / 网络错误）</em></p>")

    return "\n".join(parts)


def enrich_items_with_readme(items: list[dict[str, Any]], timeout_s: int = 12) -> None:
    raise RuntimeError("enrich_items_with_readme 已废弃，请使用 fetch_and_cache_daily 内的两阶段流程")


def fetch_trending(options: TrendingOptions, timeout_s: int = 12) -> list[dict[str, Any]]:
    params: dict[str, str] = {}
    since = normalize_since(options.since)
    if since:
        params["since"] = since
    if options.language:
        params["language"] = options.language

    logger.info(f"请求 Trending 页面: {TRENDING_URL} params={params}")
    headers = {
        "User-Agent": "miniDeskKit/0.1 (+https://github.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(
        TRENDING_URL,
        params=params,
        headers=headers,
        timeout=timeout_s,
    )
    resp.raise_for_status()
    logger.info(
        f"Trending 页面响应成功: status={resp.status_code}, bytes={len(resp.text or '')}"
    )
    items = parse_trending_html(resp.text)
    if not items:
        raise RuntimeError("Parsed trending items is empty")
    logger.info(f"Trending 列表解析完成: count={len(items)}")
    return items


def _all_summaries_done(items: list[dict[str, Any]]) -> bool:
    done_states = {"openai", "heuristic", "missing", "error"}
    for item in items:
        state = str(item.get("readme_source") or "none")
        if state not in done_states:
            return False
    return True


def fetch_all_raw_readmes(
    items: list[dict[str, Any]],
    d: date | str | None,
    timeout_s: int = 12,
) -> None:
    session = _build_github_session()
    logger.info(f"开始获取原始 README: count={len(items)}")
    for item in items:
        full_name = str(item.get("full_name") or "")
        if not full_name:
            item["readme_source"] = "missing"
            continue
        try:
            readme_raw_md = fetch_repo_readme_md(session, full_name, timeout_s=timeout_s)
        except Exception as e:
            logger.warning(f"Fetch README failed: {full_name} ({e})")
            item["readme_source"] = "error"
            continue
        if not readme_raw_md:
            item["readme_source"] = "missing"
            continue
        raw_path = repo_readme_path(full_name, d)
        _atomic_write_text(raw_path, readme_raw_md.strip() + "\n")
        item["readme_raw_path"] = str(raw_path)
        item["readme_source"] = "raw"


def summarize_all_readmes_from_raw(
    items: list[dict[str, Any]],
    d: date | str | None,
    options: TrendingOptions,
    timeout_s: int = 12,
    cache_json_path: Path | None = None,
    cache_payload: dict[str, Any] | None = None,
    persist_every: int = 5,
) -> None:
    from utils.openai_llm import summarize_readme_markdown

    session = _build_github_session()
    logger.info(f"开始总结 README: count={len(items)}")
    updated_count = 0
    for item in items:
        full_name = str(item.get("full_name") or "")
        state = str(item.get("readme_source") or "none")
        if state != "raw":
            continue
        raw_path = item.get("readme_raw_path")
        if not isinstance(raw_path, str) or not raw_path:
            item["readme_source"] = "missing"
            continue
        try:
            raw_text = Path(raw_path).read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"读取原始 README 失败: {full_name} ({e})")
            item["readme_source"] = "error"
            continue

        try:
            readme_md, summary_source = summarize_readme_markdown(raw_text or "", full_name)
            readme_html = (
                render_markdown_to_html(
                    session,
                    readme_md or "",
                    context=full_name,
                    timeout_s=timeout_s,
                )
                if readme_md
                else None
            )
        except Exception as e:
            logger.warning(f"总结 README 失败: {full_name} ({e})")
            item["readme_md"] = None
            item["readme_html"] = None
            item["readme_source"] = "error"
            continue

        item["readme_md"] = readme_md
        item["readme_source"] = summary_source
        item["readme_html"] = readme_html
        item["readme"] = build_repo_markdown(item)
        item["readme_html_page"] = build_repo_html(item)
        if isinstance(readme_md, str) and readme_md.strip() and full_name:
            _atomic_write_text(
                repo_readme_summary_path(full_name, d), readme_md.strip() + "\n"
            )
            item["readme_path"] = str(repo_readme_summary_path(full_name, d))
        html_page = item.get("readme_html_page")
        if isinstance(html_page, str) and html_page.strip() and full_name:
            _atomic_write_text(repo_readme_html_path(full_name, d), html_page.strip() + "\n")
            item["readme_html_path"] = str(repo_readme_html_path(full_name, d))
        logger.info(
            f"README 总结完成: {full_name}, source={item.get('readme_source')}, md={bool(readme_md)}, html={bool(readme_html)}"
        )
        updated_count += 1
        if (
            cache_json_path is not None
            and cache_payload is not None
            and persist_every > 0
            and updated_count % persist_every == 0
        ):
            cache_payload["items"] = items
            cache_payload["summaries_complete"] = _all_summaries_done(items)
            _atomic_write_json(cache_json_path, cache_payload)


def fetch_and_cache_daily(
    d: date | str | None = None,
    options: TrendingOptions | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    if options is None:
        options = TrendingOptions()
    options = TrendingOptions(since=normalize_since(options.since), language=options.language)
    if d is not None and date_str(d) != date_str():
        if has_success_cache(d, options):
            cached = load_cached_items(d, options)
            if cached is not None:
                logger.info(f"使用历史缓存: date={date_str(d)}, count={len(cached)}")
                return cached, False
        raise ValueError("GitHub Trending 不支持按历史日期在线爬取，仅支持读取已缓存数据")

    md_path, json_path = daily_cache_paths(d, options)
    if has_success_cache(d, options):
        cached = load_cached_items(d, options)
        if cached is not None:
            if summaries_complete(d, options):
                logger.info(
                    f"使用今日缓存: date={date_str(d)}, since={options.since}, count={len(cached)}"
                )
                return cached, False
            logger.info(
                f"今日缓存存在但总结未完成，继续总结: date={date_str(d)}, since={options.since}, count={len(cached)}"
            )
            payload = load_cached_payload(d, options) or {}
            summarize_all_readmes_from_raw(
                cached,
                d=d,
                options=options,
                cache_json_path=json_path,
                cache_payload=payload,
            )
            md_text = build_daily_markdown(d, options, cached)
            payload.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "date": date_str(d),
                    "since": options.since,
                    "language": options.language,
                    "summaries_complete": _all_summaries_done(cached),
                    "items": cached,
                }
            )
            _atomic_write_text(md_path, md_text)
            _atomic_write_json(json_path, payload)
            return cached, True

    logger.info(f"开始抓取 Trending 并写入缓存: date={date_str(d)}")
    items = fetch_trending(options)

    try:
        from utils.openai_llm import get_openai_settings

        settings = get_openai_settings()
        openai_enabled = bool(settings.api_key)
        openai_model = settings.model
    except Exception:
        openai_enabled = False
        openai_model = None

    fetch_all_raw_readmes(items, d=d)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "date": date_str(d),
        "since": options.since,
        "language": options.language,
        "openai_enabled": openai_enabled,
        "openai_model": openai_model,
        "summaries_complete": False,
        "items": items,
    }
    _atomic_write_text(md_path, build_daily_markdown(d, options, items))
    _atomic_write_json(json_path, payload)

    summarize_all_readmes_from_raw(
        items,
        d=d,
        options=options,
        cache_json_path=json_path,
        cache_payload=payload,
    )
    payload["summaries_complete"] = _all_summaries_done(items)
    md_text = build_daily_markdown(d, options, items)
    _atomic_write_text(md_path, md_text)
    _atomic_write_json(json_path, payload)
    logger.info(
        f"Trending 缓存写入完成: md={md_path}, json={json_path}, count={len(items)}, summaries_complete={payload['summaries_complete']}"
    )
    return items, True


def has_success_cache_all_periods(
    d: date | str | None = None, language: str | None = None
) -> bool:
    for since in ("daily", "weekly", "monthly"):
        if not has_success_cache(d, TrendingOptions(since=since, language=language)):
            return False
    return True
