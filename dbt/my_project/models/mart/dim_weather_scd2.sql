{{
  config(
    materialized='incremental',
    incremental_strategy='append', 
    unique_key='weather_sk',
    post_hook =[
        "
        UPDATE {{ this }}
        SET 
            is_current = FALSE, 
            valid_to = current_timestamp
        WHERE 
            is_current = TRUE 
            AND city IN (
                SELECT city 
                FROM {{ ref('stg_weather') }} 
            )
            AND weather_local_time < (
                SELECT MAX(weather_local_time) 
                FROM {{ ref('stg_weather') }} s_new
                WHERE s_new.city = {{ this }}.city
            )","ANALYZE {{ this }}"
            ],
    indexes=[
      {'columns': ['is_current'], 'type': 'btree', 'where': 'is_current = TRUE'},
      {'columns': ['city', 'weather_id'], 'type': 'btree'},
      {'columns': ['weather_sk'], 'unique': True}

    ]

  )
}}
-- Post_hook logic manages to update the old records to be flaged out as false ( not active ) & end their validity period
WITH source_data AS (
    SELECT 
        -- GENERATE OUR OWN KEY (Brick 1)
        -- We hash the metrics to make a unique ID for this specific report
        md5(cast(city as varchar) || cast(temperature as varchar) || cast(wind_speed as varchar)) as weather_sk,
        id as weather_id,
        city,
        weather_local_time,
        temperature,
        weather_description,
        wind_speed,
        md5(
            COALESCE(CAST(city AS TEXT), '') || '-' ||
            COALESCE(CAST(temperature AS TEXT), '') || '-' ||
            COALESCE(CAST(weather_description AS TEXT), '') || '-' ||
            COALESCE(CAST(wind_speed AS TEXT), '')
        ) as record_hash,
        -- Set default valid_to for new rows
        '9999-12-31 23:59:59'::timestamp as valid_to,
        TRUE as is_current
    FROM {{ ref('stg_weather') }}
),

{% if is_incremental() %}
current_data AS (
    -- Get the currently active row for every city
    SELECT 
        weather_id, 
        city, 
        record_hash
    FROM {{ this }}
    WHERE is_current = TRUE
),
{% endif %}

rows_to_insert AS (
    SELECT 
        s.weather_sk,
        s.weather_id,
        s.city,
        s.weather_local_time,
        s.temperature,
        s.weather_description,
        s.wind_speed,
        s.record_hash,
        s.weather_local_time as valid_from, -- Valid starting NOW
        s.valid_to,
        s.is_current
    FROM source_data s
    {% if is_incremental() %}
    -- Left Join to see if we already have this city
    LEFT JOIN current_data c 
        ON s.city = c.city 
        AND s.weather_id = c.weather_id
    
    WHERE 
        -- Scenario A: It's a brand new city we've never seen
        c.weather_id IS NULL
        
        -- Scenario C: It's a city we know, but the hash changed (Weather is different)
        OR (c.weather_id IS NOT NULL AND s.record_hash != c.record_hash)
    {% endif %}
)

SELECT * FROM rows_to_insert