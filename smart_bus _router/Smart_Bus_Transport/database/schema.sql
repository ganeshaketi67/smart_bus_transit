CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_name TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance REAL
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_name TEXT NOT NULL,
    location TEXT
);

CREATE TABLE IF NOT EXISTS route_stops (
    route_id INTEGER,
    stop_id INTEGER,
    stop_order INTEGER,

    PRIMARY KEY (route_id, stop_id),

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id),

    FOREIGN KEY (stop_id)
        REFERENCES stops(stop_id)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,

    route_id INTEGER,

    bus_number TEXT NOT NULL,

    trip_date TEXT,

    departure_time TEXT,
    arrival_time TEXT,

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
);

CREATE TABLE IF NOT EXISTS ridership (
    ridership_id INTEGER PRIMARY KEY AUTOINCREMENT,

    trip_id INTEGER,

    date TEXT,

    passenger_count INTEGER,

    FOREIGN KEY (trip_id)
        REFERENCES trips(trip_id)
);