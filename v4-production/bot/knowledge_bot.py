"""知识库交互模块，支持搜索、订阅、权限管理。

提供 KnowledgeBot 作为统一入口，封装搜索引擎、订阅管理、权限控制功能。
"""

import enum
import fnmatch
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


ARTICLES_DIR = Path(__file__).parent.parent / "knowledge" / "articles"


class Intent(enum.Enum):
    """支持的意图类型。"""

    SEARCH = "search"
    TODAY = "today"
    TOP = "top"
    SUBSCRIBE = "subscribe"
    HELP = "help"
    UNKNOWN = "unknown"


class Permission(enum.Enum):
    """权限级别。"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"


@dataclass
class SearchFilter:
    """搜索过滤器。"""

    keywords: list[str] = None
    tags: list[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.tags is None:
            self.tags = []


@dataclass
class Article:
    """知识条目。"""

    id: str
    title: str
    source: str
    url: str
    summary: str
    tags: list[str]
    relevance_score: float
    category: str
    collected_at: str
    key_insight: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        return cls(
            id=data["id"],
            title=data["title"],
            source=data["source"],
            url=data["url"],
            summary=data["summary"],
            tags=data.get("tags", []),
            relevance_score=data.get("relevance_score", 0.0),
            category=data.get("category", ""),
            collected_at=data["collected_at"],
            key_insight=data.get("key_insight", ""),
        )


class KnowledgeSearchEngine:
    """知识库搜索引擎，支持多维度过滤检索。"""

    def __init__(self, articles_dir: Optional[Path | str] = None):
        if articles_dir is None:
            articles_dir = ARTICLES_DIR
        self.articles_dir = Path(articles_dir) if isinstance(articles_dir, str) else articles_dir

    def _load_articles(self) -> list[Article]:
        articles = []
        if not self.articles_dir.exists():
            return articles
        for fp in self.articles_dir.glob("*.json"):
            if fp.name == "index.json":
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                    articles.append(Article.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return articles

    def _match_keywords(self, article: Article, keywords: list[str]) -> bool:
        if not keywords:
            return True
        text = f"{article.title} {article.summary} {article.key_insight}".lower()
        return all(kw.lower() in text for kw in keywords)

    def _match_tags(self, article: Article, tags: list[str]) -> bool:
        if not tags:
            return True
        article_tags = {t.lower() for t in article.tags}
        return any(t.lower() in article_tags for t in tags)

    def _match_date_range(
        self, article: Article, date_from: Optional[str], date_to: Optional[str]
    ) -> bool:
        try:
            collected = datetime.fromisoformat(article.collected_at.replace("Z", "+00:00"))
            if date_from:
                dt_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
                if collected < dt_from:
                    return False
            if date_to:
                dt_to = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
                if collected > dt_to:
                    return False
            return True
        except ValueError:
            return True

    def search(
        self,
        filter_spec: Optional[SearchFilter] = None,
        keyword: str = "",
        limit: int = 20,
    ) -> list[Article]:
        """根据过滤条件搜索知识条目。

        Args:
            filter_spec: 搜索过滤器。
            limit: 返回结果数量上限。

        Returns:
            匹配的知识条目列表，按 relevance_score 降序排列。
        """
        if filter_spec is None:
            filter_spec = SearchFilter(keywords=[keyword] if keyword else [])
        elif keyword:
            filter_spec = SearchFilter(
                keywords=filter_spec.keywords + [keyword],
                tags=filter_spec.tags,
                date_from=filter_spec.date_from,
                date_to=filter_spec.date_to,
                source=filter_spec.source,
                category=filter_spec.category,
            )
        articles = self._load_articles()
        results = []
        for article in articles:
            if not self._match_keywords(article, filter_spec.keywords):
                continue
            if not self._match_tags(article, filter_spec.tags):
                continue
            if not self._match_date_range(article, filter_spec.date_from, filter_spec.date_to):
                continue
            if filter_spec.source and article.source != filter_spec.source:
                continue
            if filter_spec.category and article.category != filter_spec.category:
                continue
            results.append(article)

        results.sort(key=lambda a: a.relevance_score, reverse=True)
        return results[:limit]

    def get_today(self, limit: int = 10) -> list[Article]:
        """获取今日采集的知识条目。

        Args:
            limit: 返回结果数量上限。

        Returns:
            今日的知识条目列表。
        """
        today = datetime.now(timezone.utc).date().isoformat()
        articles = self._load_articles()
        results = [
            a
            for a in articles
            if a.collected_at.startswith(today) or a.id.startswith(today)
        ]
        results.sort(key=lambda a: a.relevance_score, reverse=True)
        return results[:limit]

    def get_top(self, limit: int = 10, days: int = 7) -> list[Article]:
        """获取近期评分最高的热榜条目。

        Args:
            limit: 返回结果数量上限。
            days: 统计天数窗口。

        Returns:
            评分最高的条目列表。
        """
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        articles = self._load_articles()
        results = []
        for a in articles:
            try:
                ts = datetime.fromisoformat(a.collected_at.replace("Z", "+00:00")).timestamp()
                if ts >= cutoff:
                    results.append(a)
            except ValueError:
                continue
        results.sort(key=lambda a: a.relevance_score, reverse=True)
        return results[:limit]


class SubscriptionManager:
    """用户订阅管理，支持增删查。"""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path(__file__).parent / "subscriptions.json"
        self.storage_path = storage_path
        self._subscriptions: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if not self.storage_path.exists():
            return {}
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._subscriptions, f, ensure_ascii=False, indent=2)

    def add(self, user_id: str, subscription: dict) -> bool:
        """添加或更新订阅配置。

        Args:
            user_id: 用户标识。
            subscription: 订阅配置，含 tags、keywords、enabled 等字段。

        Returns:
            操作是否成功。
        """
        self._subscriptions[user_id] = subscription
        self._save()
        return True

    def remove(self, user_id: str) -> bool:
        """删除用户订阅。

        Args:
            user_id: 用户标识。

        Returns:
            用户是否存在并被删除。
        """
        if user_id in self._subscriptions:
            del self._subscriptions[user_id]
            self._save()
            return True
        return False

    def get(self, user_id: str) -> Optional[dict]:
        """查询用户订阅配置。

        Args:
            user_id: 用户标识。

        Returns:
            订阅配置，不存在则返回 None。
        """
        return self._subscriptions.get(user_id)

    def list_all(self) -> dict[str, dict]:
        """列出所有订阅。

        Returns:
            用户 ID 到订阅配置的映射。
        """
        return dict(self._subscriptions)


class PermissionManager:
    """三级权限控制（READ/WRITE/DELETE）。"""

    READ_OPERATIONS = {"search", "today", "top", "help"}
    WRITE_OPERATIONS = {"subscribe"}
    DELETE_OPERATIONS = set()

    def __init__(self):
        self._user_roles: dict[str, Permission] = {}

    def grant(self, user_id: str, permission: Permission) -> None:
        """授予用户权限级别。

        Args:
            user_id: 用户标识。
            permission: 权限级别。
        """
        self._user_roles[user_id] = permission

    def revoke(self, user_id: str) -> None:
        """撤销用户所有权限。

        Args:
            user_id: 用户标识。
        """
        self._user_roles.pop(user_id, None)

    def get(self, user_id: str) -> Permission:
        """获取用户权限级别，默认 READ。

        Args:
            user_id: 用户标识。

        Returns:
            权限级别。
        """
        return self._user_roles.get(user_id, Permission.READ)

    def has_permission(self, user_id: str, operation: str) -> bool:
        """检查用户是否有权限执行指定操作。

        Args:
            user_id: 用户标识。
            operation: 操作名称。

        Returns:
            是否有权限。
        """
        user_perm = self.get(user_id)

        if operation in self.READ_OPERATIONS:
            return True
        if operation in self.WRITE_OPERATIONS:
            return user_perm in (Permission.WRITE, Permission.DELETE)
        if operation in self.DELETE_OPERATIONS:
            return user_perm == Permission.DELETE

        return False


def recognize_intent(text: str) -> tuple[Intent, str]:
    """识别用户意图（规则匹配，无需 LLM）。

    优先匹配命令前缀（/search, /today, /top, /subscribe, /help），
    再匹配自然语言关键词（搜索、查询、今天、简报、订阅等）。

    Args:
        text: 用户输入文本。

    Returns:
        (Intent 枚举, 参数字符串) 元组。
    """
    text = text.strip()

    if text.startswith("/search "):
        return (Intent.SEARCH, text[len("/search ") :].strip())
    if text.startswith("/today"):
        return (Intent.TODAY, text[len("/today") :].strip())
    if text.startswith("/top "):
        return (Intent.TOP, text[len("/top ") :].strip())
    if text.startswith("/subscribe"):
        return (Intent.SUBSCRIBE, text[len("/subscribe") :].strip())
    if text.startswith("/help"):
        return (Intent.HELP, text[len("/help") :].strip())

    lower = text.lower()

    if any(kw in lower for kw in ("订阅", "subscribe", "订阅主题", "关注")):
        return (Intent.SUBSCRIBE, text)
    if any(kw in lower for kw in ("搜索", "查询", "找", "search", "搜一下")):
        return (Intent.SEARCH, text)
    if any(kw in lower for kw in ("今天", "今日", "today", "今日动态")):
        return (Intent.TODAY, text)
    if any(kw in lower for kw in ("top", "排行", "热榜", "最热", "热门", "简报")):
        return (Intent.TOP, text)
    if any(kw in lower for kw in ("帮助", "help", "怎么用", "命令")):
        return (Intent.HELP, text)

    return (Intent.UNKNOWN, text)


class KnowledgeBot:
    """知识库机器人，整合搜索、订阅、权限模块的统一入口。"""

    def __init__(
        self,
        articles_dir: Optional[Path] = None,
        subscriptions_path: Optional[Path] = None,
    ):
        self.search_engine = KnowledgeSearchEngine(articles_dir or ARTICLES_DIR)
        self.subscription_mgr = SubscriptionManager(subscriptions_path)
        self.permission_mgr = PermissionManager()

    def handle_message(self, user_id: str, text: str) -> str:
        """统一消息入口，根据意图分发到对应处理器。

        Args:
            user_id: 用户标识。
            text: 用户输入文本。

        Returns:
            机器人响应文本。
        """
        intent, params = recognize_intent(text)

        if intent == Intent.SEARCH:
            return self._handle_search(user_id, params)
        if intent == Intent.TODAY:
            return self._handle_today(user_id, params)
        if intent == Intent.TOP:
            return self._handle_top(user_id, params)
        if intent == Intent.SUBSCRIBE:
            return self._handle_subscribe(user_id, params)
        if intent == Intent.HELP:
            return self._handle_help(user_id, params)

        return self._format_unknown(text)

    def _require_permission(self, user_id: str, operation: str) -> bool:
        return self.permission_mgr.has_permission(user_id, operation)

    def _handle_search(self, user_id: str, params: str) -> str:
        if not self._require_permission(user_id, "search"):
            return "⚠️ 无阅读权限"

        filter_spec = self._parse_search_params(params)
        results = self.search_engine.search(filter_spec)

        if not results:
            return "🔍 未找到匹配结果，试试其他关键词？"

        lines = ["📚 搜索结果："]
        for i, a in enumerate(results[:5], 1):
            lines.append(f"{i}. [{a.title}]({a.url})")
            lines.append(f"   {a.summary[:80]}...")
        return "\n".join(lines)

    def _handle_today(self, user_id: str, params: str) -> str:
        if not self._require_permission(user_id, "today"):
            return "⚠️ 无阅读权限"

        results = self.search_engine.get_today()
        if not results:
            return "📅 今日暂无新条目"

        lines = ["📅 今日知识速递："]
        for i, a in enumerate(results[:5], 1):
            lines.append(f"{i}. [{a.title}]({a.url})")
            lines.append(f"   #{' #'.join(a.tags[:3])}")
        return "\n".join(lines)

    def _handle_top(self, user_id: str, params: str) -> str:
        if not self._require_permission(user_id, "top"):
            return "⚠️ 无阅读权限"

        days = 7
        limit = 10
        parts = params.split()
        if parts:
            try:
                limit = int(parts[0])
            except ValueError:
                pass

        results = self.search_engine.get_top(limit=limit, days=days)
        if not results:
            return "🏆 暂无热榜数据"

        lines = ["🏆 AI 知识热榜："]
        for i, a in enumerate(results[:limit], 1):
            lines.append(f"{i}. [{a.title}]({a.url}) ⭐{a.relevance_score:.2f}")
            lines.append(f"   {a.summary[:60]}...")
        return "\n".join(lines)

    def _handle_subscribe(self, user_id: str, params: str) -> str:
        if not self._require_permission(user_id, "subscribe"):
            return "⚠️ 订阅需要 WRITE 权限，请联系管理员"

        existing = self.subscription_mgr.get(user_id)
        if existing:
            return f"📋 当前订阅：tags={existing.get('tags')}, keywords={existing.get('keywords')}"

        default_sub = {"tags": [], "keywords": [], "enabled": True}
        self.subscription_mgr.add(user_id, default_sub)
        return "✅ 订阅已创建，使用 /search 或关键词搜索感兴趣的内容"

    def _handle_help(self, user_id: str, params: str) -> str:
        help_text = """🤖 知识库机器人命令：

