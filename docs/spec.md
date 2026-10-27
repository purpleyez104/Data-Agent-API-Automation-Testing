# Data Agent API Automation Testing 项目规格 V1.0

## 1. Goal

从独立测试人员视角，为 Ecommerce Data Agent 的运行中 HTTP API 建立可重复执行的自动化回归，展示 API Contract 验证、功能与边界测试设计、MySQL 数据对账、SQL 执行边界验证以及缺陷定位能力。最终成果达到 Portfolio Quality：可运行、可复现、可讲解，所有结论来自真实执行。

## 2. Users / Use Cases

- 求职者通过项目证明初级软件测试、接口测试与自动化测试能力。
- 面试官可以根据 README 在本地复现核心回归并检查测试证据。
- 测试人员可以对规则路径执行稳定回归，对关键业务指标执行独立数据对账。

## 3. System Under Test

被测系统为独立 Repository 中运行的 Ecommerce Data Agent。本 Repository 不包含被测应用源码，通过 HTTP 访问服务，并通过只读账号查询同一测试数据库。

### 3.1 API Contract

| Method | Path | 用途 |
| --- | --- | --- |
| `GET` | `/` | 服务入口 |
| `GET` | `/health` | 进程级健康检查，不代表 MySQL 或 LLM 健康 |
| `POST` | `/query` | 自然语言问数 |

`POST /query` 成功响应重点验证：`question`、`metric_name`、`question_type`、`route`、`sql`、`normalized_sql`、`row_count`、`columns`、`data`、`summary`。

### 3.2 Supported Domain

- 查询类型：`single_value`、`trend`、`comparison`、`topn`。
- 指标：GMV、支付订单数、下单用户数、下单到支付转化率、单日热门商品 TopN。
- 白名单表：`ads_gmv_day`、`ads_top_product`、`ads_user_conversion`。

## 4. Scope

### 4.1 API Contract Test

- 验证 HTTP Method、Status Code、`Content-Type`、Request Body 和 Response JSON。
- 验证成功响应的必需字段、数据类型及字段关系。
- 验证 `400`、`422`、`500` 的实际错误语义，不预设未运行行为。

### 4.2 Functional and Boundary Test

- 单日指标：GMV、支付订单数、下单用户数、下单到支付转化率。
- 趋势：固定日期下最近 N 天的 GMV 或用户数变化。
- 对比：最近 7 天与前 7 天对比。
- TopN：单日 Top1、Top5、Top10，以及缺少 N、N 大于 10、跨日排行。
- 输入边界：缺少字段、空字符串、全空格、类型错误、非法或无数据日期、未知指标和不支持问题。
- 同义表达：至少覆盖 GMV 与成交额等已支持问法。

### 4.3 Data Validation

使用人工确认、独立维护的 MySQL 查询对比 API 结果，至少覆盖：

1. 单日 GMV；
2. 单日支付订单数；
3. 最近 7 天 GMV 趋势；
4. 最近 7 天与前 7 天 GMV 对比；
5. 单日热门商品 Top5。

对账验证日期范围、行数、字段值、Decimal 精度、排序、排名和汇总计算。不得直接重新执行 API 返回的 SQL 并将其称为独立正确性验证。

### 4.4 Input Safety and SQL Execution Boundary

- 验证不支持请求受到受控拒绝。
- 验证非 `SELECT` 意图不能导致数据库写入。
- 验证表白名单、字段白名单和 TopN 限制的外部行为。
- 验证错误响应与测试证据不泄露密码或 API Key。
- 本项目不将这些检查描述为完整渗透测试或生产安全认证。

### 4.5 Regression Boundary

- MVP 回归以确定性规则路径为主，不依赖真实 LLM。
- 相对日期问题必须显式传入固定 `today`。
- 测试独立执行，不依赖用例顺序。
- 失败时保存必要的请求、响应和数据差异。

## 5. Test Environment and Data Contract

### 5.1 MySQL

| 配置 | 值 |
| --- | --- |
| Host | `127.0.0.1` |
| Port | `3306` |
| Database | `ecommerce_agent_test` |
| Test User | `data_agent_test_user` |
| Permission | `SELECT` on `ecommerce_agent_test.*` |
| Character Set | `utf8mb4` |

本地测试账号当前为空密码，只允许用于本机隔离环境，不得用于远程、共享或发布环境。

### 5.2 Verified Dataset

| 表 | 行数 | 日期范围 | 状态 |
| --- | ---: | --- | --- |
| `ads_gmv_day` | 92 | 2026-03-01 至 2026-05-31 | `VERIFIED` |
| `ads_top_product` | 920 | 2026-03-01 至 2026-05-31 | `VERIFIED` |
| `ads_user_conversion` | 92 | 2026-03-01 至 2026-05-31 | `VERIFIED` |

已验证三张表无关键字段 `NULL`、无候选主键重复、`dt` 长度为 10，抽查数据与 Tab 分隔且无 Header 的源 CSV 一致。`ads_category_top` 不在被测系统白名单中，不纳入 MVP。

## 6. Constraints

