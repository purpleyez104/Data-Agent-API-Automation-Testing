# Ecommerce Data Agent 接口文档

本文档依据 [`spec.md`](spec.md) 描述测试项目所依赖的 HTTP API Contract，用于接口联调、自动化测试设计和问题定位。

> 证据边界：Endpoint、请求模型和响应模型已与被测系统源码对照，并已在受控本地实例完成 MVP Runtime 回归。本文示例仅用于说明数据结构；已执行结果和剩余边界以本文第 9 节及 [`test-summary.md`](test-summary.md) 为准。

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 服务名称 | `Ecommerce Data Agent` |
| 默认 Base URL | `http://127.0.0.1:8000` |
| 数据格式 | `application/json` |
| OpenAPI UI | `/docs` |
| 当前 API 版本 | `0.1.0` |
| API 认证 | 当前未实现；调用接口无需提供 Token 或 API Key。数据库访问仍使用独立的只读账号控制权限 |

调用 `POST /query` 时应设置：

```http
Content-Type: application/json
```

## 2. 接口总览

| Method | Path | 用途 | 成功状态码 |
| --- | --- | --- | ---: |
| `GET` | `/` | 确认 HTTP 服务已启动，并获取文档入口 | `200` |
| `GET` | `/health` | 进程级健康检查 | `200` |
| `POST` | `/query` | 提交自然语言问题并返回查询结果 | `200` |

`GET /` 和 `GET /health` 只能证明 Web 进程能够响应，不代表 MySQL 或 LLM 可用。

## 3. `GET /`

### 3.1 请求

无 Query Parameter，无 Request Body。

```bash
curl http://127.0.0.1:8000/
```

### 3.2 `200 OK`

| 字段 | 类型 | 必有 | 说明 |
| --- | --- | --- | --- |
| `message` | `string` | 是 | 服务运行提示 |
| `docs` | `string` | 是 | OpenAPI UI 相对路径 |

```json
{
  "message": "Ecommerce Data Agent is running.",
  "docs": "/docs"
}
```

## 4. `GET /health`

### 4.1 请求

无 Query Parameter，无 Request Body。

```bash
curl http://127.0.0.1:8000/health
```

### 4.2 `200 OK`

| 字段 | 类型 | 必有 | 说明 |
| --- | --- | --- | --- |
| `status` | `string` | 是 | 当前固定为 `ok` |

```json
{
  "status": "ok"
}
```

## 5. `POST /query`

接收自然语言问题，完成问题路由、SQL 生成与校验、MySQL 查询和结果摘要。

### 5.1 Request Body

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `question` | `string` | 是 | 长度至少为 1 | 用户自然语言问题 |
| `today` | `string \| null` | 否 | 预期格式为 `YYYY-MM-DD` | 相对日期计算基准；不传时使用服务进程当天日期 |

`today` 对可重复测试十分重要。测试“最近 7 天”等相对日期问题时必须显式传入固定值。

