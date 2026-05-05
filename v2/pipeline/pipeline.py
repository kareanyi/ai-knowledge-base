#!/usr/bin/env python3
"""知识库自动化流水线。

四步处理：采集(Collect) → 分析(Analyze) → 整理(Organize) → 保存(Save)

Usage:
    python pipeline/pipeline.py --sources github,rss --limit 20   # 完整流水线
    python pipeline/pipeline.py --sources github --limit 5         # 只采集 GitHub
    python pipeline/pipeline.py --sources rss --limit 10           # 只采集 RSS
    python pipeline/pipeline.py --sources github --limit 5 --dry-run  # 干跑模式
    python pipeline/pipeline.py --verbose                          # 详细日志
"""

import argparse
import json
import logging
import random
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from model_client import chat_with_retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
RAW_DIR = KNOWLEDGE_DIR / "raw"
ARTICLES_DIR = KNOWLEDGE_DIR / "articles"

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://feeds.feedburner.com/oreilly radar",
    "https://www.artificialintelligence-news.com/feed/",
]

GITHUB_AI_QUERY = "AI OR artificial intelligence OR LLM OR large language model OR GPT OR machine learning"
GITHUB_SORT = "stars"
GITHUB_ORDER = "desc"


@dataclass
class RawItem:
    """原始采集条目。"""

    id: str
    source: str
    source_url: str
    title: str
    content: str
    author: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzedItem:
    """分析后的知识条目。"""

    id: str
    source: str
    source_url: str
    title: str
    summary: str
    tech_stack: list[str]
    problem_solved: str
    why_valuable: str
    tags: list[str]
    score: int
    status: str = "analyzed"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_to: list[str] = field(default_factory=list)


class PipelineError(Exception):
    """流水线执行错误。"""


