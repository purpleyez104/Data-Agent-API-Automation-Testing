"""Ecommerce Data Agent HTTP Client。

本模块只负责连接复用、URL 拼接和 Timeout，不包含业务断言。
"""

from __future__ import annotations

from typing import Any

import requests


class ApiClient:
    """通过公开 HTTP Contract 访问被测服务。"""

    def __init__(self, base_url: str, timeout: float = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def close(self) -> None:
        """释放 Session 持有的连接。"""

        self.session.close()

    def get_root(self) -> requests.Response:
        """请求服务入口。"""

        return self.session.get(f"{self.base_url}/", timeout=self.timeout)

    def get_health(self) -> requests.Response:
        """请求进程级健康检查。"""

        return self.session.get(f"{self.base_url}/health", timeout=self.timeout)

    def query(self, payload: dict[str, Any]) -> requests.Response:
        """向问数接口提交 JSON Payload。"""

        return self.session.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout,
        )

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """执行边界测试需要的任意 HTTP Method。"""

        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, f"{self.base_url}{path}", **kwargs)

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
