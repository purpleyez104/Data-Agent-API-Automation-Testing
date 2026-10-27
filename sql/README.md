# Expected Queries

本目录用于保存人工确认的 MySQL 预期查询，以独立验证 API 返回的业务数据。不得直接复制 API 响应中的 SQL 作为预期查询。

当前文件：

- `single_day_gmv.sql`：单日 GMV；
- `single_day_paid_orders.sql`：单日支付订单数；
- `gmv_trend_7d.sql`：最近 7 天 GMV 趋势；
- `gmv_comparison.sql`：最近 7 天与前 7 天 GMV 对比源数据；
- `top_products_5.sql`：单日热门商品 Top5；
- `gmv_row_count.sql`：写入意图测试前后的只读行数检查。

前五项独立数据对账已于 `2026-10-26` 执行通过，结果为 `5 passed in 0.20s`。行数检查也已进入完整回归，用于证明本次写入意图没有产生数据库副作用。