class Collector:
    """采集器：从 GitHub Search API 和 RSS 源采集内容。"""

    def __init__(self, limit: int = 20) -> None:
        self.limit = limit
        self.client = httpx.Client(timeout=30.0)

    def collect_github(self, limit: int | None = None) -> list[RawItem]:
        """从 GitHub Search API 采集 AI 相关仓库。

        Args:
            limit: 采集数量上限，默认使用实例的 limit。

        Returns:
            原始条目列表。
        """
        effective_limit = min(limit or self.limit, 100)
        query = GITHUB_AI_QUERY.replace(" ", "+")
        url = (
            f"https://api.github.com/search/repositories"
            f"?q={query}&sort={GITHUB_SORT}&order={GITHUB_ORDER}&per_page={effective_limit}"
        )
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-knowledge-base-pipeline/1.0",
        }

        log.info("Collecting GitHub repositories: %s", url.split("?")[0])
        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            log.error("GitHub API request failed: %s", e)
            return []

        items: list[RawItem] = []
        for repo in data.get("items", [])[:effective_limit]:
            raw = RawItem(
                id=f"github-{repo['id']}",
                source="github_trending",
                source_url=repo["html_url"],
                title=repo.get("full_name", ""),
                content=repo.get("description", "") or "",
                author=repo.get("owner", {}).get("login", ""),
                created_at=repo.get("created_at", ""),
                metadata={
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language", ""),
                    "topics": repo.get("topics", []),
                },
            )
            items.append(raw)

        log.info("Collected %d GitHub repositories", len(items))
        return items

    def collect_rss(self, limit: int | None = None) -> list[RawItem]:
        """从 RSS 源采集内容。

        用简易正则解析 XML，提取标题、链接、描述。

        Args:
            limit: 每个源采集数量上限。

        Returns:
            原始条目列表。
        """
        effective_limit = limit or self.limit
        all_items: list[RawItem] = []

        for feed_url in RSS_FEEDS:
            log.info("Collecting RSS feed: %s", feed_url)
            try:
                response = self.client.get(feed_url, timeout=30.0)
                response.raise_for_status()
                xml_content = response.text
            except httpx.HTTPError as e:
                log.warning("RSS feed request failed for %s: %s", feed_url, e)
                continue

            items = self._parse_rss(xml_content, feed_url, effective_limit)
            all_items.extend(items)
            log.info("Collected %d items from %s", len(items), feed_url)

        log.info("Collected %d items from RSS feeds", len(all_items))
        return all_items

    def _parse_rss(self, xml: str, feed_url: str, limit: int) -> list[RawItem]:
        """解析 RSS XML 内容。

        Args:
            xml: RSS XML 原始文本。
            feed_url: 源 URL，用于生成 ID。
            limit: 采集数量上限。

        Returns:
            解析后的原始条目列表。
        """
        items: list[RawItem] = []

        item_pattern = re.compile(r"<item>(.*?)</item>", re.DOTALL | re.IGNORECASE)
        title_pattern = re.compile(r"<title><!\[CDATA\[(.*?)\]\]>|"
                                   r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
        link_pattern = re.compile(r"<link>(.*?)</link>", re.DOTALL | re.IGNORECASE)
        desc_pattern = re.compile(r"<description><!\[CDATA\[(.*?)\]\]>|"
                                  r"<description>(.*?)</description>", re.DOTALL | re.IGNORECASE)
        date_pattern = re.compile(r"<pubDate>(.*?)</pubDate>", re.DOTALL | re.IGNORECASE)

        for i, item_match in enumerate(item_pattern.finditer(xml)):
            if i >= limit:
                break

            item_xml = item_match.group(1)

            title_match = title_pattern.search(item_xml)
            title = ""
            if title_match:
                title = title_match.group(1) or title_match.group(2) or ""
                title = title.strip()

            link_match = link_pattern.search(item_xml)
            link = ""
            if link_match:
                link = link_match.group(1).strip()

            desc_match = desc_pattern.search(item_xml)
            content = ""
            if desc_match:
                content = desc_match.group(1) or desc_match.group(2) or ""
                content = re.sub(r"<[^>]+>", "", content).strip()
                content = content[:500]

            date_match = date_pattern.search(item_xml)
            created_at = ""
            if date_match:
                created_at = date_match.group(1).strip()

            if not title or not link:
                continue

            item_id = f"rss-{hash(link) % 1000000}"
            raw = RawItem(
                id=item_id,
                source="hacker_news" if "hnrss" in feed_url else "rss",
                source_url=link,
                title=title,
                content=content,
                created_at=created_at,
            )
            items.append(raw)

        return items

    def close(self) -> None:
        """关闭 HTTP 客户端。"""
        self.client.close()


class Analyzer:
    """分析器：调用 LLM 对内容进行摘要/评分/标签分析。"""

    SYSTEM_PROMPT = """你是一个专业的 AI 技术分析师。你的任务是对输入的技术内容进行深度分析，输出结构化的 JSON 格式结果。

分析内容包括：
1. summary：用 2-3 句话概括这个项目/文章的核心内容
2. tech_stack：提取使用的技术栈列表（最多 5 个）
3. problem_solved：它解决什么问题（1 句话）
4. why_valuable：为什么它有价值（1 句话）
5. tags：生成 3-5 个标签，用于分类（必须是英文单词或短词）
6. score：给出一个 1-10 的质量评分，10 最高

输出格式：只输出 JSON，不要有其他内容。
{
  "summary": "...",
  "tech_stack": ["Python", "LangChain", ...],
  "problem_solved": "...",
  "why_valuable": "...",
  "tags": ["AI", "Agent", ...],
  "score": 8
}
"""

    USER_PROMPT_TEMPLATE = """请分析以下内容：

标题：{title}
链接：{url}
内容：{content}

{metadata_str}
"""

    def __init__(self) -> None:
        self.provider: str | None = None

    def analyze(self, item: RawItem) -> AnalyzedItem | None:
        """分析单个条目。

        Args:
            item: 原始条目。

        Returns:
            分析后的条目，失败返回 None。
        """
        metadata_str = ""
        if item.metadata:
            meta_parts = [f"{k}: {v}" for k, v in item.metadata.items()]
            metadata_str = "元数据：" + " | ".join(meta_parts)

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            title=item.title,
            url=item.source_url,
            content=item.content[:1000] if item.content else "无描述",
            metadata_str=metadata_str,
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = chat_with_retry(messages, self.provider, temperature=0.3)
        except Exception as e:
            log.warning("LLM analysis failed for %s: %s", item.id, e)
            return None

        content = response.content.strip()

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            log.warning("No JSON found in LLM response for %s", item.id)
            return None

        try:
            analysis = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            log.warning("JSON parse failed for %s: %s", item.id, e)
            return None

        return AnalyzedItem(
            id=item.id,
            source=item.source,
            source_url=item.source_url,
            title=item.title,
            summary=analysis.get("summary", ""),
            tech_stack=analysis.get("tech_stack", [])[:5],
            problem_solved=analysis.get("problem_solved", ""),
            why_valuable=analysis.get("why_valuable", ""),
            tags=analysis.get("tags", [])[:5],
            score=min(10, max(1, int(analysis.get("score", 5)))),
        )

    def batch_analyze(self, items: list[RawItem]) -> list[AnalyzedItem]:
        """批量分析条目。

        Args:
            items: 原始条目列表。

        Returns:
            分析后的条目列表。
        """
        results: list[AnalyzedItem] = []
        total = len(items)

        for i, item in enumerate(items, 1):
            log.info("Analyzing [%d/%d]: %s", i, total, item.title[:50])
            analyzed = self.analyze(item)
            if analyzed:
                results.append(analyzed)
                log.info("  Score: %d, Tags: %s", analyzed.score, analyzed.tags)
            time.sleep(random.uniform(0.5, 1.5))

        log.info("Analyzed %d/%d items successfully", len(results), total)
        return results


class Organizer:
    """整理器：去重 + 格式标准化 + 校验。"""

    def __init__(self) -> None:
        self.existing_urls: set[str] = set()
        self._load_existing_urls()

    def _load_existing_urls(self) -> None:
        """加载已存在的文章 URL 用于去重。"""
        if not ARTICLES_DIR.exists():
            return

        for json_file in ARTICLES_DIR.glob("*.json"):
            try:
                data = json.loads(json_file.read_text())
                url = data.get("source_url", "")
                if url:
                    self.existing_urls.add(url)
            except (json.JSONDecodeError, OSError):
                continue

        log.info("Loaded %d existing URLs for deduplication", len(self.existing_urls))

    def organize(self, items: list[AnalyzedItem]) -> list[AnalyzedItem]:
        """整理条目：去重、过滤、校验。

        Args:
            items: 分析后的条目列表。

        Returns:
            整理后的条目列表。
        """
        before_count = len(items)

        items = self._deduplicate(items)
        items = self._filter_quality(items)
        items = self._standardize_format(items)

        log.info(
            "Organized: %d -> %d items (removed %d)",
            before_count,
            len(items),
            before_count - len(items),
        )
        return items

    def _deduplicate(self, items: list[AnalyzedItem]) -> list[AnalyzedItem]:
        """URL 去重。"""
        seen_urls: set[str] = set()
        unique: list[AnalyzedItem] = []

        for item in items:
            if item.source_url not in seen_urls and item.source_url not in self.existing_urls:
                seen_urls.add(item.source_url)
                unique.append(item)
            else:
                log.info("Duplicate removed: %s", item.title[:50])

        return unique

    def _filter_quality(self, items: list[AnalyzedItem]) -> list[AnalyzedItem]:
        """过滤低质量内容。"""
        quality_threshold = 4
        filtered = [item for item in items if item.score >= quality_threshold]
        removed = len(items) - len(filtered)

        if removed > 0:
            log.info("Low quality items removed: %d", removed)

        return filtered

    def _standardize_format(self, items: list[AnalyzedItem]) -> list[AnalyzedItem]:
        """标准化格式。"""
        for item in items:
            item.id = str(uuid.uuid4())
            item.status = "analyzed"
            item.updated_at = datetime.now(timezone.utc).isoformat()

            if isinstance(item.tech_stack, list):
                item.tech_stack = [str(t)[:50] for t in item.tech_stack]
            if isinstance(item.tags, list):
                item.tags = [str(t)[:30] for t in item.tags]

        return items

    def validate(self, item: AnalyzedItem) -> list[str]:
        """校验单个条目。

        Args:
            item: 待校验条目。

        Returns:
            错误列表，空列表表示校验通过。
        """
        errors: list[str] = []

        if not item.title or len(item.title) < 3:
            errors.append("title must be at least 3 characters")
        if not item.source_url or not item.source_url.startswith("http"):
            errors.append("source_url must be a valid URL")
        if not item.summary or len(item.summary) < 20:
            errors.append("summary must be at least 20 characters")
        if not item.tags or len(item.tags) == 0:
            errors.append("tags must not be empty")
        if not isinstance(item.score, int) or not 1 <= item.score <= 10:
            errors.append("score must be between 1 and 10")
        if not item.id or len(item.id) < 10:
            errors.append("id must be a valid UUID")

        return errors


class Saver:
    """保存器：将文章保存为独立 JSON 文件。"""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    def save(self, items: list[AnalyzedItem]) -> list[Path]:
        """保存条目到 JSON 文件。

        Args:
            items: 待保存的条目列表。

        Returns:
            保存的文件路径列表。
        """
        saved_paths: list[Path] = []

        for item in items:
            item.status = "published"
            item.updated_at = datetime.now(timezone.utc).isoformat()

            if self.dry_run:
                log.info("[DRY-RUN] Would save: %s", item.title[:50])
                continue

            file_path = ARTICLES_DIR / f"{item.id}.json"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self._to_dict(item), f, ensure_ascii=False, indent=2)
                saved_paths.append(file_path)
                log.info("Saved: %s", file_path.name)
            except OSError as e:
                log.error("Failed to save %s: %s", file_path.name, e)

        return saved_paths

    def _to_dict(self, item: AnalyzedItem) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "id": item.id,
            "source": item.source,
            "source_url": item.source_url,
            "title": item.title,
            "summary": item.summary,
            "tech_stack": item.tech_stack,
            "problem_solved": item.problem_solved,
            "why_valuable": item.why_valuable,
            "tags": item.tags,
            "score": item.score,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "published_to": item.published_to,
        }


