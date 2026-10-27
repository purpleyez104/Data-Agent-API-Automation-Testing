# Data Agent API Automation Testing

面向 Ecommerce Data Agent 的独立 API 自动化测试项目，重点验证 API Contract、自然语言输入边界、SQL 执行边界和 MySQL 数据一致性。

当前已完成 MVP API 自动化回归，正式范围与验收标准见 [`docs/spec.md`](docs/spec.md)。回归覆盖 API Contract、核心功能、输入与 TopN 边界、五项 MySQL 独立数据对账和最小 SQL 安全边界。

## 测试设计

本项目以 Pytest 作为自动化回归主入口，Postman 仅用于手工联调和请求探索。MVP 按以下四层组织：

1. API Contract：验证 HTTP 状态、响应格式、字段类型和字段关系。
2. 功能与边界：验证四类核心查询、输入校验和 TopN 约束。
3. 数据对账：使用独立维护的只读 SQL 对比 API 与 MySQL 结果。
4. SQL 安全边界：验证不支持请求、只读行为和敏感信息保护。

详细用例矩阵、Fixture 设计和实施顺序见 [`docs/test-plan.md`](docs/test-plan.md)。

## 目录

- `tests/api/`：HTTP Contract、功能、异常与边界测试。
- `tests/data_validation/`：API 返回值与独立 MySQL 查询的对账测试。
- `tests/smoke/`：最小核心链路检查。
- `clients/`：必要的 HTTP 和只读数据库访问封装。
- `sql/`：人工确认的 MySQL 预期查询。
- `test_data/`：参数化测试数据。
- `artifacts/`：本地测试报告和失败证据，不提交生成内容。
- `docs/`：正式规格与后续测试文档。
- [`测试用例及执行记录.xlsx`](测试用例及执行记录.xlsx)：37 条实际收集用例的设计与执行记录，包含 35 条 `PASS` 和 2 条已关联 Bug 的 `XFAIL`。
- [`docs/bug-reports.md`](docs/bug-reports.md)：`BUG-001`、`BUG-002` 的标准化缺陷报告。

## 当前证据边界

- 测试数据库及三张 ADS 表已完成只读验收。
- 受控测试实例的 `/`、`/health` 和规则型 `/query` 冒烟链路已于 `2026-10-26` 执行通过，结果为 `4 passed in 0.32s`。
- 完整 MVP Regression 已于 `2026-10-26` 在受控 `8001` 实例执行，结果为 `35 passed, 2 xfailed in 0.77s`。
- 两条 `xfail` 分别对应跨日 TopN 被静默降级为首日查询，以及写入意图未受到受控拒绝；后者实际生成只读 SQL，数据库行数前后未变化。
- MySQL 或其他依赖故障对应的 `500` Runtime 语义仍为 `not_run`。

## 运行冒烟测试

前置条件：MySQL 测试库已启动，被测 API 使用 `ecommerce_agent_test` 和只读账号启动。

```powershell
$env:BASE_URL='http://127.0.0.1:8001'
python -m pytest tests/smoke -q
```

HTTP 用例在 `TestSmoke` 中通过 `requests.session()` 复用连接。Base URL 和数据库配置可通过 `.env` 或当前进程环境变量覆盖，字段示例见 [`.env.example`](.env.example)。

完整回归使用共享 `ApiClient` Fixture，并支持以下分组入口：`smoke`、`contract`、`functional`、`boundary`、`data_validation` 和 `safety`。