```json
{
  "question": "最近7天 GMV 趋势",
  "today": "2026-05-31"
}
```

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"最近7天 GMV 趋势\",\"today\":\"2026-05-31\"}"
```

### 5.2 支持范围

#### 指标

| `metric_name` | 业务含义 |
| --- | --- |
| `gmv` | GMV / 成交额 |
| `paid_order_count` | 支付订单数 |
| `order_user_count` | 下单用户数 |
| `order_to_pay_rate` | 下单到支付转化率 |
| `top_product_by_rank` | 单日热门商品排行 |

#### 问题类型

| `question_type` | 业务含义 | 主要边界 |
| --- | --- | --- |
| `single_value` | 单日单指标查询 | 需要可解析的单日日期 |
| `trend` | 一段时间内的趋势查询 | 支持固定日期下最近 N 天等表达 |
| `comparison` | 最近 7 天与前 7 天对比 | 稳定范围为 GMV、支付订单数、下单用户数 |
| `topn` | 单日热门商品排行 | 必须显式给出 N，且 `1 <= N <= 10`，不支持跨日排行 |

当前稳定回归以确定性规则路径为主，不应依赖真实 LLM。白名单表为 `ads_gmv_day`、`ads_top_product`、`ads_user_conversion`。

### 5.3 `200 OK` Response Body

| 字段 | 类型 | 必有 | 说明 |
| --- | --- | --- | --- |
| `question` | `string` | 是 | 原始问题 |
| `metric_name` | `string \| null` | 是 | 识别出的指标名 |
| `question_type` | `string` | 是 | 识别出的问题类型 |
| `route` | `object` | 是 | 问题理解与路由详情 |
| `sql` | `string` | 是 | 生成的最终 SQL |
| `normalized_sql` | `string` | 是 | 经过本地校验和归一化的 SQL |
| `row_count` | `integer` | 是 | `data` 的结果行数 |
| `columns` | `string[]` | 是 | 结果字段名，顺序与查询结果一致 |
| `data` | `object[]` | 是 | 查询结果行 |
| `summary` | `string` | 是 | 面向用户的中文结果摘要 |

字段关系：

- `row_count` 应等于 `data` 数组长度。
- `data` 每行的 Key 应与 `columns` 对应。
- `sql` 与 `normalized_sql` 都只能表达受控的只读查询；实际执行的是通过校验后的 `normalized_sql`。
- 无数据属于成功查询时，可返回 `200`、`row_count: 0`、空 `data` 和无结果摘要。

#### `route` Object

| 字段 | 类型 | 必有 | 说明 |
| --- | --- | --- | --- |
| `intent` | `string` | 是 | 高层意图 |
| `metric_name` | `string \| null` | 是 | 路由阶段识别出的指标 |
| `question_type` | `string` | 是 | 路由阶段识别出的问题类型 |
| `time_mode` | `string` | 是 | 时间解析模式 |
| `topn` | `integer \| null` | 是 | TopN 值；非排行问题通常为 `null` |
| `use_rule_based` | `boolean` | 是 | 是否使用规则 SQL 路径 |
| `need_llm_sql` | `boolean` | 是 | 是否需要 LLM 生成 SQL |
| `unsupported_reason` | `string \| null` | 是 | 不支持原因；成功响应通常为 `null` |
| `time_context` | `object` | 是 | 已解析的时间范围 |

`time_mode` 的已知值：

| 值 | 含义 |
| --- | --- |
| `single_day` | 单日查询 |
| `last_n_days` | 最近 N 天趋势 |
| `last_7_vs_prev_7` | 最近 7 天与前 7 天对比 |
| `single_day_topn` | 单日 TopN |
| `unknown` | 时间范围未识别或问题不支持 |

`time_context` 会随问题类型变化。单日或趋势通常包含 `start_date`、`end_date`；对比问题还可能包含当前周期和前一周期的边界字段。调用方不应假设所有问题类型具有完全相同的 Key 集合。

### 5.4 成功响应结构示例

以下内容仅展示 Contract 结构，业务值不是已执行证据。

```json
{
  "question": "查询 2026-05-31 的 GMV",
  "metric_name": "gmv",
  "question_type": "single_value",
  "route": {
    "intent": "single_value",
    "metric_name": "gmv",
    "question_type": "single_value",
    "time_mode": "single_day",
    "topn": null,
    "use_rule_based": true,
    "need_llm_sql": false,
    "unsupported_reason": null,
    "time_context": {
      "start_date": "2026-05-31",
      "end_date": "2026-05-31"
    }
  },
  "sql": "SELECT dt, gmv FROM ads_gmv_day WHERE dt = '2026-05-31';",
  "normalized_sql": "SELECT dt, gmv FROM ads_gmv_day WHERE dt = '2026-05-31';",
  "row_count": 1,
  "columns": ["dt", "gmv"],
  "data": [
    {
      "dt": "2026-05-31",
      "gmv": 100000.00
    }
  ],
  "summary": "2026-05-31 的GMV为 100000.00。"
}
```

## 6. 错误响应

错误响应遵循 FastAPI 的 `detail` 结构，但 `detail` 的类型取决于错误来源。

### 6.1 `400 Bad Request`

业务输入不受支持，或生成 SQL 未通过安全与业务规则校验时返回。

典型场景：

- 未识别出支持的指标；
- TopN 问题没有显式给出 N；
- `N > 10`；
- 请求跨日商品排行；
- 请求当前不支持的解释类问题；
- SQL 使用非白名单表、字段或不满足只读边界。

```json
{
  "detail": "当前版本仅支持 Top10 以内的单日热门商品排行查询。"
}
```

### 6.2 `422 Unprocessable Entity`

Request Body 无法通过 FastAPI/Pydantic 请求模型校验时返回，例如：

- 缺少 Request Body；
- 缺少 `question`；
- `question` 为空字符串；
- 字段类型不符合模型要求。

`detail` 为校验错误数组，数组元素的精确字段可能随 FastAPI/Pydantic 版本变化。自动化测试应优先断言状态码、错误位置和错误类型，不应绑定整段错误文案。

结构示例：

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### 6.3 `500 Internal Server Error`

未被业务错误处理覆盖的服务内部异常，例如 MySQL 连接或 SQL 执行失败。

```json
{
  "detail": "服务内部错误: ..."
}
```

当前实现可能把底层异常文本放入 `detail`。测试和报告不得记录密码、API Key 或完整数据库连接 URL；若 Runtime 响应泄露 Secret，应作为缺陷处理。

### 6.4 待 Runtime 确认的边界

以下行为不能仅凭 Spec 或静态源码认定，测试时应以实际响应为准：

- 全空格 `question` 最终返回 `400` 还是其他业务结果；
- 非法日期和无数据日期的具体 `detail` 文案；
- JSON 类型转换在当前 Pydantic 版本下是否被接受；
- MySQL、LLM 或其他依赖故障对应的具体 `500` 文案；
- 不受支持的 HTTP Method 是否返回 `405` 及其响应头。

## 7. 数据与序列化约定

- 测试数据的已验证日期范围为 `2026-03-01` 至 `2026-05-31`。
- 日期在 JSON 中以 `YYYY-MM-DD` 字符串表示。
- 金额、比率等数据库 `Decimal` 值经过 JSON 序列化后可能表现为 JSON Number；调用方不应使用二进制浮点误差判断财务值。
- `columns` 和 `data` 的具体字段由问题类型决定。数据对账需同时验证日期范围、行数、字段值、精度、排序、排名和汇总计算。
- 不得重新执行响应中的 `sql` 并把结果称为独立数据正确性验证；预期结果必须来自独立维护的只读 SQL。

## 8. 调用与测试约束

- MVP 稳定回归使用规则路径，不依赖真实 LLM。
- 相对日期请求必须固定 `today`，避免测试结果随系统日期漂移。
- TopN 仅支持单日 Top1 至 Top10，并应按 `rank_no ASC` 返回。
- API 只允许访问三张白名单表，不应执行 `INSERT`、`UPDATE`、`DELETE`、DDL 或多语句 SQL。
- 自动化测试应验证 Status Code、`Content-Type`、Response JSON、字段类型和字段关系，并为失败保留必要的请求、响应及数据差异。

## 9. 当前验证状态

| 项目 | 状态 |
| --- | --- |
| Endpoint 与 Schema 静态对照 | 已完成文档编写所需对照 |
| `GET /` Runtime | `PASS`（受控本地实例，2026-10-26） |
| `GET /health` Runtime | `PASS`（受控本地实例，2026-10-26） |
| `POST /query` Runtime | `PASS`（固定日期 GMV 规则路径，2026-10-26） |
| `400`、`422` 和 `405` 错误语义 | `PASS`（受控本地实例，2026-10-26） |
| `500` 依赖故障语义 | `not_run` |
| 成功响应与 MySQL 独立对账 | `PASS`（五个场景，2026-10-26） |

完整 MVP Regression 结果为 `35 passed, 2 xfailed in 0.77s`。两条预期失败对应跨日 TopN 静默降级和写入意图未受控拒绝，详见 [`test-summary.md`](test-summary.md) 与 [`bug-reports.md`](bug-reports.md)。
