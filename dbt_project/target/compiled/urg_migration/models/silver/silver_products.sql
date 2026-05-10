SELECT
    TRY_CAST(TRY_CAST(product_id AS DOUBLE) AS INTEGER) AS product_id,
    TRIM(product_name) AS product_name,
    CASE
        WHEN TRIM(category) IS NULL THEN NULL
        ELSE UPPER(LEFT(TRIM(category), 1)) || LOWER(SUBSTR(TRIM(category), 2))
    END AS category,
    TRY_CAST(unit_price AS DOUBLE) AS unit_price,
    NULLIF(TRIM(supplier_code), '') AS supplier_code
FROM main.bronze_products
WHERE product_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY TRY_CAST(TRY_CAST(product_id AS DOUBLE) AS INTEGER)
    ORDER BY product_id
) = 1