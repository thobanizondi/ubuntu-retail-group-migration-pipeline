SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status,
    channel
FROM "urg_migration"."main_silver"."silver_orders"
WHERE order_id IS NOT NULL