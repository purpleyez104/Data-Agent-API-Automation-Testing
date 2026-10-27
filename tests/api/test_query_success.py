"""规则路径核心功能测试。"""

from __future__ import annotations

import pytest

from clients import ApiClient
from tests.api.helpers import assert_json_response, assert_success_contract


pytestmark = pytest.mark.functional


@pytest.mark.parametrize(
    ("question", "expected_metric", "expected_column"),
    [
        ("查询 2026-05-31 的 GMV", "gmv", "gmv"),
        ("查询 2026-05-31 的支付订单数", "paid_order_count", "paid_order_count"),
        ("查询 2026-05-31 的下单用户数", "order_user_count", "order_user_count"),
        ("查询 2026-05-31 的下单到支付转化率", "order_to_pay_rate", "order_to_pay_rate"),
    ],
)
def test_single_value_metrics(
    api_client: ApiClient,
    question: str,
    expected_metric: str,
    expected_column: str,
) -> None:
    body = assert_json_response(
        api_client.query({"question": question, "today": "2026-05-31"}),
        200,
    )

    assert_success_contract(body)
    assert body["metric_name"] == expected_metric
    assert body["question_type"] == "single_value"
    assert body["row_count"] == 1
    assert body["columns"] == ["dt", expected_column]
    assert body["data"][0]["dt"] == "2026-05-31"


def test_gmv_synonym_is_supported(api_client: ApiClient) -> None:
    body = assert_json_response(
        api_client.query({"question": "查询 2026-05-31 的成交额", "today": "2026-05-31"}),
        200,
    )
    assert body["metric_name"] == "gmv"


def test_last_seven_days_gmv_trend(api_client: ApiClient) -> None:
    body = assert_json_response(
        api_client.query({"question": "最近7天 GMV 趋势", "today": "2026-05-31"}),
        200,
    )

    assert_success_contract(body)
    assert body["question_type"] == "trend"
    assert body["row_count"] == 7
    assert [row["dt"] for row in body["data"]] == sorted(row["dt"] for row in body["data"])
    assert body["data"][0]["dt"] == "2026-05-25"
    assert body["data"][-1]["dt"] == "2026-05-31"


def test_last_seven_days_comparison(api_client: ApiClient) -> None:
    body = assert_json_response(
        api_client.query(
            {"question": "最近7天 GMV 比前7天变化多少", "today": "2026-05-31"}
        ),
        200,
    )

    assert_success_contract(body)
    assert body["question_type"] == "comparison"
    assert body["row_count"] == 14
    expected_periods = {
        "previous_start_date": "2026-05-18",
        "previous_end_date": "2026-05-24",
        "current_start_date": "2026-05-25",
        "current_end_date": "2026-05-31",
    }
    assert expected_periods.items() <= body["route"]["time_context"].items()


@pytest.mark.parametrize("topn", [1, 5, 10])
def test_single_day_top_products(api_client: ApiClient, topn: int) -> None:
    body = assert_json_response(
        api_client.query(
            {
                "question": f"查询 2026-05-31 热门商品 Top {topn}",
                "today": "2026-05-31",
            }
        ),
        200,
    )

    assert_success_contract(body)
    assert body["question_type"] == "topn"
    assert body["row_count"] == topn
    assert [row["rank_no"] for row in body["data"]] == list(range(1, topn + 1))


def test_no_data_date_returns_empty_success(api_client: ApiClient) -> None:
    body = assert_json_response(
        api_client.query({"question": "查询 2026-06-01 的 GMV", "today": "2026-06-01"}),
        200,
    )

    assert_success_contract(body)
    assert body["row_count"] == 0
    assert body["data"] == []
