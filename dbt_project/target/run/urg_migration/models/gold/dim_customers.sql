
  
    
    

    create  table
      "urg_migration"."main_gold"."dim_customers__dbt_tmp"
  
    as (
      SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    signup_date,
    status
FROM "urg_migration"."main_silver"."silver_customers"
WHERE customer_id IS NOT NULL
    );
  
  