{{ config(
    materialized = 'table' 
)}}

SELECT 
    city,
    date(weather_local_time) as date,
    round(avg(temperature)::numeric,2) as avg_temp,
    round(avg(wind_speed)::numeric,2) as avg_wind_speed
FROM {{ ref('stg_weather')}}
GROUP BY 
    city,
    date(weather_local_time)
ORDER BY
    city,
    date(weather_local_time)