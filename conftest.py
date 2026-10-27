"""冒烟测试共享 Fixture。

测试通过公开 HTTP Contract 访问被测服务，并使用只读账号确认测试库可用；
不会导入被测项目内部实现，也不会在失败信息中输出数据库密码。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from clients import ApiClient, DatabaseClient


load_dotenv()


@pytest.fixture(scope="session")
def base_url() -> str:
    """返回去除末尾斜杠的被测 API 地址。"""

    return os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


@pytest.fixture(scope="session")
def api_client(base_url: str) -> ApiClient:
    """创建复用连接且带统一 Timeout 的公开 API Client。"""

    with ApiClient(base_url=base_url, timeout=5) as client:
        yield client


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """创建测试库只读连接池，并在测试会话结束后释放连接。"""

    mysql_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER", "data_agent_test_user"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "ecommerce_agent_test"),
        query={"charset": os.getenv("MYSQL_CHARSET", "utf8mb4")},
    )
    engine = create_engine(mysql_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def database_client(db_engine: Engine) -> DatabaseClient:
    """创建只执行项目内独立预期 SQL 的数据库 Client。"""

    return DatabaseClient(
        engine=db_engine,
        sql_directory=Path(__file__).parent / "sql",
    )
