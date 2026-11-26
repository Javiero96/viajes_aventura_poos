import os
import sqlite3
import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_engine() -> str:
    """Returns the configured database engine ('mysql' or 'sqlite')."""
    return os.getenv("DB_ENGINE", "sqlite").lower()


def get_config() -> dict:
    """Returns a dictionary with the current connection configuration."""
    engine = get_engine()
    # Defaults to viajes_aventura_db for MySQL, and viajes_aventura.db for SQLite
    db_name_default = "viajes_aventura_db" if engine == "mysql" else "viajes_aventura.db"

    return {
        "engine": engine,
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "javier"),
        "database": os.getenv("DB_NAME", db_name_default),
    }


def open_server_connection():
    """
    Connects to the database server for global operations
    (such as creating the database if it does not exist in MySQL).
    For SQLite, it simply connects to the local file.
    """
    config = get_config()

    if config["engine"] == "sqlite":
        return sqlite3.connect(config["database"])

    if config["engine"] == "mysql":
        return pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            charset="utf8mb4",
        )

    raise ValueError(f"Unsupported database engine: {config['engine']}")


def open_connection():
    """
    Connects directly to the selected database
    (ready to execute queries with DAOs/Repositories).
    """
    config = get_config()

    if config["engine"] == "sqlite":
        connection = sqlite3.connect(config["database"])
        # Enable foreign key constraints in SQLite
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    if config["engine"] == "mysql":
        return pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
        )

    raise ValueError(f"Unsupported database engine: {config['engine']}")


def sql_placeholder() -> str:
    """Returns the appropriate SQL parameter placeholder according to the active engine."""
    if get_engine() == "sqlite":
        return "?"
    return "%s"