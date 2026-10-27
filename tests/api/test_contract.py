"""公开 HTTP Endpoint 与成功响应 Contract 测试。"""

from __future__ import annotations

import pytest

from clients import ApiClient
from tests.api.helpers import assert_json_response, assert_success_contract


pytestmark = pytest.mark.contract


def test_root_contract(api_client: ApiClient) -> None:
    body = assert_json_response(api_client.get_root(), 200)
    assert body == {"message": "Ecommerce Data Agent is running.", "docs": "/docs"}


def test_health_contract(api_client: ApiClient) -> None:
    body = assert_json_response(api_client.get_health(), 200)
    assert body == {"status": "ok"}


def test_rule_query_success_contract(api_client: ApiClient) -> None:
    question = "查询 2026-05-31 的 GMV"
    body = assert_json_response(
        api_client.query({"question": question, "today": "2026-05-31"}),
        200,
    )

    assert_success_contract(body)
    assert body["question"] == question
    assert body["route"]["use_rule_based"] is True
    assert body["route"]["need_llm_sql"] is False
    assert body["route"]["time_context"] == {
        "start_date": "2026-05-31",
        "end_date": "2026-05-31",
    }
