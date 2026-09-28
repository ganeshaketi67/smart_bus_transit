import sqlite3
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"

DATABASE_DIR.mkdir(exist_ok=True)

DB_PATH = DATABASE_DIR / "smart_transit.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # ROUTES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            route_name TEXT NOT NULL,

            source TEXT NOT NULL,

            destination TEXT NOT NULL,

            distance REAL DEFAULT 0

        )
    """)


    # --------------------------------------------------------
    # STOPS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stops (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            stop_name TEXT NOT NULL,

            location TEXT

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_stops (
            route_id INTEGER NOT NULL,
            stop_id INTEGER NOT NULL,
            stop_order INTEGER NOT NULL,
            PRIMARY KEY (route_id, stop_id),
            FOREIGN KEY(route_id) REFERENCES routes(id),
            FOREIGN KEY(stop_id) REFERENCES stops(id)
        )
    """)

    # --------------------------------------------------------
    # TRIPS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            route_id INTEGER,

            bus_number TEXT,

            trip_date TEXT,

            departure TEXT,

            arrival TEXT,

            FOREIGN KEY(route_id)
                REFERENCES routes(id)

        )
    """)

    trip_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(trips)").fetchall()
    }
    if "trip_date" not in trip_columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN trip_date TEXT")


    # --------------------------------------------------------
    # RIDERSHIP
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ridership (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trip_id INTEGER,

            date TEXT,

            passengers INTEGER,

            FOREIGN KEY(trip_id)
                REFERENCES trips(id)

        )
    """)

    # --------------------------------------------------------
    # OVERCROWDING ALERTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS overcrowding_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            bus_number TEXT,
            stop_name TEXT,
            report_date TEXT,
            report_time TEXT,
            passenger_notes TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(route_id) REFERENCES routes(id)
        )
    """)

    # --------------------------------------------------------
    # FLEET REBALANCE LOGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fleet_rebalance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT,
            donor_route TEXT,
            recipient_route TEXT,
            bus_number TEXT,
            rebalance_date TEXT,
            rebalance_time TEXT,
            revenue_gain REAL,
            fuel_savings REAL,
            status TEXT DEFAULT 'Active'
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# ROUTE FUNCTIONS
# ============================================================

def add_route(
    route_name,
    source,
    destination,
    distance,
    stop_names=None,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO routes
        (
            route_name,
            source,
            destination,
            distance
        )

        VALUES (?, ?, ?, ?)
    """, (
        route_name,
        source,
        destination,
        distance
    ))
    route_id = cursor.lastrowid
    for stop_order, stop_name in enumerate(stop_names or [], start=1):
        stop = cursor.execute(
            "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
            (stop_name,),
        ).fetchone()
        if stop is None:
            cursor.execute(
                "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                (stop_name, ""),
            )
            stop_id = cursor.lastrowid
        else:
            stop_id = stop["id"]
        cursor.execute(
            "INSERT INTO route_stops (route_id, stop_id, stop_order) VALUES (?, ?, ?)",
            (route_id, stop_id, stop_order),
        )

    connection.commit()

    connection.close()
    return route_id


def route_exists(route_name, source, destination, exclude_id=None):
    """Return whether an equivalent route already exists."""
    connection = get_connection()
    query = """
        SELECT 1
        FROM routes
        WHERE lower(route_name) = lower(?)
          AND lower(source) = lower(?)
          AND lower(destination) = lower(?)
    """
    parameters = [route_name, source, destination]
    if exclude_id is not None:
        query += " AND id != ?"
        parameters.append(exclude_id)
    exists = connection.execute(query, parameters).fetchone() is not None
    connection.close()
    return exists


def route_code_exists(route_code, exclude_id=None):
    """Return whether a route code is already assigned."""
    connection = get_connection()
    query = "SELECT 1 FROM routes WHERE lower(route_name) = lower(?)"
    parameters = [route_code.strip()]
    if exclude_id is not None:
        query += " AND id != ?"
        parameters.append(exclude_id)
    exists = connection.execute(query, parameters).fetchone() is not None
    connection.close()
    return exists


