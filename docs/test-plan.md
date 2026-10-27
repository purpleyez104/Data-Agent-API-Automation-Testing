# 测试计划

本计划依据 [`spec.md`](spec.md) 的 Scope、Acceptance Criteria 和 Verification，按风险从最小核心链路逐步扩展。

## 1. 当前阶段：Smoke

目标：确认测试库、FastAPI 进程和一条确定性规则查询具备继续开展接口测试的基本条件。

| 用例 | 验证点 | 状态 |
| --- | --- | --- |
| `SMOKE-DB-001` | 只读账号连接指定测试库，三张核心 ADS 表均有数据 | `PASS` |
| `SMOKE-API-001` | `GET /` 返回服务入口 Contract | `PASS` |
| `SMOKE-API-002` | `GET /health` 返回进程健康状态 | `PASS` |
| `SMOKE-API-003` | 固定日期 GMV 请求走规则路径并查询 MySQL | `PASS` |

退出条件：四条用例全部通过，且请求与日志不包含 Secret。该条件已于 `2026-10-26` 在受控 `8001` 实例满足。

## 2. 执行约定

- HTTP 用例按模块封装在 `TestSmoke` Class 中。
- 同一 Class 使用 `requests.session()` 复用 HTTP 连接，并在 `teardown_class()` 中关闭。
- 相对日期请求显式传入固定 `today`。
- 数据库检查只使用 `data_agent_test_user` 的 `SELECT` 权限。
- 用例独立断言，不依赖执行顺序。

## 3. 测试架构

Pytest 是自动化回归主入口，Postman 仅用于手工联调和请求探索。MVP 不建设通用测试框架，也不引入 BaseTest 继承体系、Allure、Docker 或 CI。

```text
clients/
├── api_client.py             # HTTP Session、Base URL、Timeout
└── database_client.py        # 只读 SQL 查询
tests/
├── smoke/                    # 最小核心链路
├── api/
│   ├── test_contract.py
│   ├── test_query_success.py
│   ├── test_query_invalid.py
│   └── test_sql_safety.py
└── data_validation/
    └── test_query_results.py
sql/                         # 独立维护的预期 SQL
test_data/                   # 不含 Secret 的参数化输入
```

### 3.1 Client 与 Fixture 边界

- `ApiClient` 负责 URL 拼接、连接复用、Timeout 和公开 Endpoint 调用，不负责业务断言。
- 数据库 Client 只使用只读账号执行人工确认的预期 SQL，不复用 API 返回的 SQL。
- HTTP Session 和数据库 Engine 使用 Session Scope Fixture，并在测试会话结束后释放。
- 测试断言保留在对应测试模块中，避免 Client 隐藏失败原因。

## 4. 测试分层

### 4.1 API Contract

验证 Status Code、`Content-Type`、必需字段、字段类型及以下字段关系：

- `row_count == len(data)`；
- `data` 每行 Key 与 `columns` 对应；
- 顶层 `metric_name`、`question_type` 与 `route` 中的值一致；
- 规则回归中 `use_rule_based` 为 `true`、`need_llm_sql` 为 `false`；
- `normalized_sql` 为单条只读 `SELECT`，且仅访问白名单表；
- 相对日期解析结果与显式传入的固定 `today` 一致。

MVP 使用 Python 直接断言，不新增 JSON Schema Dependency。

### 4.2 功能与输入边界

