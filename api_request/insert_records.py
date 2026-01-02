from api_request import mock_fetch_data, fetch_data
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, date, time
import json

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create connection pool at module level
def get_db_engine():
    """Create reusable database engine with connection pooling"""
    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER', 'weather_user')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST', 'db')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'weather_db')}"
    )
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Test connections before use
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=UTC"
        }
    )
    return engine

ENGINE = get_db_engine()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def connect_to_db():
    """Get database connection with retry logic"""
    try:
        conn = ENGINE.connect()
        # Test connection
        conn.execute(text("SELECT 1"))
        logger.info("Connected to database successfully")
        return conn
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        raise

def create_table(engine):
    print("Creating Table if not exist...")
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE SCHEMA IF NOT EXISTS dev;
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dev.raw_weather_data(
                    id SERIAL PRIMARY KEY,
                    city TEXT,
                    temp FLOAT,
                    weather_description TEXT,
                    wind_speed FLOAT,
                    time TIMESTAMP,
                    inserted_at TIMESTAMP DEFAULT NOW(),
                    utc_offset TEXT
                );
            """))
        print("Table Created Successfully")
    except SQLAlchemyError as e:
        print(f"Failed to create table due to {e}")
        logger.error("Failed to create table", exc_info=True, extra={
            "table": "raw_weather_data",
            "schema": "dev",
            "action": "schema_creation"
        })
        raise

#######################################
######## to_timestamp #################
#######################################
def time_conversion(data):
    weather = data['current']
    time_str = weather["observation_time"]
    # Parse time string
    time_obj = datetime.strptime(time_str, "%I:%M %p").time()

    # Combine with today's date
    timestamp_obj = datetime.combine(date.today(), time_obj)
    return timestamp_obj



@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def insert_records(engine, data):
    """Insert weather records with transaction safety"""
    try:
        location = data['location']
        weather = data['current']
        
        with engine.begin() as conn:  # Auto-rollback on exception
            conn.execute(text("""
                INSERT INTO dev.raw_weather_data
                (city, temp, weather_description, wind_speed, time, inserted_at, utc_offset)
                VALUES (:city, :temp, :description, :wind_speed, :time, NOW(), :utc_offset)
            """), {
                "city": location['name'],
                "temp": weather['temperature'],
                "description": weather['weather_descriptions'][0],
                "wind_speed": weather['wind_speed'],
                "time": time_conversion(data),
                "utc_offset": location["utc_offset"]
            })
            logger.info("Data inserted successfully", extra={
                "city": location['name'],
                "temperature": weather['temperature']
            })
    except SQLAlchemyError as e:
        logger.error("Failed to insert records", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

def main():
    try:
        # data = mock_fetch_data()
        data = fetch_data()
        create_table(ENGINE)
        insert_records(ENGINE, data)
        logger.info("Data pipeline completed successfully")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise
    finally:
        print("Pipeline execution finished")
        ENGINE.dispose()

if __name__ == "__main__":
    main()