def get_routes():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            route_name,
            source,
            destination,
            distance
        FROM routes
        ORDER BY id DESC
    """)

    routes = cursor.fetchall()

    connection.close()

    return routes


def update_route(
    route_id,
    route_name,
    source,
    destination,
    distance,
    stop_names=None,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE routes

        SET
            route_name = ?,
            source = ?,
            destination = ?,
            distance = ?

        WHERE id = ?
    """, (
        route_name,
        source,
        destination,
        distance,
        route_id
    ))
    if stop_names is not None:
        cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
        for stop_order, stop_name in enumerate(stop_names, start=1):
            stop = cursor.execute(
                "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
                (stop_name,),
            ).fetchone()
            if stop is None:
                cursor.execute(
                    "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                    (stop_name, ""),
                )
                stop_id = cursor.lastrowid
            else:
                stop_id = stop["id"]
            cursor.execute(
                "INSERT INTO route_stops (route_id, stop_id, stop_order) VALUES (?, ?, ?)",
                (route_id, stop_id, stop_order),
            )

    connection.commit()

    connection.close()


def delete_route(route_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
    cursor.execute(
        "DELETE FROM routes WHERE id = ?",
        (route_id,)
    )

    connection.commit()

    connection.close()


def get_route_stops(route_id):
    """Return the ordered custom stop sequence for a route."""
    connection = get_connection()
    stops = connection.execute(
        """
        SELECT stops.id, stops.stop_name, stops.location, route_stops.stop_order
        FROM route_stops
        JOIN stops ON stops.id = route_stops.stop_id
        WHERE route_stops.route_id = ?
        ORDER BY route_stops.stop_order
        """,
        (route_id,),
    ).fetchall()
    connection.close()
    return stops


def replace_route_stops(route_id, stop_names):
    """Replace the ordered stop list belonging to one route."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
    for stop_order, stop_name in enumerate(stop_names, start=1):
        stop = cursor.execute(
            "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
            (stop_name,),
        ).fetchone()
        if stop is None:
            cursor.execute(
                "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                (stop_name, ""),
            )
            stop_id = cursor.lastrowid
        else:
            stop_id = stop["id"]
        cursor.execute(
            """
            INSERT INTO route_stops (route_id, stop_id, stop_order)
            VALUES (?, ?, ?)
            """,
            (route_id, stop_id, stop_order),
        )
    connection.commit()
    connection.close()


def bus_number_exists(bus_number, exclude_trip_id=None):
    """Return whether a bus number is already assigned to a trip."""
    connection = get_connection()
    query = "SELECT 1 FROM trips WHERE lower(bus_number) = lower(?)"
    parameters = [bus_number.strip()]
    if exclude_trip_id is not None:
        query += " AND id != ?"
        parameters.append(exclude_trip_id)
    exists = connection.execute(query, parameters).fetchone() is not None
    connection.close()
    return exists


def route_has_trips(route_id):
    """Return whether trips still reference a route."""
    connection = get_connection()
    has_trips = connection.execute(
        "SELECT 1 FROM trips WHERE route_id = ? LIMIT 1",
        (route_id,),
    ).fetchone() is not None
    connection.close()
    return has_trips


# ============================================================
# STOP FUNCTIONS
# ============================================================

def add_stop(
    stop_name,
    location
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO stops
        (
            stop_name,
            location
        )

        VALUES (?, ?)
    """, (
        stop_name,
        location
    ))

    connection.commit()

    connection.close()


def stop_exists(stop_name, exclude_id=None):
    """Return whether a stop with this name already exists."""
    connection = get_connection()
    query = "SELECT 1 FROM stops WHERE lower(stop_name) = lower(?)"
    parameters = [stop_name]
    if exclude_id is not None:
        query += " AND id != ?"
        parameters.append(exclude_id)
    exists = connection.execute(query, parameters).fetchone() is not None
    connection.close()
    return exists


def get_stops():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            stop_name,
            location
        FROM stops
        ORDER BY id DESC
    """)

    stops = cursor.fetchall()

    connection.close()

    return stops


def delete_stop(stop_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM stops WHERE id = ?",
        (stop_id,)
    )

    connection.commit()

    connection.close()


def update_stop(stop_id, stop_name, location):
    """Update an existing stop."""
    connection = get_connection()
    connection.execute(
        """
        UPDATE stops
        SET stop_name = ?, location = ?
        WHERE id = ?
        """,
        (stop_name, location, stop_id),
    )
    connection.commit()
    connection.close()


# ============================================================
# TRIP FUNCTIONS
# ============================================================

def add_trip(
    route_id,
    bus_number,
    trip_date,
    departure,
    arrival
):

    connection = get_connection()

    cursor = connection.cursor()
    duplicate = cursor.execute(
        "SELECT 1 FROM trips WHERE lower(bus_number) = lower(?)",
        (bus_number.strip(),),
    ).fetchone()
    if duplicate:
        connection.close()
        raise ValueError(f"Bus number '{bus_number}' is already assigned.")

    cursor.execute("""
        INSERT INTO trips
        (
            route_id,
            bus_number,
            trip_date,
            departure,
            arrival
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        route_id,
        bus_number,
        trip_date,
        departure,
        arrival
    ))

    connection.commit()

    connection.close()


