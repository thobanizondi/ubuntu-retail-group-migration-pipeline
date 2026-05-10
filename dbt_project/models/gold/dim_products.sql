SELECT
    product_id,
    product_name,
    category,
    unit_price,
    supplier_code
FROM {{ ref('silver_products') }}
WHERE product_id IS NOT NULL