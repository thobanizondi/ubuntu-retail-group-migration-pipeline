
  
    
    

    create  table
      "urg_migration"."main_gold"."dim_products__dbt_tmp"
  
    as (
      SELECT
    product_id,
    product_name,
    category,
    unit_price,
    supplier_code
FROM "urg_migration"."main_silver"."silver_products"
WHERE product_id IS NOT NULL
    );
  
  