def get_trips():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            route_id,
            bus_number,
            trip_date,
            departure,
            arrival
        FROM trips
        ORDER BY id DESC
    """)

    trips = cursor.fetchall()

    connection.close()

    return trips


def update_trip(
    trip_id,
    route_id,
    bus_number,
    trip_date,
    departure,
    arrival,
):
    """Update an existing scheduled trip."""
    connection = get_connection()
    connection.execute(
        """
        UPDATE trips
        SET route_id = ?, bus_number = ?, trip_date = ?,
            departure = ?, arrival = ?
        WHERE id = ?
        """,
        (route_id, bus_number, trip_date, departure, arrival, trip_id),
    )
    connection.commit()
    connection.close()


def delete_trip(trip_id):
    """Delete a trip and its associated ridership records."""
    connection = get_connection()
    connection.execute("DELETE FROM ridership WHERE trip_id = ?", (trip_id,))
    connection.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    connection.commit()
    connection.close()


def get_trips_with_routes():
    """Return trips with the route name and endpoints for display."""
    connection = get_connection()
    trips = connection.execute("""
        SELECT
            trips.id,
            trips.route_id,
            trips.bus_number,
            trips.trip_date,
            trips.departure,
            trips.arrival,
            routes.route_name,
            routes.source,
            routes.destination
        FROM trips
        LEFT JOIN routes ON routes.id = trips.route_id
        ORDER BY trips.id DESC
    """).fetchall()
    connection.close()
    return trips


# ============================================================
# RIDERSHIP FUNCTIONS
# ============================================================

def add_ridership(
    trip_id,
    date,
    passengers
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO ridership
        (
            trip_id,
            date,
            passengers
        )

        VALUES (?, ?, ?)
    """, (
        trip_id,
        date,
        passengers
    ))

    connection.commit()

    connection.close()


