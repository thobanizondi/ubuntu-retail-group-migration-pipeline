WITH cte_CleanedData AS (
    SELECT
        TRY_CAST(TRY_CAST(transaction_id AS DOUBLE) AS INTEGER) AS transaction_id,
        TRY_CAST(order_id AS INTEGER)                           AS order_id,

        CASE UPPER(TRIM(payment_method))
            WHEN 'CARD'        THEN 'Credit Card'
            WHEN 'CC'          THEN 'Credit Card'
            WHEN 'CREDIT CARD' THEN 'Credit Card'
            WHEN 'CASH'        THEN 'Cash'
            WHEN 'EFT'         THEN 'EFT'
            WHEN 'DEBIT CARD'  THEN 'Debit Card'
            ELSE NULL
        END AS payment_method,

        TRY_CAST(transaction_amount AS DOUBLE) AS transaction_amount,

        COALESCE(
            TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
            TRY_STRPTIME(transaction_date, '%d/%m/%Y')
        )::DATE AS transaction_date,

        CASE UPPER(TRIM(success_flag))
            WHEN 'Y'     THEN TRUE
            WHEN 'YES'   THEN TRUE
            WHEN '1'     THEN TRUE
            WHEN 'TRUE'  THEN TRUE
            WHEN 'N'     THEN FALSE
            WHEN 'NO'    THEN FALSE
            WHEN '0'     THEN FALSE
            WHEN 'FALSE' THEN FALSE
            ELSE NULL
        END AS success_flag

    FROM main.bronze_transactions
    WHERE transaction_id IS NOT NULL
)

SELECT
    c.transaction_id,
    c.order_id,
    c.payment_method,
    c.transaction_amount,
    c.transaction_date,
    c.success_flag
FROM cte_CleanedData c
INNER JOIN {{ ref('silver_orders') }} so ON c.order_id = so.order_id