/search <关键词>  — 按关键词搜索
/today            — 查看今日新条目
/top [数量]       — 查看热榜（默认10条）
/subscribe        — 管理订阅
/help             — 显示此帮助

也可直接发送自然语言，如「搜索 AI Agent」「今天有什么新内容」"""
        return help_text

    def _format_unknown(self, text: str) -> str:
        return f"❓ 无法识别意图：「{text[:30]}」\n输入 /help 查看可用命令"

    def _parse_search_params(self, text: str) -> SearchFilter:
        keywords = []
        tags = []
        date_from = None
        date_to = None

        tag_pattern = r"#(\w+)"
        for match in re.findall(tag_pattern, text):
            tags.append(match)

        remaining = re.sub(tag_pattern, "", text).strip()

        words = remaining.split()
        for w in words:
            if w.startswith("from:"):
                date_from = w[5:]
            elif w.startswith("to:"):
                date_to = w[3:]
            elif w.startswith("source:"):
                pass
            elif len(w) > 2:
                keywords.append(w)

        return SearchFilter(
            keywords=keywords if keywords else [],
            tags=tags if tags else [],
            date_from=date_from,
            date_to=date_to,
        )


def format_search_results(articles: list[Article], query: str = "") -> str:
    """格式化搜索结果为可读字符串。

    Args:
        articles: Article 列表。
        query: 搜索关键词（用于标题）。

    Returns:
        格式化的结果字符串。
    """
    if not articles:
        return "🔍 未找到结果"

    lines = [f"📚 搜索「{query}」结果："]
    for i, a in enumerate(articles, 1):
        lines.append(f"\n{i}. [{a.title}]({a.url})")
        lines.append(f"   {a.summary[:80]}...")
        if a.tags:
            lines.append(f"   {' '.join(f'#{t}' for t in a.tags[:3])}")
    return "\n".join(lines)