| ID | 场景 | 核心预期 | 状态 |
| --- | --- | --- | --- |
| `API-001` | 单日 GMV | `single_value`，返回一日结果 | `PASS` |
| `API-002` | 单日支付订单数 | 指标、字段和来源表正确 | `PASS` |
| `API-003` | 单日下单用户数 | 查询用户转化结果 | `PASS` |
| `API-004` | 单日支付转化率 | 数值与精度正确 | `PASS` |
| `API-005` | 最近 7 天 GMV 趋势 | 固定日期范围、升序、7 行 | `PASS` |
| `API-006` | 最近 7 天与前 7 天 GMV 对比 | 两个周期边界和汇总正确 | `PASS` |
| `API-007` | 单日 Top1 | 1 行且 `rank_no=1` | `PASS` |
| `API-008` | 单日 Top5 | 5 行且排名升序 | `PASS` |
| `API-009` | 单日 Top10 | 10 行且排名升序 | `PASS` |
| `API-010` | “成交额”同义表达 | 识别为 `gmv` | `PASS` |
| `API-011` | 合法但无数据日期 | `200`、空数据和无结果摘要 | `PASS` |
| `API-012` | 未知指标 | `400` 受控拒绝 | `PASS` |
| `API-013` | TopN 缺少 N | `400` 受控拒绝 | `PASS` |
| `API-014` | Top11 | `400` 受控拒绝 | `PASS` |
| `API-015` | 跨日商品排行 | `400` 受控拒绝 | `XFAIL / BUG-001` |
| `API-016` | 缺少 `question` | `422`，定位请求字段 | `PASS` |
| `API-017` | `question` 为空字符串 | `422` | `PASS` |
| `API-018` | `question` 全空格 | 受控拒绝 | `PASS` |
| `API-019` | 非法 `today` | `400` 受控拒绝 | `PASS` |
| `API-020` | 不支持的 HTTP Method | `405` Contract | `PASS` |

相同断言结构的单指标成功场景使用 `pytest.mark.parametrize`；Comparison、TopN、数据对账和安全场景保留独立测试，避免巨大参数表掩盖业务差异。

### 4.3 MySQL 独立数据对账

至少维护以下五份预期查询：

1. 单日 GMV；
2. 单日支付订单数；
3. 最近 7 天 GMV 趋势；
4. 最近 7 天与前 7 天 GMV 对比；
5. 单日热门商品 Top5。

预期查询独立存放在 `sql/`，不得执行 API 返回的 `sql` 或 `normalized_sql` 作为正确性依据。对账统一日期和 `Decimal` 表示，并比较日期范围、Columns、行数、值、顺序、排名及汇总计算。

### 4.4 SQL 安全边界

- 写入、DDL 或多语句意图不得造成数据库变化；
- 未知指标、跨日 TopN 和非白名单资源请求应受到受控拒绝；
- 未配置 LLM 时，需要 LLM 的请求应受控失败；
- 响应、断言消息和测试 Artifact 不得包含密码、API Key 或完整数据库连接 URL；
- 测试结论仅说明公开接口行为与只读权限，不描述为完整渗透测试或安全认证。

当前写入意图未被受控拒绝，登记为 `BUG-002`；独立副作用检查确认请求前后 `ads_gmv_day` 行数一致。

## 5. Marker 与执行入口

计划使用以下 Marker：

- `smoke`：最小核心链路；
- `contract`：HTTP 与 Response Contract；
- `functional`：核心业务功能；
- `boundary`：输入和业务边界；
- `data_validation`：API 与 MySQL 独立对账；
- `safety`：SQL 和敏感信息边界。

```powershell
python -m pytest tests/smoke -q
python -m pytest -m "contract or functional or boundary" -q
python -m pytest -m data_validation -q
python -m pytest -m "not smoke" -q
python -m pytest -q
```

六类 Marker 均已实现并进入完整回归。当前结果为 `35 passed, 2 xfailed`；`xfail` 对应已登记产品缺陷，不代表测试未执行。

## 6. 实施顺序

```text
共享 ApiClient 与 Fixture
→ /、/health、/query Contract Test
→ 四类核心成功场景
→ 400、422 与 TopN 边界
→ 五个 MySQL 独立数据对账
→ 最小 SQL 安全边界
→ MVP Regression
```

以上 MVP 实施步骤均已完成并执行。依赖故障注入和 `500` Runtime 语义不在本次已执行证据内，保持 `not_run`。
