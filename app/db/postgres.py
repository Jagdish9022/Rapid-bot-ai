import psycopg2
from psycopg2 import sql, Error
import os
from dotenv import load_dotenv
from app.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("postgres")

def get_db_connection():
    try:
        connection_params = {
            "host": os.environ["POSTGRES_DB_HOST"],
            "user": os.environ["POSTGRES_DB_USER"],
            "password": os.environ["POSTGRES_DB_PASSWORD"],
            "dbname": os.environ["POSTGRES_DB_NAME"],
            "port": int(os.environ.get("POSTGRES_DB_PORT", 5432)),
            "sslmode": "require",   # MANDATORY FOR NEON
        }

        logger.info("Connecting to PostgreSQL (Neon)...")
        connection = psycopg2.connect(**connection_params)
        logger.info("PostgreSQL connection successful")
        return connection

    except KeyError as e:
        raise RuntimeError(f"Missing environment variable: {e}")

    except Error as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        raise e


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        logger.info("Initializing tables...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chatbots (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                collection_name VARCHAR(255) NOT NULL UNIQUE,
                source_url TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        connection.commit()
        logger.info("Tables initialized successfully")

    except Error as e:
        logger.error(f"Schema init failed: {e}")
        raise e
    finally:
        cursor.close()
        connection.close()


def get_db():
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()
