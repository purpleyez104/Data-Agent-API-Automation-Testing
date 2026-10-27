SELECT
    product_id,
    product_name,
    category_name,
    brand_name,
    sale_count,
    sale_amount,
    rank_no
FROM ads_top_product
WHERE dt = :target_date
ORDER BY rank_no ASC
LIMIT 5;
