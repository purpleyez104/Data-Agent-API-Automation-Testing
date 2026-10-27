"""Ecommerce Data Agent 最小核心链路冒烟测试。"""

from __future__ import annotations

from typing import Any

import pytest
import requests
from sqlalchemy import text
from sqlalchemy.engine import Engine


pytestmark = pytest.mark.smoke
REQUEST_TIMEOUT_SECONDS = 5


class TestSmoke:
    """验证数据库、服务进程和规则查询的最小核心链路。"""

    @classmethod
    def setup_class(cls) -> None:
        """为当前冒烟测试模块创建可复用的 HTTP Session。"""

        cls.session = requests.session()

    @classmethod
    def teardown_class(cls) -> None:
        """冒烟测试结束后释放 HTTP Session 持有的连接。"""

        cls.session.close()

    @staticmethod
    def _get_json(response: requests.Response) -> dict[str, Any]:
        """校验 JSON 响应的基础 HTTP Contract，并返回解析结果。"""

        assert response.status_code == 200, (
            f"期望 HTTP 200，实际为 {response.status_code}；"
            f"响应前 300 字符：{response.text[:300]}"
        )
        assert response.headers.get("content-type", "").startswith("application/json")
        body = response.json()
        assert isinstance(body, dict)
        return body

    def test_test_database_is_reachable_and_seeded(self, db_engine: Engine) -> None:
        """只读连接应进入指定测试库，且三张核心 ADS 表均有测试数据。"""

        with db_engine.connect() as connection:
            database_name = connection.execute(text("SELECT DATABASE()")).scalar_one()
            counts = {
                table_name: connection.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar_one()
                for table_name in (
                    "ads_gmv_day",
                    "ads_top_product",
                    "ads_user_conversion",
                )
            }

        assert database_name == "ecommerce_agent_test"
        assert all(count > 0 for count in counts.values()), f"测试表存在空表：{counts}"

    def test_root_endpoint_exposes_service_entry(
        self,
        base_url: str,
    ) -> None:
        """服务入口应返回运行提示和 OpenAPI 文档路径。"""

        response = self.session.get(
            f"{base_url}/",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        body = self._get_json(response)

        assert body == {
            "message": "Ecommerce Data Agent is running.",
            "docs": "/docs",
        }

    def test_health_endpoint_reports_process_alive(
        self,
        base_url: str,
    ) -> None:
        """健康检查应证明 FastAPI 进程能够正常响应。"""

        response = self.session.get(
            f"{base_url}/health",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        body = self._get_json(response)

        assert body == {"status": "ok"}

    def test_rule_based_query_reaches_mysql(
        self,
        base_url: str,
    ) -> None:
        """固定日期 GMV 查询应走规则路径并返回一行真实数据。"""

        question = "查询 2026-05-31 的 GMV"
        response = self.session.post(
            f"{base_url}/query",
            json={"question": question, "today": "2026-05-31"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        body = self._get_json(response)

        required_fields = {
            "question",
            "metric_name",
            "question_type",
            "route",
            "sql",
            "normalized_sql",
            "row_count",
            "columns",
            "data",
            "summary",
        }
        assert required_fields <= body.keys()
        assert body["question"] == question
        assert body["metric_name"] == "gmv"
        assert body["question_type"] == "single_value"
        assert body["route"]["use_rule_based"] is True
        assert body["route"]["need_llm_sql"] is False
        assert body["row_count"] == len(body["data"]) == 1
        assert set(body["data"][0]) == set(body["columns"])
        assert body["data"][0]["dt"] == "2026-05-31"
        assert body["data"][0]["gmv"] is not None
        assert body["normalized_sql"].lstrip().upper().startswith("SELECT")
        assert "ads_gmv_day" in body["normalized_sql"].lower()
