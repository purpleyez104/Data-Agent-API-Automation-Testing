"""请求模型、业务输入和 TopN 边界测试。"""

from __future__ import annotations

import pytest

from clients import ApiClient
from tests.api.helpers import assert_json_response


pytestmark = pytest.mark.boundary


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": ""},
    ],
)
def test_invalid_request_model_returns_422(
    api_client: ApiClient,
    payload: dict[str, str],
) -> None:
    body = assert_json_response(api_client.query(payload), 422)
    assert isinstance(body["detail"], list)
    assert any(error.get("loc", [])[-1:] == ["question"] for error in body["detail"])


@pytest.mark.parametrize(
    "question",
    [
        "查询 2026-05-31 的退款金额",
        "查询 2026-05-31 的热门商品",
        "查询 2026-05-31 的热门商品 Top 11",
    ],
)
def test_unsupported_business_input_returns_400(
    api_client: ApiClient,
    question: str,
) -> None:
    body = assert_json_response(
        api_client.query({"question": question, "today": "2026-05-31"}),
        400,
    )
    assert isinstance(body["detail"], str) and body["detail"].strip()


@pytest.mark.xfail(
    strict=True,
    reason="BUG-001：跨日 TopN 被静默降级为首日查询，未按 Contract 拒绝",
)
def test_cross_day_topn_is_rejected(api_client: ApiClient) -> None:
    assert_json_response(
        api_client.query(
            {
                "question": "查询 2026-05-30 至 2026-05-31 的热门商品 Top 5",
                "today": "2026-05-31",
            }
        ),
        400,
    )


def test_whitespace_question_is_rejected(api_client: ApiClient) -> None:
    response = api_client.query({"question": "   ", "today": "2026-05-31"})
    assert response.status_code in {400, 422}, (
        "全空格问题应受到受控拒绝；"
        f"实际 HTTP {response.status_code}：{response.text[:500]}"
    )


def test_invalid_today_is_rejected(api_client: ApiClient) -> None:
    response = api_client.query({"question": "最近7天 GMV 趋势", "today": "not-a-date"})
    assert response.status_code == 400, (
        "非法 today 应作为客户端业务输入错误返回 400；"
        f"实际 HTTP {response.status_code}：{response.text[:500]}"
    )


def test_unsupported_http_method_returns_405(api_client: ApiClient) -> None:
    body = assert_json_response(api_client.request("GET", "/query"), 405)
    assert "detail" in body
