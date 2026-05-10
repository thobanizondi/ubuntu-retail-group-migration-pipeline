
  
    
    

    create  table
      "urg_migration"."main_silver"."silver_orders__dbt_tmp"
  
    as (
      WITH cte_CleanedData AS (
    SELECT
        TRY_CAST(TRY_CAST(order_id AS DOUBLE)    AS INTEGER) AS order_id,
        TRY_CAST(TRY_CAST(customer_id AS DOUBLE) AS INTEGER) AS customer_id,

        COALESCE(
            TRY_STRPTIME(order_date, '%Y-%m-%d'),
            TRY_STRPTIME(REPLACE(order_date, '/', '-'), '%Y-%m-%d'),
            TRY_STRPTIME(order_date, '%d/%m/%Y'),
            TRY_STRPTIME(order_date, '%m/%d/%Y')
        )::DATE AS order_date,

        TRY_CAST(
            REPLACE(
                REGEXP_REPLACE(TRIM(total_amount), '^R\s*', '', 'g'),
            ',', '.')
        AS DOUBLE) AS total_amount,

        CASE UPPER(TRIM(status))
            WHEN 'COMPLETED' THEN 'Completed'
            WHEN 'DONE'      THEN 'Completed'
            WHEN 'C'         THEN 'Completed'
            WHEN 'CANCELLED' THEN 'Cancelled'
            WHEN 'CANCELED'  THEN 'Cancelled'
            WHEN 'PENDING'   THEN 'Pending'
            WHEN 'P'         THEN 'Pending'
            ELSE NULL
        END AS status,

        LOWER(TRIM(channel)) AS channel

    FROM main.bronze_orders
    WHERE order_id IS NOT NULL
)

SELECT
    c.order_id,
    c.customer_id,
    c.order_date,
    c.total_amount,
    c.status,
    c.channel
FROM cte_CleanedData c
INNER JOIN "urg_migration"."main_silver"."silver_customers" sc ON c.customer_id = sc.customer_id
    );
  
  