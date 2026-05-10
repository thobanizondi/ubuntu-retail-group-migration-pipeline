WITH cte_CleanedData AS (
    SELECT
        TRY_CAST(TRY_CAST(customer_id AS DOUBLE) AS INTEGER) AS customer_id,

        CASE
            WHEN full_name IS NOT NULL AND INSTR(full_name, ' ') > 0
                THEN TRIM(LEFT(full_name, INSTR(full_name, ' ') - 1))
            ELSE TRIM(full_name)
        END AS first_name,

        CASE
            WHEN full_name IS NOT NULL AND INSTR(full_name, ' ') > 0
                THEN TRIM(SUBSTR(full_name, INSTR(full_name, ' ') + 1))
            ELSE NULL
        END AS last_name,

        CASE
            WHEN email IS NOT NULL THEN LOWER(TRIM(email))
            ELSE NULL
        END AS email,

        TRIM(phone_number) AS phone_number,

        COALESCE(
            TRY_STRPTIME(signup_date, '%Y-%m-%d'),
            TRY_STRPTIME(signup_date, '%d/%m/%Y'),
            TRY_STRPTIME(signup_date, '%m-%d-%Y')
        )::DATE AS signup_date,

        CASE UPPER(TRIM(status))
            WHEN 'ACTIVE'   THEN 'Active'
            WHEN 'INACTIVE' THEN 'Inactive'
            WHEN 'ACT'      THEN 'Active'
            ELSE NULL
        END AS status

    FROM main.bronze_customers
    WHERE customer_id IS NOT NULL
)

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    signup_date,
    status
FROM cte_CleanedData
WHERE customer_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY customer_id
) = 1