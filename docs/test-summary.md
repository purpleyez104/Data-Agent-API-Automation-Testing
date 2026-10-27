# 测试总结

## 2026-10-26 Smoke

### 环境

- API：受控本地实例 `http://127.0.0.1:8001`
- Database：`ecommerce_agent_test`，只读账号 `data_agent_test_user`
- LLM：未配置，规则路径不依赖真实 LLM
- Dataset：`2026-03-01` 至 `2026-05-31` 的固定测试数据

### 命令与结果

```powershell
$env:BASE_URL='http://127.0.0.1:8001'
python -m pytest tests/smoke -q
```

```text
4 passed in 0.32s
```

### 结论

- 数据库只读连接、`GET /`、`GET /health` 和固定日期 GMV 规则查询通过。
- 三个 HTTP 请求由同一个 `requests.session()` 发出，服务日志显示复用同一客户端连接端口。
- Smoke Gate 通过，可以进入 Targeted API Test。

### 证据边界

- 本次结果只覆盖 4 条冒烟用例，不代表完整 MVP Regression。
- `400`、`422`、`500`、输入边界、TopN 边界和独立 MySQL 对账仍为 `not_run`。
- 原有 `127.0.0.1:8000` 进程的 `/query` 曾在 5 秒内未响应；由于其启动配置未知，当前只记录为环境观察，不认定为产品缺陷。

## 2026-10-26 MVP Regression

### 环境

- API：受控本地实例 `http://127.0.0.1:8001`
- Database：`ecommerce_agent_test`，只读账号 `data_agent_test_user`
- LLM：未配置，回归仅覆盖确定性规则路径
- Dataset：`2026-03-01` 至 `2026-05-31` 的固定测试数据

### 命令与结果

```powershell
$env:BASE_URL='http://127.0.0.1:8001'
python -m pytest -q
```

```text
35 passed, 2 xfailed in 0.77s
```

另有以下 Targeted Verification：

- 测试收集：`37 tests collected in 0.05s`；
- Smoke：`4 passed in 0.22s`；
- 五项 MySQL 独立数据对账：`5 passed in 0.20s`。

### 结论

- `/`、`/health` 和 `/query` 的成功 Contract、核心规则查询及主要 `400`、`422`、`405` 边界通过。
- 单日 GMV、单日支付订单数、7 天 GMV 趋势、14 天 GMV 对比源数据、单日 Top5 均与独立 SQL 查询一致。
- 成功响应生成的 SQL 均为单条只读 `SELECT`，并访问三张白名单表之一。
- 写入意图未被受控拒绝，但实际仍生成只读查询；`ads_gmv_day` 行数在请求前后保持不变。

### 已知缺陷

- `BUG-001`：跨日 TopN 请求被静默降级为首个日期的单日查询，并返回 `200`。
- `BUG-002`：包含支持指标的写入意图被识别为普通查询并返回 `200`，没有受控拒绝。

两条缺陷用例使用 `strict xfail` 保留，产品修复后会以 `XPASS(strict)` 使回归失败，提醒移除缺陷标记并更新证据。

### 证据边界

- `500` 依赖故障语义未执行故障注入，仍为 `not_run`。
- 未覆盖真实 LLM、性能、并发、完整渗透测试或生产环境。
- 本结果只适用于上述受控测试实例和固定数据集。
