SELECT dt, gmv
FROM ads_gmv_day
WHERE dt BETWEEN :start_date AND :end_date
ORDER BY dt ASC;