- 被测应用与测试项目保持独立 Repository，不复制应用内部实现作为测试代码。
- 数据库自动化仅使用 `data_agent_test_user` 的只读权限。
- `.env`、密码、API Key、完整连接 URL 和生成的测试证据不得提交 Git。
- 不为方便测试而改变被测系统业务 Contract；发现缺陷后先保留证据。
- 测试实现保持最小充分，不建设通用自动化框架。
- 未运行的 Test、Build、API 或 Runtime 检查必须标记为 `not_run`。

## 7. Non-goals

- Web UI 自动化、Selenium 或 Playwright。
- 性能、并发、移动端、完整渗透或生产安全测试。
- 真实 LLM 输出稳定性回归和外部依赖故障注入。
- 自研测试平台、通用测试框架、多环境部署或完整数仓恢复。
- MVP 阶段的 Allure、GitHub Actions、Docker Compose。
- `ads_category_top` 测试和被测系统功能扩展。

## 8. Technology Stack

- Python 3.12
- Pytest
- requests
- SQLAlchemy
- PyMySQL
- python-dotenv
- MySQL 8.0
- Pytest Fixture 与 `pytest.mark.parametrize`
- Postman、MySQL Workbench 仅作为手工辅助工具

### 8.1 Test Architecture

- Pytest 是自动化执行与回归的唯一主入口，Postman 不作为 MVP 通过条件。
- `clients/api_client.py` 负责 Base URL、HTTP Session 和 Timeout，不包含业务断言。
- `clients/database_client.py` 仅封装只读查询，不计算或隐藏业务预期。
- `tests/api/` 按 Contract、核心功能、输入边界、TopN 和 SQL 安全边界拆分。
- `tests/data_validation/` 使用 `sql/` 中独立维护的预期 SQL 完成数据对账。
- 金额与比率使用 `Decimal` 语义比较；趋势和排行同时验证范围、行数、顺序与字段值。
- 不为 MVP 引入 BaseTest 继承体系、Allure、自研测试平台、Docker 或 CI。

## 9. Acceptance Criteria

1. 被测系统和测试 Repository 的职责边界清晰。
2. 被测系统能够连接 `ecommerce_agent_test`，测试代码使用只读账号查询。
3. `/`、`/health`、`/query` 的实际 Contract 得到自动化验证。
4. 四类核心查询至少各有一个成功场景。
5. 关键输入异常和 TopN 边界得到验证。
6. 至少五个场景完成独立 MySQL 数据对账。
7. 相对日期测试显式使用固定 `today`。
8. 测试之间不存在执行顺序依赖。
9. MVP 稳定回归不依赖真实 LLM。
10. 单个命令可以运行 MVP 测试。
11. 失败信息足以定位请求、响应或数据差异，且不泄露 Secret。
12. README 提供可复现的准备与运行步骤。
13. 测试总结和缺陷报告只记录真实执行结果。
14. MVP 不存在阻塞核心回归的已知 Flaky Test。

## 10. Verification

按以下顺序选择最小充分验证：

```text
数据库只读连接 Smoke
→ API 启动 Smoke
→ Targeted API Test
→ 数据一致性 Test
→ MVP Regression
```

最终证据必须包含实际 Pytest 结果、核心查询真实响应、MySQL 对账结果、异常状态码与响应、环境和数据版本，以及 Acceptance Criteria 到证据的映射。无法执行的检查保持 `not_run` 或 `UNKNOWN`。

## 11. Current Status

### VERIFIED

- MySQL Server、`ecommerce_agent_test` 和只读账号可连接。
- 只读账号仅有测试库的 `SELECT` 权限。
- 三张白名单表的行数、日期范围、空值、候选主键和样例数据通过只读验收。
- 受控本地实例的 `/`、`/health` 和固定日期 GMV 规则查询 Smoke 已于 `2026-10-26` 通过，结果为 `4 passed in 0.32s`。
- API Contract、四类规则查询、输入与 TopN 边界、五项 MySQL 独立数据对账和最小 SQL 安全边界已执行。
- 完整 MVP Regression 结果为 `35 passed, 2 xfailed in 0.77s`；两条预期失败已登记为 `BUG-001` 和 `BUG-002`。
- 写入意图虽然未被受控拒绝，但实际 SQL 保持只读，测试前后 `ads_gmv_day` 行数未变化。

### not_run

- MySQL 或其他依赖故障对应的 `500` Runtime 错误语义。

## 12. Decisions and Open Questions

### Confirmed Decisions

- 项目一聚焦 API 与 MySQL 数据测试，项目二独立承担 UI 自动化。
- 固定 CSV 数据已导入独立测试库，自动化使用只读账号。
- 仅覆盖 Data Agent 当前三张白名单表。
- 规则路径是稳定回归主干，真实 LLM 不是 MVP 依赖。
- 不以测试用例数量或工具数量作为质量指标。
- 采用“Contract、功能与边界、MySQL 独立对账、SQL 安全边界”四层测试结构。
- HTTP 与数据库 Client 只封装访问行为，断言保留在测试中以保证失败可定位。
- 测试按 `smoke`、`contract`、`functional`、`boundary`、`data_validation`、`safety` 分组。

### Open Questions

- 无阻塞实现的 `DECISION_REQUIRED`。报告格式和后置增强项在 MVP 稳定后按目标 JD 决定。
