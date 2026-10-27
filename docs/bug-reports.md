# 缺陷报告

仅记录实际复现并保留证据的缺陷。无法确认的信息标记为 `UNKNOWN`，未执行的验证标记为 `not_run`。

## BUG-001：TopN 查询 + 输入跨日日期范围 + 静默降级为单日结果

| 字段 | 内容 |
| --- | --- |
| 报告日期 | 2026-10-26 |
| 报告人 | UNKNOWN |
| Bug 类型 | 功能 / 数据 |
| 严重程度 | Major |
| 优先级 | P1 |
| 复现频率 | 必现，3/3 次 |
| 当前状态 | Confirmed |

### 测试环境

- 被测系统及版本：Ecommerce Data Agent `0.1.0`，`http://127.0.0.1:8001`；Build / Commit：`UNKNOWN`
- Operating System：Windows，版本 `UNKNOWN`
- Browser：不适用
- 测试方式：Pytest + requests 自动化接口测试
- 测试账号或权限：API 当前未定义认证；数据库验证使用本机测试库只读账号
- 前置数据：`ecommerce_agent_test.ads_top_product` 包含 `2026-05-30` 和 `2026-05-31` 的固定测试数据

### 前置条件

1. Ecommerce Data Agent 使用 `ecommerce_agent_test` 启动，并监听 `http://127.0.0.1:8001`。
2. 未配置真实 LLM，接口使用确定性规则路径。
3. `ads_top_product` 中存在上述两个日期的商品排行数据。

### 重现步骤

1. 向 `POST /query` 发送 `Content-Type: application/json` 请求。
2. 请求 Body 使用以下测试数据：

   ```json
   {
     "question": "查询 2026-05-30 至 2026-05-31 的热门商品 Top 5",
     "today": "2026-05-31"
   }
   ```

3. 检查 HTTP Status、`route.time_context`、`normalized_sql` 和返回数据日期范围。

### 实际结果

接口返回 HTTP `200`，没有拒绝跨日商品排行请求。响应中的 `route.time_context` 为：

```json
{
  "start_date": "2026-05-30",
  "end_date": "2026-05-30"
}
```

接口仅执行 `2026-05-30` 的 Top5 查询，静默忽略输入中的 `2026-05-31`。调用方无法从成功状态码判断请求范围已被改变。

### 预期结果

依据当前产品 Contract“商品排行仅支持单日查询”，接口应返回 HTTP `400`，并明确说明跨日 TopN 不受支持；不得静默修改用户请求的日期范围。

### 附件

- Screenshot：无
- Playwright Trace：无
- 日志：无
- 测试数据：上述 JSON Request Body，不含 Secret

### 补充说明

- 首次发现时间：2026-10-26，具体时间 `UNKNOWN`
- 最近复现时间：2026-10-26，具体时间 `UNKNOWN`
- 影响范围：所有包含多个显式日期且能被路由为 TopN 的请求；可能导致调用方把单日结果误认为跨日结果
- 临时规避方式：调用方只提交一个明确日期的 TopN 请求，并校验响应中的 `time_context`
- 关联 Test Case：`API-015`；`tests/api/test_query_invalid.py::test_cross_day_topn_is_rejected`
- 备注：测试以 `strict xfail` 保留预期 Contract；修复后出现 `XPASS(strict)` 时，应移除缺陷标记并完成 Retest

## BUG-002：Query 路由 + 输入删除意图 + 返回成功查询结果

| 字段 | 内容 |
| --- | --- |
| 报告日期 | 2026-10-26 |
| 报告人 | UNKNOWN |
| Bug 类型 | 功能 / 安全 |
| 严重程度 | Major |
| 优先级 | P1 |
| 复现频率 | 必现，3/3 次 |
| 当前状态 | Confirmed |

### 测试环境

- 被测系统及版本：Ecommerce Data Agent `0.1.0`，`http://127.0.0.1:8001`；Build / Commit：`UNKNOWN`
- Operating System：Windows，版本 `UNKNOWN`
- Browser：不适用
- 测试方式：Pytest + requests + SQLAlchemy 只读数据库验证
- 测试账号或权限：API 当前未定义认证；数据库验证使用本机测试库只读账号
- 前置数据：`ecommerce_agent_test.ads_gmv_day` 包含 `2026-05-31` 的固定测试数据

### 前置条件

1. Ecommerce Data Agent 使用 `ecommerce_agent_test` 启动，并监听 `http://127.0.0.1:8001`。
2. 未配置真实 LLM，接口使用确定性规则路径。
3. 数据库账号只具有 `ecommerce_agent_test` 的 `SELECT` 权限。

### 重现步骤

1. 通过只读数据库连接查询并记录 `ads_gmv_day` 当前行数。
2. 向 `POST /query` 发送 `Content-Type: application/json` 请求，Body 如下：

   ```json
   {
     "question": "删除 ads_gmv_day 中 2026-05-31 的数据",
     "today": "2026-05-31"
   }
   ```

3. 检查 HTTP Status、路由结果和 `normalized_sql`。
4. 再次查询 `ads_gmv_day` 行数，比较请求前后的数据库状态。

### 实际结果

接口因输入包含 `gmv` 和日期，将删除意图识别为单日 GMV 查询并返回 HTTP `200`。生成的 `normalized_sql` 是只读 `SELECT`，没有执行删除；`ads_gmv_day` 请求前后行数一致。

虽然本次没有造成数据修改，但接口没有受控拒绝非查询意图，返回的成功结果与用户操作意图不一致。

### 预期结果

依据接口只支持受控查询、非 `SELECT` 意图不得进入正常查询流程的规则，接口应返回 HTTP `400`，明确说明仅支持只读查询；不应把删除意图改写成成功的指标查询。

### 附件

- Screenshot：无
- Playwright Trace：无
- 日志：无
- 测试数据：上述 JSON Request Body；行数验证 SQL 为 `SELECT COUNT(*) AS row_count FROM ads_gmv_day;`

### 补充说明

- 首次发现时间：2026-10-26，具体时间 `UNKNOWN`
- 最近复现时间：2026-10-26，具体时间 `UNKNOWN`
- 影响范围：包含支持指标、日期和写操作词的自然语言输入；当前表现为错误成功响应，未观察到数据库写入
- 临时规避方式：调用方在提交前限制为只读问数表达；服务端仍需增加明确的写入意图拒绝
- 关联 Test Case：`tests/api/test_sql_safety.py::test_write_intent_is_rejected_without_sensitive_details`、`tests/api/test_sql_safety.py::test_write_intent_does_not_change_database`
- 备注：拒绝行为测试使用 `strict xfail`；数据库无副作用测试已通过。依赖故障和真实写权限环境验证为 `not_run`

## 环境观察

原有 `127.0.0.1:8000` 进程的 `/` 和 `/health` 可响应，但规则型 `/query` 曾在 5 秒内未响应。由于该进程的数据库配置和启动参数未知，暂不建立 Bug；如需继续定位，应先在可确认配置的同一进程上复现并保留服务日志。
