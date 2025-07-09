import psycopg2
from psycopg2 import sql, Error
import os
from dotenv import load_dotenv
from app.utils.logger import setup_logger 

# Load environment variables
load_dotenv()

# Use your custom logger
logger = setup_logger("postgres")

def get_db_connection(use_database=True):
    try:
        connection_params = {
            'host': os.getenv("POSTGRES_DB_HOST", "localhost"),
            'user': os.getenv("POSTGRES_DB_USER", "postgres"),
            'password': os.getenv("POSTGRES_DB_PASSWORD", "postgresql"),
            'port': os.getenv("POSTGRES_DB_PORT", 5432),
        }

        if use_database:
            connection_params['dbname'] = os.getenv("POSTGRES_DB_NAME", "webchat_db")

        logger.info(f"Attempting to connect to PostgreSQL {'database' if use_database else 'server'}...")
        connection = psycopg2.connect(**connection_params)
        logger.info("Successfully connected to PostgreSQL")
        return connection

    except Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise e

def create_database():
    """Create database if it doesn't exist"""
    connection = None
    cursor = None
    try:
        logger.info("Starting PostgreSQL database creation process...")
        connection = get_db_connection(use_database=False)
        connection.autocommit = True
        cursor = connection.cursor()

        db_name = os.getenv("POSTGRES_DB_NAME", "webchat_db")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        logger.info(f"Database '{db_name}' created (if it didn't exist).")

    except Error as e:
        if "already exists" in str(e):
            logger.info("Database already exists, skipping creation.")
        else:
            logger.error(f"Failed to create PostgreSQL database: {e}")
            raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            logger.info("PostgreSQL server connection closed.")

def init_db():
    """Initialize PostgreSQL database with required tables."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        logger.info("Initializing PostgreSQL tables...")
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
        logger.info("PostgreSQL tables initialized successfully")

    except Error as e:
        logger.error(f"Error initializing PostgreSQL tables: {e}")
        raise e
    finally:
        cursor.close()
        connection.close()
        logger.info("PostgreSQL connection closed")

def get_db():
    """Yield PostgreSQL connection."""
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()
