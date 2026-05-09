"""Cost guard for multi-agent budget tracking."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded."""

    def __init__(self, total_cost: float, budget: float) -> None:
        self.total_cost = total_cost
        self.budget = budget
        super().__init__(f"Budget exceeded: {total_cost:.4f} yuan > {budget:.4f} yuan")


@dataclass
class CostRecord:
    """Record of a single LLM call."""

    timestamp: datetime
    node_name: str
    prompt_tokens: int
    completion_tokens: int
    cost_yuan: float
    model: str = ""


class CostGuard:
    """Budget guard with三重保护机制 for LLM cost tracking.

    Attributes:
        budget_yuan: Maximum budget in yuan.
        alert_threshold: Ratio of budget to trigger warning (0.0-1.0).
        input_price_per_million: Price per million input tokens.
        output_price_per_million: Price per million output tokens.
    """

    def __init__(
        self,
        budget_yuan: float = 1.0,
        alert_threshold: float = 0.8,
        input_price_per_million: float = 1.0,
        output_price_per_million: float = 2.0,
    ) -> None:
        self.budget_yuan = budget_yuan
        self.alert_threshold = alert_threshold
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million
        self._records: list[CostRecord] = []

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self._records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self._records)

    @property
    def total_cost_yuan(self) -> float:
        return sum(r.cost_yuan for r in self._records)

    def record(self, node_name: str, usage: dict[str, int], model: str = "") -> None:
        """Record a single LLM call.

        Args:
            node_name: Name of the workflow node (e.g., "analyzer", "reviewer").
            usage: Token usage dict with "prompt_tokens" and "completion_tokens".
            model: Model identifier (e.g., "gpt-4o").
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost_yuan = (
            prompt_tokens * self.input_price_per_million / 1_000_000
            + completion_tokens * self.output_price_per_million / 1_000_000
        )
        record = CostRecord(
            timestamp=datetime.now(timezone.utc),
            node_name=node_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_yuan=cost_yuan,
            model=model,
        )
        self._records.append(record)

    def check(self) -> dict[str, Any]:
        """Check budget status.

        Returns:
            Dict with status, total_cost, budget, usage_ratio, and message.

        Raises:
            BudgetExceededError: If total cost exceeds budget.
        """
        total_cost = self.total_cost_yuan
        usage_ratio = total_cost / self.budget_yuan if self.budget_yuan > 0 else 0.0

        if total_cost > self.budget_yuan:
            raise BudgetExceededError(total_cost, self.budget_yuan)

        if usage_ratio >= self.alert_threshold:
            status = "warning"
            message = f"Budget warning: {usage_ratio:.1%} used ({total_cost:.4f}/{self.budget_yuan:.4f} yuan)"
        else:
            status = "ok"
            message = f"Budget OK: {usage_ratio:.1%} used ({total_cost:.4f}/{self.budget_yuan:.4f} yuan)"

        return {
            "status": status,
            "total_cost": round(total_cost, 6),
            "budget": self.budget_yuan,
            "usage_ratio": round(usage_ratio, 4),
            "message": message,
        }

    def get_report(self) -> dict[str, Any]:
        """Generate cost report grouped by node.

        Returns:
            Dict with overall stats and per-node breakdown.
        """
        node_stats: dict[str, dict[str, Any]] = {}
        for record in self._records:
            if record.node_name not in node_stats:
                node_stats[record.node_name] = {
                    "calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost_yuan": 0.0,
                    "models": set(),
                }
            stats = node_stats[record.node_name]
            stats["calls"] += 1
            stats["prompt_tokens"] += record.prompt_tokens
            stats["completion_tokens"] += record.completion_tokens
            stats["cost_yuan"] += record.cost_yuan
            if record.model:
                stats["models"].add(record.model)

        result: dict[str, Any] = {
            "total_cost_yuan": round(self.total_cost_yuan, 6),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_calls": len(self._records),
            "budget_yuan": self.budget_yuan,
            "usage_ratio": round(self.total_cost_yuan / self.budget_yuan, 4)
            if self.budget_yuan > 0
            else 0.0,
            "by_node": {},
        }
        for node_name, stats in node_stats.items():
            result["by_node"][node_name] = {
                "calls": stats["calls"],
                "prompt_tokens": stats["prompt_tokens"],
                "completion_tokens": stats["completion_tokens"],
                "cost_yuan": round(stats["cost_yuan"], 6),
                "models": sorted(stats["models"]),
            }

        return result

    def save_report(self, path: str | Path | None = None) -> str:
        """Save cost report to JSON file.

        Args:
            path: Output file path. If None, saves to cost_report.json in current dir.

        Returns:
            Path to the saved file.
        """
        if path is None:
            path = Path("cost_report.json")
        else:
            path = Path(path)

        report = self.get_report()
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        return str(path)


if __name__ == "__main__":
    import unittest

    class TestCostGuard(unittest.TestCase):
        def setUp(self) -> None:
            self.guard = CostGuard(
                budget_yuan=0.01,
                alert_threshold=0.8,
                input_price_per_million=1.0,
                output_price_per_million=2.0,
            )

        def test_cost_tracking(self) -> None:
            self.guard.record("analyzer", {"prompt_tokens": 1000, "completion_tokens": 500})
            self.assertEqual(self.guard.total_prompt_tokens, 1000)
            self.assertEqual(self.guard.total_completion_tokens, 500)
            expected_cost = 1000 * 1.0 / 1_000_000 + 500 * 2.0 / 1_000_000
            self.assertAlmostEqual(self.guard.total_cost_yuan, expected_cost, places=9)

        def test_multiple_records(self) -> None:
            self.guard.record("analyzer", {"prompt_tokens": 1000, "completion_tokens": 500})
            self.guard.record("reviewer", {"prompt_tokens": 2000, "completion_tokens": 1000})
            self.assertEqual(self.guard.total_prompt_tokens, 3000)
            self.assertEqual(self.guard.total_completion_tokens, 1500)

        def test_budget_exceeded(self) -> None:
            self.guard.record("analyzer", {"prompt_tokens": 5_000_000, "completion_tokens": 5_000_000})
            with self.assertRaises(BudgetExceededError) as ctx:
                self.guard.check()
            self.assertGreater(ctx.exception.total_cost, self.guard.budget_yuan)

        def test_alert_threshold(self) -> None:
            cost_per_call = 1000 * 1.0 / 1_000_000 + 500 * 2.0 / 1_000_000
            needed_calls = int(self.guard.budget_yuan * self.guard.alert_threshold / cost_per_call) + 1
            for i in range(needed_calls):
                self.guard.record("analyzer", {"prompt_tokens": 1000, "completion_tokens": 500})
            result = self.guard.check()
            self.assertEqual(result["status"], "warning")

        def test_report_generation(self) -> None:
            self.guard.record("analyzer", {"prompt_tokens": 1000, "completion_tokens": 500})
            self.guard.record("analyzer", {"prompt_tokens": 2000, "completion_tokens": 1000})
            self.guard.record("reviewer", {"prompt_tokens": 500, "completion_tokens": 250})
            report = self.guard.get_report()
            self.assertEqual(report["total_calls"], 3)
            self.assertEqual(report["by_node"]["analyzer"]["calls"], 2)
            self.assertEqual(report["by_node"]["reviewer"]["calls"], 1)
            self.assertEqual(report["by_node"]["analyzer"]["prompt_tokens"], 3000)

        def test_save_report(self) -> None:
            import tempfile

            self.guard.record("test", {"prompt_tokens": 100, "completion_tokens": 50})
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                path = self.guard.save_report(f.name)
            self.assertTrue(Path(path).exists())

    unittest.main(verbosity=2)