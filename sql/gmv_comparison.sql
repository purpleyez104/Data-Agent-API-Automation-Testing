SELECT dt, gmv
FROM ads_gmv_day
WHERE dt BETWEEN :previous_start_date AND :current_end_date
ORDER BY dt ASC;
