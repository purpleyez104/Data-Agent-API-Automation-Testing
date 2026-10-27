"""API 测试共享断言，避免不同场景重复基础 Contract 检查。"""

from __future__ import annotations

from typing import Any

import requests


REQUIRED_QUERY_FIELDS = {
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


def assert_json_response(response: requests.Response, expected_status: int) -> Any:
    """校验基础 HTTP Contract，并返回 JSON Body。"""

    assert response.status_code == expected_status, (
        f"期望 HTTP {expected_status}，实际为 {response.status_code}；"
        f"响应前 500 字符：{response.text[:500]}"
    )
    assert response.headers.get("content-type", "").startswith("application/json")
    return response.json()


def assert_success_contract(body: dict[str, Any]) -> None:
    """校验所有成功问数响应共享的结构和字段关系。"""

    assert REQUIRED_QUERY_FIELDS <= body.keys()
    assert isinstance(body["question"], str)
    assert body["metric_name"] is None or isinstance(body["metric_name"], str)
    assert isinstance(body["question_type"], str)
    assert isinstance(body["route"], dict)
    assert isinstance(body["sql"], str) and body["sql"].strip()
    assert isinstance(body["normalized_sql"], str) and body["normalized_sql"].strip()
    assert isinstance(body["row_count"], int) and body["row_count"] >= 0
    assert isinstance(body["columns"], list)
    assert all(isinstance(column, str) for column in body["columns"])
    assert isinstance(body["data"], list)
    assert isinstance(body["summary"], str) and body["summary"].strip()
    assert body["row_count"] == len(body["data"])
    assert body["metric_name"] == body["route"]["metric_name"]
    assert body["question_type"] == body["route"]["question_type"]
    assert all(set(row) == set(body["columns"]) for row in body["data"])
