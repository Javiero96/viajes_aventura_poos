from persistence.connection import (
    open_server_connection,
    open_connection,
    get_config,
    get_engine,
)


def create_database_and_tables():
    engine = get_engine()

    # 1. Create database (ONLY FOR MYSQL)
    if engine == "mysql":
        config = get_config()
        db_name = config["database"]

        srv_conn = open_server_connection()
        srv_cursor = srv_conn.cursor()
        try:
            srv_cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            srv_conn.commit()
        finally:
            srv_cursor.close()
            srv_conn.close()

    # 2. Create Tables according to the active engine
    connection = open_connection()
    cursor = connection.cursor()

    try:
        if engine == "sqlite":
            # --- SQLITE SYNTAX ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'CLIENT'
                        CHECK (role IN ('ADMIN', 'CLIENT'))
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS destinations (
                    destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    description TEXT NULL,
                    base_cost REAL NOT NULL CHECK (base_cost >= 0),
                    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                    UNIQUE (name, country)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    package_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NULL,
                    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS package_destinations (
                    package_destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    destination_id INTEGER NOT NULL,
                    visit_order INTEGER NOT NULL CHECK (visit_order >= 1),
                    stay_days INTEGER NOT NULL DEFAULT 1 CHECK (stay_days >= 1),
                    UNIQUE (package_id, visit_order),
                    UNIQUE (package_id, destination_id),
                    FOREIGN KEY (package_id) REFERENCES packages(package_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS package_departures (
                    departure_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    offer_price REAL NOT NULL CHECK (offer_price > 0),
                    total_spots INTEGER NOT NULL CHECK (total_spots > 0),
                    available_spots INTEGER NOT NULL CHECK (available_spots >= 0),
                    CHECK (end_date >= start_date),
                    CHECK (available_spots <= total_spots),
                    FOREIGN KEY (package_id) REFERENCES packages(package_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    departure_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    contracted_unit_price REAL NOT NULL CHECK (contracted_unit_price > 0),
                    total_paid REAL NOT NULL CHECK (total_paid >= 0),
                    status TEXT NOT NULL DEFAULT 'CONFIRMED'
                        CHECK (status IN ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
                    FOREIGN KEY (departure_id) REFERENCES package_departures(departure_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passengers (
                    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    identity_document TEXT NOT NULL,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stage_progress (
                    passenger_id INTEGER NOT NULL,
                    package_destination_id INTEGER NOT NULL,
                    stage_status TEXT NOT NULL DEFAULT 'PENDING'
                        CHECK (stage_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')),
                    updated_at TEXT NULL,
                    PRIMARY KEY (passenger_id, package_destination_id),
                    FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    FOREIGN KEY (package_destination_id) REFERENCES package_destinations(package_destination_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
            """)

        else:
            # --- MYSQL SYNTAX ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    phone VARCHAR(20) NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'CLIENT',
                    CHECK (role IN ('ADMIN', 'CLIENT'))
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS destinations (
                    destination_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    country VARCHAR(80) NOT NULL,
                    description TEXT NULL,
                    base_cost DECIMAL(10,2) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    UNIQUE KEY uq_destination_name_country (name, country),
                    CHECK (base_cost >= 0)
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    package_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    description TEXT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS package_destinations (
                    package_destination_id INT AUTO_INCREMENT PRIMARY KEY,
                    package_id INT NOT NULL,
                    destination_id INT NOT NULL,
                    visit_order INT NOT NULL,
                    stay_days INT NOT NULL DEFAULT 1,
                    UNIQUE KEY uq_package_order (package_id, visit_order),
                    UNIQUE KEY uq_package_destination (package_id, destination_id),
                    CHECK (visit_order >= 1),
                    CHECK (stay_days >= 1),
                    CONSTRAINT fk_pkg_dest_package
                        FOREIGN KEY (package_id) REFERENCES packages(package_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    CONSTRAINT fk_pkg_dest_destination
                        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS package_departures (
                    departure_id INT AUTO_INCREMENT PRIMARY KEY,
                    package_id INT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    offer_price DECIMAL(10,2) NOT NULL,
                    total_spots INT NOT NULL,
                    available_spots INT NOT NULL,
                    CHECK (offer_price > 0),
                    CHECK (total_spots > 0),
                    CHECK (available_spots >= 0),
                    CHECK (end_date >= start_date),
                    CHECK (available_spots <= total_spots),
                    CONSTRAINT fk_departure_package
                        FOREIGN KEY (package_id) REFERENCES packages(package_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    departure_id INT NOT NULL,
                    booking_date DATETIME NOT NULL,
                    contracted_unit_price DECIMAL(10,2) NOT NULL,
                    total_paid DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED',
                    CHECK (contracted_unit_price > 0),
                    CHECK (total_paid >= 0),
                    CHECK (status IN ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
                    CONSTRAINT fk_booking_user
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
                    CONSTRAINT fk_booking_departure
                        FOREIGN KEY (departure_id) REFERENCES package_departures(departure_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passengers (
                    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    full_name VARCHAR(120) NOT NULL,
                    identity_document VARCHAR(30) NOT NULL,
                    CONSTRAINT fk_passenger_booking
                        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stage_progress (
                    passenger_id INT NOT NULL,
                    package_destination_id INT NOT NULL,
                    stage_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    updated_at DATETIME NULL,
                    PRIMARY KEY (passenger_id, package_destination_id),
                    CHECK (stage_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')),
                    CONSTRAINT fk_progress_passenger
                        FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    CONSTRAINT fk_progress_stage
                        FOREIGN KEY (package_destination_id) REFERENCES package_destinations(package_destination_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                ) ENGINE=InnoDB
            """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    create_database_and_tables()
    active_engine = get_engine()
    print(f"Database and tables successfully initialized using engine: {active_engine.upper()}.")