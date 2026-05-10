SELECT
    transaction_id,
    order_id,
    payment_method,
    transaction_amount,
    transaction_date,
    success_flag
FROM {{ ref('silver_transactions') }}
WHERE transaction_id IS NOT NULL