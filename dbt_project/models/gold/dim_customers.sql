SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    signup_date,
    status
FROM {{ ref('silver_customers') }}
WHERE customer_id IS NOT NULL