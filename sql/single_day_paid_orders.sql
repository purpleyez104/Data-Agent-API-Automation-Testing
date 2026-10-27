SELECT dt, paid_order_count
FROM ads_gmv_day
WHERE dt = :target_date;
