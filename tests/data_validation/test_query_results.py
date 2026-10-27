"""API 结果与人工维护的独立 MySQL 查询对账。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from clients import ApiClient, DatabaseClient
from tests.api.helpers import assert_json_response


pytestmark = pytest.mark.data_validation


def normalize_value(value: Any) -> Any:
    """统一 JSON 与数据库驱动对日期和 Decimal 的不同表示。"""

    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return format(Decimal(str(value)), "f")
    return str(value) if hasattr(value, "isoformat") else value


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """逐字段归一化结果行，保留行顺序用于趋势和排名验证。"""

    return [
        {key: normalize_value(value) for key, value in row.items()}
        for row in rows
    ]


@pytest.mark.parametrize(
    ("question", "sql_file", "expected_metric"),
    [
        ("查询 2026-05-31 的 GMV", "single_day_gmv.sql", "gmv"),
        (
            "查询 2026-05-31 的支付订单数",
            "single_day_paid_orders.sql",
            "paid_order_count",
        ),
    ],
)
def test_single_day_value_matches_mysql(
    api_client: ApiClient,
    database_client: DatabaseClient,
    question: str,
    sql_file: str,
    expected_metric: str,
) -> None:
    body = assert_json_response(
        api_client.query({"question": question, "today": "2026-05-31"}),
        200,
    )
    expected = database_client.query_file(sql_file, {"target_date": "2026-05-31"})

    assert body["metric_name"] == expected_metric
    assert normalize_rows(body["data"]) == normalize_rows(expected)


def test_gmv_trend_matches_mysql(
    api_client: ApiClient,
    database_client: DatabaseClient,
) -> None:
    body = assert_json_response(
        api_client.query({"question": "最近7天 GMV 趋势", "today": "2026-05-31"}),
        200,
    )
    expected = database_client.query_file(
        "gmv_trend_7d.sql",
        {"start_date": "2026-05-25", "end_date": "2026-05-31"},
    )

    assert body["row_count"] == len(expected) == 7
    assert normalize_rows(body["data"]) == normalize_rows(expected)


def test_gmv_comparison_source_rows_and_summary_match_mysql(
    api_client: ApiClient,
    database_client: DatabaseClient,
) -> None:
    body = assert_json_response(
        api_client.query(
            {"question": "最近7天 GMV 比前7天变化多少", "today": "2026-05-31"}
        ),
        200,
    )
    expected = database_client.query_file(
        "gmv_comparison.sql",
        {
            "previous_start_date": "2026-05-18",
            "current_end_date": "2026-05-31",
        },
    )

    assert body["row_count"] == len(expected) == 14
    assert normalize_rows(body["data"]) == normalize_rows(expected)

    previous_total = sum(row["gmv"] for row in expected[:7])
    current_total = sum(row["gmv"] for row in expected[7:])
    difference = current_total - previous_total
    assert format(previous_total, "f") in body["summary"]
    assert format(current_total, "f") in body["summary"]
    assert format(abs(difference), "f") in body["summary"]


def test_top_five_products_match_mysql(
    api_client: ApiClient,
    database_client: DatabaseClient,
) -> None:
    body = assert_json_response(
        api_client.query(
            {
                "question": "查询 2026-05-31 热门商品 Top 5",
                "today": "2026-05-31",
            }
        ),
        200,
    )
    expected = database_client.query_file(
        "top_products_5.sql",
        {"target_date": "2026-05-31"},
    )

    assert body["row_count"] == len(expected) == 5
    assert normalize_rows(body["data"]) == normalize_rows(expected)
    assert [row["rank_no"] for row in expected] == [1, 2, 3, 4, 5]
