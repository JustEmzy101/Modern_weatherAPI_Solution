{{ config(
    materialized = 'table',
    unique_key='id'
)}}

with source as (SELECT
    *
FROM {{source('dev','raw_weather_data')}}
),

de_duplication as (
    SELECT
    *,
    row_number() OVER(PARTITION BY time ORDER BY inserted_at) as rn
    FROM source
)


SELECT
    id,
    city,
    temp as temperature,
    weather_description,
    wind_speed,
    time as weather_local_time,
    (inserted_at + (utc_offset || 'hours')::interval) as insert_time_local
FROM de_duplication
WHERE rn = 1