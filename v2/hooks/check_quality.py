#!/usr/bin/env python3
"""知识条目质量评分脚本。

支持单文件和多文件（通配符）模式，对知识条目进行 5 维度质量评分。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


VALID_TAGS = {
    "AI", "LLM", "Agent", "开源", "大模型", "机器学习", "深度学习",
    "NLP", "CV", "强化学习", "多模态", "RAG", "向量数据库",
    "推理", "微调", "部署", "框架", "工具链", "自动化", "优化",
}


@dataclass
class DimensionScore:
    name: str
    score: float
    max_score: float
    detail: str


@dataclass
class QualityReport:
    file_path: str
    title: str
    dimensions: list[DimensionScore]
    total_score: float
    grade: str

    def print_summary(self) -> None:
        grade_icon = {"A": "✓", "B": "~", "C": "✗"}[self.grade]
        print(f"\n{'=' * 60}")
        print(f"[{self.grade}] {grade_icon} {self.title}")
        print(f"  文件: {self.file_path}")
        print(f"  总分: {self.total_score:.1f} / 100")
        print("  维度得分:")
        for d in self.dimensions:
            bar_len = int(d.score / d.max_score * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            print(f"    {d.name:<10} {bar} {d.score:.1f}/{d.max_score}  {d.detail}")


def _load_entry(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check_uuid(text: str) -> bool:
    return bool(re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        text, re.IGNORECASE
    ))


def _has_hollow_words(text: str) -> tuple[bool, list[str]]:
    cn_words = ["赋能", "抓手", "闭环", "打通", "全链路", "底层逻辑",
                "颗粒度", "对齐", "拉通", "沉淀", "强大的", "革命性的"]
    en_words = ["groundbreaking", "revolutionary", "game-changing",
                "cutting-edge", "next-generation", "state-of-the-art"]
    found = []
    for w in cn_words:
        if w in text:
            found.append(w)
    text_lower = text.lower()
    for w in en_words:
        if w in text_lower:
            found.append(w)
    return len(found) > 0, found


def score_summary(entry: dict) -> DimensionScore:
    summary = entry.get("summary", "")
    length = len(summary)
    tech_keywords = ["模型", "框架", "API", "神经网络", "算法", "训练", "推理",
                     "embedding", "transformer", "llm", "agent", "rag"]
    has_tech = any(k.lower() in summary.lower() for k in tech_keywords)

    if length >= 50:
        base = 25 if has_tech else 22
    elif length >= 20:
        base = 15 if has_tech else 12
    else:
        base = 5

    detail = f"字数={length}" + (" 含技术词" if has_tech else "")
    return DimensionScore(name="摘要质量", score=base, max_score=25, detail=detail)


def score_tech_depth(entry: dict) -> DimensionScore:
    raw = entry.get("score", 0)
    score = min(max(raw, 0) / 10 * 25, 25)
    return DimensionScore(
        name="技术深度", score=score, max_score=25,
        detail=f"原始score={raw} → 映射到 {score:.1f}"
    )


def score_format(entry: dict) -> DimensionScore:
    score = 0
    details = []

    if _check_uuid(entry.get("id", "")):
        score += 4
        details.append("id✓")
    else:
        details.append("id✗")

    if entry.get("title"):
        score += 4
        details.append("title✓")
    else:
        details.append("title✗")

    url = entry.get("source_url", "")
    if url and (url.startswith("http://") or url.startswith("https://")):
        score += 4
        details.append("url✓")
    else:
        details.append("url✗")

    status = entry.get("status", "")
    if status in ("raw", "analyzed", "published", "archived"):
        score += 4
        details.append("status✓")
    else:
        details.append("status✗")

    for ts_field in ("created_at", "updated_at"):
        ts = entry.get(ts_field, "")
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
            score += 4
            details.append(f"{ts_field}✓")
        except (ValueError, AttributeError):
            details.append(f"{ts_field}✗")

    return DimensionScore(
        name="格式规范", score=score, max_score=20,
        detail=" ".join(details)
    )


def score_tags(entry: dict) -> DimensionScore:
    tags = entry.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    count = len(tags)

    if 1 <= count <= 3:
        valid = [t for t in tags if t in VALID_TAGS]
        score = 15 if len(valid) == count else 10
    elif count == 0:
        score = 0
    else:
        score = max(5, 15 - (count - 3) * 3)

    tag_str = ",".join(tags[:5]) + ("..." if len(tags) > 5 else "")
    return DimensionScore(
        name="标签精度", score=score, max_score=15,
        detail=f"tags=[{tag_str}]"
    )


def score_hollow(entry: dict) -> DimensionScore:
    text = " ".join(str(v) for v in entry.values() if isinstance(v, str))
    has_h, found = _has_hollow_words(text)
    if has_h:
        score = 0
        detail = f"检测到空洞词: {', '.join(found)}"
    else:
        score = 15
        detail = "无空洞词"
    return DimensionScore(name="空洞词检测", score=score, max_score=15, detail=detail)


def grade_from_score(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    return "C"


def evaluate_entry(path: Path) -> QualityReport:
    entry = _load_entry(path)
    dimensions = [
        score_summary(entry),
        score_tech_depth(entry),
        score_format(entry),
        score_tags(entry),
        score_hollow(entry),
    ]
    total = sum(d.score for d in dimensions)
    return QualityReport(
        file_path=str(path),
        title=entry.get("title", "未知标题"),
        dimensions=dimensions,
        total_score=total,
        grade=grade_from_score(total),
    )


def resolve_files(pattern: str) -> list[Path]:
    p = Path(pattern)
    if p.exists() and p.is_file():
        return [p]
    expanded = list(Path(".").glob(pattern))
    if not expanded:
        expanded = list(Path.cwd().glob(pattern))
    return expanded


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python check_quality.py <文件路径或通配符>")
        print("示例: python check_quality.py knowledge/articles/*.json")
        sys.exit(1)

    pattern = sys.argv[1]
    paths = resolve_files(pattern)

    if not paths:
        print(f"错误: 未找到匹配的文件: {pattern}", file=sys.stderr)
        sys.exit(1)

    print(f"开始质量评分，共 {len(paths)} 个文件")
    print("=" * 60)

    reports: list[QualityReport] = []
    for i, p in enumerate(paths, 1):
        print(f"\r[{i}/{len(paths)}] 评分中: {p.name}...", end="", flush=True)
        try:
            report = evaluate_entry(p)
            reports.append(report)
        except Exception as e:
            print(f"\n错误: 无法处理 {p}: {e}")

    print(f"\r{' ' * 60}\r")  # clear progress line

    grade_counts = {"A": 0, "B": 0, "C": 0}
    for r in reports:
        r.print_summary()
        grade_counts[r.grade] += 1

    print("=" * 60)
    print(f"汇总: A={grade_counts['A']} B={grade_counts['B']} C={grade_counts['C']}")
    print(f"总计 {len(reports)} 个文件，平均分 {sum(r.total_score for r in reports)/len(reports):.1f}")

    if grade_counts["C"] > 0:
        print("\n存在 C 级条目，质量不达标。")
        return 1
    print("\n全部达到 B 级以上，质量达标。")
    return 0


if __name__ == "__main__":
    sys.exit(main())