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
