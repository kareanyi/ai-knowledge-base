## With memory

```
millerlin@192 v1 % cat utils/github_api.py
import logging
from urllib.request import urlopen, Request
import json

logger = logging.getLogger(__name__)


def get_repo_info(owner: str, repo: str) -> dict:
    """Fetch basic info for a GitHub repository.

    Args:
        owner: Repository owner (user or organization).
        repo: Repository name.

    Returns:
        Dict containing stargazers_count, forks_count, and description.
        Returns empty dict if the request fails.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "stargazers_count": data.get("stargazers_count", 0),
                "forks_count": data.get("forks_count", 0),
                "description": data.get("description") or "",
            }
    except Exception as e:
        logger.warning("Failed to fetch repo info for %s/%s: %s", owner, repo, e)
        return {}
```

| 检查项           | 期望（有 Memory） | 实际 |
|:--------------|:-------------|:---|
| 命名风格          | snake_case   | ✅  |
| 有没有 docstring | 有（Google 风格） | ✅  |
| 有没有用 print()  | 不用，用 logging | ✅  |
| 文件放在哪个目录      | 按项目结构放置      | ✅  |

## Without memory

```
millerlin@192 v1 % cat utils/github_api_new.py
import requests


def get_repo_info(owner: str, repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "description": data.get("description", ""),
    }%
```

| 检查项           | 无 Memory 实际表现 |
|:--------------|:--------------|
| 命名风格          | snake_case    |
| 有没有 docstring | 无             |
| 有没有用 print()  | 无             |

# Memory 有无对比：github_api.py vs github_api_new.py

## 总体对比

| 维度 | 有 Memory (github_api.py) | 无 Memory (github_api_new.py) |
|------|---------------------------|-------------------------------|
| **命名风格** | 保守，沿用 GitHub API 原生字段名 `stargazers_count`、`forks_count` | 精简重命名为 `stars`、`forks` |
| **docstring** | 有完整 Google 风格文档，含 Args/Returns 说明 | **无** docstring |
| **日志方式** | 使用 `logging` 模块，失败时 `logger.warning` 记录并返回空 dict | **无日志**，HTTP 错误直接 `raise_for_status()` 抛出异常 |
| **错误处理** | 捕获所有异常，返回空 dict，程序继续运行 | 不捕获异常，HTTP 4xx/5xx 直接崩溃 |
| **文件位置** | `utils/github_api.py` | `utils/github_api_new.py` |

---

## 结论

无 Memory 版本（`github_api_new.py`）代码更简洁，但牺牲了**健壮性**和**可维护性**：

1. **错误处理**：有 Memory 版本通过 try/except + 返回默认值保证程序不崩溃；无 Memory 版本直接抛出异常，上层调用方必须自行处理。
2. **日志**：有 Memory 版本保留了完整的调试线索；无 Memory 版本没有任何运行记录。
3. **可发现性**：有 Memory 版本有完整 docstring；无 Memory 版本调用方只能靠读源码猜用法。
4. **命名**：无 Memory 版本的短命名（`stars`/`forks`）更符合现代直觉，但字段名与 API 原生不一致，增加了理解成本。

整体而言，**有 Memory 版本更适合生产环境**，无 Memory 版本可作为快速原型参考。
