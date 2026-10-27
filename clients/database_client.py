"""只读测试数据库访问封装。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Engine


class DatabaseClient:
    """执行人工维护的只读预期 SQL 并返回字典行。"""

    def __init__(self, engine: Engine, sql_directory: Path) -> None:
        self.engine = engine
        self.sql_directory = sql_directory

    def query_file(
        self,
        filename: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """读取并执行 SQL 文件。

        Args:
            filename: `sql/` 下的文件名，不允许目录穿越。
            parameters: SQLAlchemy 命名绑定参数。

        Returns:
            由列名映射到数据库值的结果行。

        Raises:
            ValueError: SQL 文件不在指定目录内，或不是单条 SELECT。
        """

        sql_path = (self.sql_directory / filename).resolve()
        if sql_path.parent != self.sql_directory.resolve():
            raise ValueError(f"SQL 文件必须位于 {self.sql_directory}")

        statement = sql_path.read_text(encoding="utf-8").strip()
        normalized = statement.rstrip(";").strip()
        if not normalized.upper().startswith("SELECT") or ";" in normalized:
            raise ValueError("预期 SQL 必须是单条 SELECT")

        with self.engine.connect() as connection:
            result = connection.execute(text(statement), dict(parameters or {}))
            return [dict(row) for row in result.mappings().all()]
