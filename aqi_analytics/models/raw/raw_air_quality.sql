select
    r.coord.lat::double as latitude,
    r.coord.lon::double as longitude,
    to_timestamp(observation.dt) as measured_at,
    observation.main.aqi::integer as aqi,
    observation.components.pm2_5::double as pm2_5,
    observation.components.pm10::double as pm10,
    observation.components.co::double as co,
    observation.components.no::double as no,
    observation.components.no2::double as no2,
    observation.components.o3::double as o3,
    observation.components.so2::double as so2,
    observation.components.nh3::double as nh3,
    r.filename as source_file

from {{ source('bronze', 'raw_files') }} as r
cross join unnest(r."list") as readings(observation)

qualify row_number() over (
    partition by
        r.coord.lat,
        r.coord.lon,
        observation.dt
    order by r.filename desc
) = 1