def get_ridership():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            trip_id,
            date,
            passengers
        FROM ridership
        ORDER BY date
    """)

    ridership = cursor.fetchall()

    connection.close()

    return ridership


def update_ridership(ridership_id, trip_id, record_date, passengers):
    """Update an existing ridership record."""
    connection = get_connection()
    connection.execute(
        """
        UPDATE ridership
        SET trip_id = ?, date = ?, passengers = ?
        WHERE id = ?
        """,
        (trip_id, record_date, passengers, ridership_id),
    )
    connection.commit()
    connection.close()


def delete_ridership(ridership_id):
    """Delete one ridership record."""
    connection = get_connection()
    connection.execute("DELETE FROM ridership WHERE id = ?", (ridership_id,))
    connection.commit()
    connection.close()


def get_ridership_with_trips():
    """Return ridership records with the associated bus number."""
    connection = get_connection()
    records = connection.execute("""
        SELECT
            ridership.id,
            ridership.trip_id,
            ridership.date,
            ridership.passengers,
            trips.bus_number,
            routes.route_name
        FROM ridership
        LEFT JOIN trips ON trips.id = ridership.trip_id
        LEFT JOIN routes ON routes.id = trips.route_id
        ORDER BY ridership.date DESC, ridership.id DESC
    """).fetchall()
    connection.close()
    return records


# ============================================================
# ADVANCED ANALYTICS & NETWORK HELPERS
# ============================================================

def get_route_ridership_analytics():
    """Return aggregated ridership, total trips, and daily averages per route."""
    connection = get_connection()
    query = """
        SELECT
            routes.id AS route_id,
            routes.route_name,
            routes.source,
            routes.destination,
            routes.distance,
            COUNT(DISTINCT trips.id) AS total_scheduled_trips,
            COUNT(DISTINCT ridership.date) AS recorded_days,
            COALESCE(SUM(ridership.passengers), 0) AS total_passengers,
            COALESCE(AVG(ridership.passengers), 0) AS avg_passengers_per_record,
            ROUND(
                CAST(COALESCE(SUM(ridership.passengers), 0) AS REAL) / 
                MAX(1, COUNT(DISTINCT ridership.date)), 1
            ) AS avg_daily_passengers
        FROM routes
        LEFT JOIN trips ON trips.route_id = routes.id
        LEFT JOIN ridership ON ridership.trip_id = trips.id
        GROUP BY routes.id
        ORDER BY total_passengers DESC
    """
    rows = connection.execute(query).fetchall()
    connection.close()
    return [dict(r) for r in rows]


def get_network_graph_data():
    """Return all routes and their ordered stop sequences for BFS graph construction."""
    connection = get_connection()
    query = """
        SELECT
            routes.id AS route_id,
            routes.route_name,
            routes.source,
            routes.destination,
            routes.distance,
            stops.id AS stop_id,
            stops.stop_name,
            stops.location,
            route_stops.stop_order
        FROM routes
        JOIN route_stops ON route_stops.route_id = routes.id
        JOIN stops ON stops.id = route_stops.stop_id
        ORDER BY routes.id, route_stops.stop_order
    """
    rows = connection.execute(query).fetchall()
    connection.close()
    return [dict(r) for r in rows]


def check_bus_schedule_conflict(bus_number, departure, arrival, trip_date, exclude_trip_id=None):
    """Check if the bus is already assigned to a trip with overlapping time window on trip_date."""
    connection = get_connection()
    query = """
        SELECT id, bus_number, departure, arrival, trip_date
        FROM trips
        WHERE lower(bus_number) = lower(?)
          AND trip_date = ?
    """
    params = [bus_number.strip(), trip_date]
    if exclude_trip_id is not None:
        query += " AND id != ?"
        params.append(exclude_trip_id)
    
    trips = connection.execute(query, params).fetchall()
    connection.close()
    
    # Check overlap in departure/arrival times
    for trip in trips:
        t_dep = trip["departure"]
        t_arr = trip["arrival"]
        if not (arrival <= t_dep or departure >= t_arr):
            return True, f"Conflict with Trip #{trip['id']} ({t_dep} - {t_arr})"
            
    return False, ""


def seed_demo_data():
    """Populate database with a realistic transport dataset for demonstration."""
    import random
    from datetime import date, timedelta
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Clear existing data safely
    cursor.execute("DELETE FROM ridership")
    cursor.execute("DELETE FROM trips")
    cursor.execute("DELETE FROM route_stops")
    cursor.execute("DELETE FROM overcrowding_alerts")
    cursor.execute("DELETE FROM fleet_rebalance_logs")
    cursor.execute("DELETE FROM routes")
    cursor.execute("DELETE FROM stops")
    
    # Reset sqlite sequences
    for tbl in ["routes", "stops", "trips", "ridership", "overcrowding_alerts", "fleet_rebalance_logs"]:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (tbl,))
        
    connection.commit()
    connection.close()
    
    # Defined routes with stops
    sample_routes = [
        {
            "code": "101",
            "source": "Secunderabad",
            "destination": "Koti",
            "distance": 12.5,
            "stops": ["Secunderabad", "Batas", "RTC X Roads", "Kachiguda", "Koti"]
        },
        {
            "code": "102",
            "source": "Hitech City",
            "destination": "Koti",
            "distance": 22.0,
            "stops": ["Hitech City", "Madhapur", "Jubilee Hills", "Ameerpet", "Punjagutta", "Koti"]
        },
        {
            "code": "103",
            "source": "Koti",
            "destination": "LB Nagar",
            "distance": 14.8,
            "stops": ["Koti", "Malakpet", "Dilsukhnagar", "LB Nagar"]
        },
        {
            "code": "104",
            "source": "Secunderabad",
            "destination": "Ameerpet",
            "distance": 9.2,
            "stops": ["Secunderabad", "Begumpet", "Ameerpet"]
        },
        {
            "code": "105",
            "source": "Ameerpet",
            "destination": "LB Nagar",
            "distance": 25.0,
            "stops": ["Ameerpet", "Punjagutta", "Koti", "Dilsukhnagar", "LB Nagar"]
        }
    ]
    
    route_ids = []
    for r in sample_routes:
        r_id = add_route(r["code"], r["source"], r["destination"], r["distance"], r["stops"])
        route_ids.append(r_id)
        
    # Sample trips
    buses = ["AP09-B-1001", "AP09-B-1002", "AP09-B-1003", "AP09-B-1004", "AP09-B-1005", "AP09-B-1006", "AP09-B-1007", "AP09-B-1008"]
    time_slots = [
        ("06:00", "07:15"),
        ("07:30", "08:45"),
        ("09:00", "10:15"),
        ("11:00", "12:15"),
        ("14:00", "15:15"),
        ("17:00", "18:15"),
        ("18:30", "19:45"),
        ("20:00", "21:15"),
    ]
    
    today = date.today()
    created_trips = []
    
    bus_idx = 0
    for idx, r_id in enumerate(route_ids):
        # assign 2 to 4 trips per route
        num_trips = 3 if idx % 2 == 0 else 4
        for t in range(num_trips):
            bus_no = buses[bus_idx % len(buses)]
            bus_idx += 1
            slot = time_slots[t % len(time_slots)]
            t_date = today.isoformat()
            
            # Add trip
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO trips (route_id, bus_number, trip_date, departure, arrival)
                VALUES (?, ?, ?, ?, ?)
            """, (r_id, bus_no, t_date, slot[0], slot[1]))
            trip_id = cursor.lastrowid
            connection.commit()
            connection.close()
            
            created_trips.append((trip_id, r_id))
            
    # Generate 30 days of historical ridership with realistic peak vs peripheral route demand
    route_demand_profiles = {
        1: 60,  # Secunderabad - Koti (Overloaded Spine ~120% load)
        2: 74,  # Hitech City - Koti (Peak IT Corridor ~148% load)
        3: 42,  # Koti - LB Nagar (Balanced standard ~84% load)
        4: 16,  # Secunderabad - Ameerpet (Peripheral Feeder ~32% load - empty buses)
        5: 18   # Ameerpet - LB Nagar (Peripheral Feeder ~36% load - empty buses)
    }

    for trip_id, r_id in created_trips:
        base_demand = route_demand_profiles.get(r_id, 35)
        for d in range(30, 0, -1):
            past_date = today - timedelta(days=d)
            # Weekend effect + upward trend + random noise
            day_of_week = past_date.weekday()
            weekend_factor = 1.25 if day_of_week in (5, 6) else 1.0
            trend_factor = 1.0 + (30 - d) * 0.012
            noise = random.randint(-4, 6)
            
            passengers = int(max(8, (base_demand * weekend_factor * trend_factor) + noise))
            add_ridership(trip_id, past_date.isoformat(), passengers)
            
    return len(sample_routes), len(created_trips)


