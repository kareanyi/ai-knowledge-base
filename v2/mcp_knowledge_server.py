#!/usr/bin/env python3
"""MCP Knowledge Server - Search local knowledge base via JSON-RPC 2.0 over stdio."""

import json
import sys
import os
from pathlib import Path
from collections import Counter
from typing import Any


class MCPError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL_ERROR = -32603

ARTICLES_DIR = Path(__file__).parent / "knowledge" / "articles"


def load_articles() -> list[dict[str, Any]]:
    articles = []
    if ARTICLES_DIR.exists():
        for path in ARTICLES_DIR.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    articles.append(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
    return articles


def search_articles(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    kw = keyword.lower()
    articles = load_articles()
    matches = []
    for article in articles:
        title_match = kw in article.get("title", "").lower()
        summary_match = kw in article.get("summary", "").lower()
        if title_match or summary_match:
            matches.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "source": article.get("source"),
                "summary": article.get("summary", "")[:200],
                "score": article.get("score", 0),
            })
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:limit]


def get_article(article_id: str) -> dict[str, Any] | None:
    articles = load_articles()
    for article in articles:
        if article.get("id") == article_id:
            return article
    return None


def knowledge_stats() -> dict[str, Any]:
    articles = load_articles()
    total = len(articles)
    sources = Counter(a.get("source", "unknown") for a in articles)
    all_tags = [tag for a in articles for tag in a.get("tags", [])]
    top_tags = Counter(all_tags).most_common(10)
    return {
        "total_articles": total,
        "source_distribution": dict(sources),
        "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
    }


TOOLS = {
    "search_articles": {
        "description": "Search articles by keyword in title and summary",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword"},
                "limit": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["keyword"],
        },
    },
    "get_article": {
        "description": "Get full article by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string", "description": "Article UUID"},
            },
            "required": ["article_id"],
        },
    },
    "knowledge_stats": {
        "description": "Get knowledge base statistics",
        "inputSchema": {"type": "object", "properties": {}},
    },
}


def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {"name": "knowledge-server", "version": "1.0.0"},
        "capabilities": {"tools": {}},
    }


def handle_tools_list(params: dict[str, Any]) -> dict[str, Any]:
    tools = [{"name": name, **defn} for name, defn in TOOLS.items()]
    return {"tools": tools}


def handle_tools_call(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name == "search_articles":
        keyword = arguments.get("keyword", "")
        limit = arguments.get("limit", 5)
        return {"content": [{"type": "text", "text": json.dumps(search_articles(keyword, limit), ensure_ascii=False)}]}
    elif name == "get_article":
        article_id = arguments.get("article_id", "")
        article = get_article(article_id)
        if article is None:
            raise MCPError(ERROR_INVALID_PARAMS, f"Article not found: {article_id}")
        return {"content": [{"type": "text", "text": json.dumps(article, ensure_ascii=False)}]}
    elif name == "knowledge_stats":
        return {"content": [{"type": "text", "text": json.dumps(knowledge_stats(), ensure_ascii=False)}]}
    else:
        raise MCPError(ERROR_METHOD_NOT_FOUND, f"Unknown tool: {name}")


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "tools/list":
            result = handle_tools_list(params)
        elif method == "tools/call":
            result = handle_tools_call(params)
        else:
            raise MCPError(ERROR_METHOD_NOT_FOUND, f"Unknown method: {method}")

        response = {"jsonrpc": "2.0", "id": req_id, "result": result}
    except MCPError as e:
        response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": e.code, "message": e.message}}

    return response


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": ERROR_INVALID_REQUEST, "message": "Invalid JSON"}}), flush=True)


if __name__ == "__main__":
    main()