def save_raw_items(items: list[RawItem]) -> Path | None:
    """保存原始采集数据。

    Args:
        items: 原始条目列表。

    Returns:
        保存的文件路径。
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DIR / f"{date_str}-raw.json"

    data = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "items": [
            {
                "id": item.id,
                "source": item.source,
                "source_url": item.source_url,
                "title": item.title,
                "content": item.content,
                "author": item.author,
                "created_at": item.created_at,
                "metadata": item.metadata,
            }
            for item in items
        ],
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info("Raw data saved to: %s", file_path)
        return file_path
    except OSError as e:
        log.error("Failed to save raw data: %s", e)
        return None


def run_pipeline(
    sources: list[str],
    limit: int,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[Path]:
    """运行完整流水线。

    Args:
        sources: 数据源列表 ["github", "rss"]。
        limit: 采集数量上限。
        dry_run: 是否干跑。
        verbose: 是否输出详细日志。

    Returns:
        保存的文件路径列表。
    """
    if verbose:
        log.setLevel(logging.DEBUG)

    log.info("=" * 60)
    log.info("Pipeline started: sources=%s limit=%d dry_run=%s", sources, limit, dry_run)
    log.info("=" * 60)

    collector = Collector(limit=limit)
    analyzer = Analyzer()
    organizer = Organizer()
    saver = Saver(dry_run=dry_run)

    raw_items: list[RawItem] = []

    if "github" in sources:
        github_items = collector.collect_github(limit)
        raw_items.extend(github_items)

    if "rss" in sources:
        rss_items = collector.collect_rss(limit)
        raw_items.extend(rss_items)

    collector.close()

    if not raw_items:
        log.warning("No items collected, pipeline aborted")
        return []

    save_raw_items(raw_items)

    if dry_run:
        log.info("[DRY-RUN] Skipping analysis and save")
        return []

    analyzed_items = analyzer.batch_analyze(raw_items)

    if not analyzed_items:
        log.warning("No items analyzed successfully, pipeline aborted")
        return []

    organized_items = organizer.organize(analyzed_items)

    validated_items: list[AnalyzedItem] = []
    for item in organized_items:
        errors = organizer.validate(item)
        if errors:
            log.warning("Validation failed for %s: %s", item.id, errors)
        else:
            validated_items.append(item)

    if not validated_items:
        log.warning("No items passed validation, pipeline aborted")
        return []

    saved_paths = saver.save(validated_items)

    log.info("=" * 60)
    log.info("Pipeline completed: collected=%d analyzed=%d saved=%d",
             len(raw_items), len(analyzed_items), len(saved_paths))
    log.info("=" * 60)

    return saved_paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    Args:
        argv: 命令行参数列表。

    Returns:
        解析后的命名空间。
    """
    parser = argparse.ArgumentParser(
        description="AI 知识库自动化流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline/pipeline.py --sources github,rss --limit 20   # 完整流水线
  python pipeline/pipeline.py --sources github --limit 5        # 只采集 GitHub
  python pipeline/pipeline.py --sources rss --limit 10          # 只采集 RSS
  python pipeline/pipeline.py --sources github --limit 5 --dry-run  # 干跑模式
  python pipeline/pipeline.py --verbose                            # 详细日志
        """,
    )

    parser.add_argument(
        "--sources",
        type=str,
        default="github,rss",
        help="数据源，逗号分隔 (github,rss)，默认 github,rss",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="每个源采集数量上限，默认 20",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式，不调用 LLM，不保存文件",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细日志输出",
    )

    return parser.parse_args(argv)


def main() -> int:
    """入口函数。"""
    args = parse_args()

    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    valid_sources = {"github", "rss"}
    invalid = set(sources) - valid_sources

    if invalid:
        log.error("Invalid sources: %s. Valid: %s", invalid, valid_sources)
        return 1

    if not sources:
        log.error("No sources specified")
        return 1

    try:
        run_pipeline(
            sources=sources,
            limit=args.limit,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        return 0
    except Exception as e:
        log.error("Pipeline failed: %s", e)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