# ============================================================
# OVERCROWDING ALERTS FUNCTIONS
# ============================================================

def add_overcrowding_alert(route_id, bus_number, stop_name, report_date, report_time, passenger_notes=""):
    """Insert a new overcrowded bus alert submitted by a passenger."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO overcrowding_alerts (route_id, bus_number, stop_name, report_date, report_time, passenger_notes, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    """, (route_id, bus_number, stop_name, report_date, report_time, passenger_notes))
    alert_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return alert_id


def get_overcrowding_alerts():
    """Retrieve all overcrowded bus alerts for operator view."""
    connection = get_connection()
    query = """
        SELECT
            overcrowding_alerts.id,
            overcrowding_alerts.route_id,
            overcrowding_alerts.bus_number,
            overcrowding_alerts.stop_name,
            overcrowding_alerts.report_date,
            overcrowding_alerts.report_time,
            overcrowding_alerts.passenger_notes,
            overcrowding_alerts.status,
            routes.route_name,
            routes.source,
            routes.destination
        FROM overcrowding_alerts
        LEFT JOIN routes ON routes.id = overcrowding_alerts.route_id
        ORDER BY overcrowding_alerts.id DESC
    """
    rows = connection.execute(query).fetchall()
    connection.close()
    return [dict(r) for r in rows]


def resolve_overcrowding_alert(alert_id):
    """Mark an overcrowding alert as Extra Bus Dispatched."""
    connection = get_connection()
    connection.execute("""
        UPDATE overcrowding_alerts
        SET status = 'Extra Bus Dispatched'
        WHERE id = ?
    """, (alert_id,))
    connection.commit()
    connection.close()


def add_rebalance_log(action_id, donor_route, recipient_route, bus_number, rebalance_date, rebalance_time, revenue_gain, fuel_savings):
    """Record an executed dynamic fleet rebalancing dispatch."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO fleet_rebalance_logs (action_id, donor_route, recipient_route, bus_number, rebalance_date, rebalance_time, revenue_gain, fuel_savings, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
    """, (action_id, donor_route, recipient_route, bus_number, rebalance_date, rebalance_time, revenue_gain, fuel_savings))
    log_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return log_id


def get_rebalance_logs():
    """Retrieve all executed fleet rebalancing dispatch logs."""
    connection = get_connection()
    rows = connection.execute("SELECT * FROM fleet_rebalance_logs ORDER BY id DESC").fetchall()
    connection.close()
    return [dict(r) for r in rows]

