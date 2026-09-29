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
# CREATE DATABASE & AUTO-MIGRATIONS
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
            distance REAL DEFAULT 0,
            base_fare REAL DEFAULT 10.0,
            fare_per_km REAL DEFAULT 2.5,
            min_fare REAL DEFAULT 10.0
        )
    """)

    # Check and migrate columns on routes table if older schema exists
    route_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(routes)").fetchall()}
    if "base_fare" not in route_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN base_fare REAL DEFAULT 10.0")
    if "fare_per_km" not in route_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN fare_per_km REAL DEFAULT 2.5")
    if "min_fare" not in route_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN min_fare REAL DEFAULT 10.0")

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

    # --------------------------------------------------------
    # ROUTE STOPS (with distance_from_origin and custom fare)
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_stops (
            route_id INTEGER NOT NULL,
            stop_id INTEGER NOT NULL,
            stop_order INTEGER NOT NULL,
            distance_from_origin REAL DEFAULT 0.0,
            fare_from_origin REAL DEFAULT NULL,
            PRIMARY KEY (route_id, stop_id),
            FOREIGN KEY(route_id) REFERENCES routes(id),
            FOREIGN KEY(stop_id) REFERENCES stops(id)
        )
    """)

    # Check and migrate columns on route_stops table
    rs_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(route_stops)").fetchall()}
    if "distance_from_origin" not in rs_columns:
        cursor.execute("ALTER TABLE route_stops ADD COLUMN distance_from_origin REAL DEFAULT 0.0")
    if "fare_from_origin" not in rs_columns:
        cursor.execute("ALTER TABLE route_stops ADD COLUMN fare_from_origin REAL DEFAULT NULL")

    # --------------------------------------------------------
    # CUSTOM STOP-TO-STOP FARES (Override matrix)
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stop_to_stop_fares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            from_stop_id INTEGER NOT NULL,
            to_stop_id INTEGER NOT NULL,
            custom_fare REAL NOT NULL,
            custom_distance REAL,
            notes TEXT,
            UNIQUE(route_id, from_stop_id, to_stop_id),
            FOREIGN KEY(route_id) REFERENCES routes(id),
            FOREIGN KEY(from_stop_id) REFERENCES stops(id),
            FOREIGN KEY(to_stop_id) REFERENCES stops(id)
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
            FOREIGN KEY(route_id) REFERENCES routes(id)
        )
    """)

    trip_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(trips)").fetchall()}
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
            FOREIGN KEY(trip_id) REFERENCES trips(id)
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
    base_fare=10.0,
    fare_per_km=2.5,
    min_fare=10.0,
    stop_distances=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO routes
        (
            route_name,
            source,
            destination,
            distance,
            base_fare,
            fare_per_km,
            min_fare
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        route_name,
        source,
        destination,
        float(distance or 0),
        float(base_fare if base_fare is not None else 10.0),
        float(fare_per_km if fare_per_km is not None else 2.5),
        float(min_fare if min_fare is not None else 10.0)
    ))
    route_id = cursor.lastrowid
    
    stops_list = stop_names or []
    num_stops = len(stops_list)
    total_dist = float(distance or 0)

    for stop_order, stop_name in enumerate(stops_list, start=1):
        stop = cursor.execute(
            "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
            (stop_name.strip(),),
        ).fetchone()
        if stop is None:
            cursor.execute(
                "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                (stop_name.strip(), ""),
            )
            stop_id = cursor.lastrowid
        else:
            stop_id = stop["id"]

        # Determine distance from origin
        if stop_distances and len(stop_distances) >= stop_order:
            dist_from_origin = float(stop_distances[stop_order - 1])
        else:
            # Proportional interpolation
            dist_from_origin = 0.0 if num_stops <= 1 else round((stop_order - 1) * (total_dist / (num_stops - 1)), 1)

        cursor.execute(
            """
            INSERT INTO route_stops (route_id, stop_id, stop_order, distance_from_origin)
            VALUES (?, ?, ?, ?)
            """,
            (route_id, stop_id, stop_order, dist_from_origin),
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
            distance,
            base_fare,
            fare_per_km,
            min_fare
        FROM routes
        ORDER BY id DESC
    """)

    routes = cursor.fetchall()
    connection.close()
    return routes


def get_route_by_id(route_id):
    connection = get_connection()
    route = connection.execute(
        """
        SELECT id, route_name, source, destination, distance, base_fare, fare_per_km, min_fare
        FROM routes
        WHERE id = ?
        """,
        (route_id,),
    ).fetchone()
    connection.close()
    return route


def update_route(
    route_id,
    route_name,
    source,
    destination,
    distance,
    stop_names=None,
    base_fare=10.0,
    fare_per_km=2.5,
    min_fare=10.0,
    stop_distances=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE routes
        SET
            route_name = ?,
            source = ?,
            destination = ?,
            distance = ?,
            base_fare = ?,
            fare_per_km = ?,
            min_fare = ?
        WHERE id = ?
    """, (
        route_name,
        source,
        destination,
        float(distance or 0),
        float(base_fare if base_fare is not None else 10.0),
        float(fare_per_km if fare_per_km is not None else 2.5),
        float(min_fare if min_fare is not None else 10.0),
        route_id
    ))

    if stop_names is not None:
        cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
        num_stops = len(stop_names)
        total_dist = float(distance or 0)
        for stop_order, stop_name in enumerate(stop_names, start=1):
            stop = cursor.execute(
                "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
                (stop_name.strip(),),
            ).fetchone()
            if stop is None:
                cursor.execute(
                    "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                    (stop_name.strip(), ""),
                )
                stop_id = cursor.lastrowid
            else:
                stop_id = stop["id"]

            if stop_distances and len(stop_distances) >= stop_order:
                dist_from_origin = float(stop_distances[stop_order - 1])
            else:
                dist_from_origin = 0.0 if num_stops <= 1 else round((stop_order - 1) * (total_dist / (num_stops - 1)), 1)

            cursor.execute(
                """
                INSERT INTO route_stops (route_id, stop_id, stop_order, distance_from_origin)
                VALUES (?, ?, ?, ?)
                """,
                (route_id, stop_id, stop_order, dist_from_origin),
            )

    connection.commit()
    connection.close()


def delete_route(route_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM stop_to_stop_fares WHERE route_id = ?", (route_id,))
    cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
    cursor.execute("DELETE FROM routes WHERE id = ?", (route_id,))

    connection.commit()
    connection.close()


def route_has_trips(route_id):
    """Return True if any trips are currently assigned to this route."""
    connection = get_connection()
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM trips WHERE route_id = ?",
        (route_id,),
    ).fetchone()["count"]
    connection.close()
    return count > 0


def get_route_stops(route_id):
    """Return the ordered custom stop sequence for a route with distances and fares."""
    connection = get_connection()
    stops = connection.execute(
        """
        SELECT
            stops.id,
            stops.stop_name,
            stops.location,
            route_stops.stop_order,
            COALESCE(route_stops.distance_from_origin, 0.0) AS distance_from_origin,
            route_stops.fare_from_origin
        FROM route_stops
        JOIN stops ON stops.id = route_stops.stop_id
        WHERE route_stops.route_id = ?
        ORDER BY route_stops.stop_order
        """,
        (route_id,),
    ).fetchall()
    connection.close()
    return stops


def replace_route_stops(route_id, stop_names, stop_distances=None):
    """Replace the ordered stop list belonging to one route."""
    connection = get_connection()
    cursor = connection.cursor()

    # Get route total distance
    route = cursor.execute("SELECT distance FROM routes WHERE id = ?", (route_id,)).fetchone()
    total_dist = float(route["distance"]) if route else 0.0
    num_stops = len(stop_names)

    cursor.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
    for stop_order, stop_name in enumerate(stop_names, start=1):
        stop = cursor.execute(
            "SELECT id FROM stops WHERE lower(stop_name) = lower(?)",
            (stop_name.strip(),),
        ).fetchone()
        if stop is None:
            cursor.execute(
                "INSERT INTO stops (stop_name, location) VALUES (?, ?)",
                (stop_name.strip(), ""),
            )
            stop_id = cursor.lastrowid
        else:
            stop_id = stop["id"]

        if stop_distances and len(stop_distances) >= stop_order:
            dist = float(stop_distances[stop_order - 1])
        else:
            dist = 0.0 if num_stops <= 1 else round((stop_order - 1) * (total_dist / (num_stops - 1)), 1)

        cursor.execute(
            """
            INSERT INTO route_stops (route_id, stop_id, stop_order, distance_from_origin)
            VALUES (?, ?, ?, ?)
            """,
            (route_id, stop_id, stop_order, dist),
        )
    connection.commit()
    connection.close()


# ============================================================
# FARE & DISTANCE PRICING MANAGEMENT FUNCTIONS
# ============================================================

def update_route_fare_pricing(route_id, base_fare, fare_per_km, min_fare=10.0):
    """Update the base fare and per-km rate for a route."""
    connection = get_connection()
    connection.execute("""
        UPDATE routes
        SET base_fare = ?, fare_per_km = ?, min_fare = ?
        WHERE id = ?
    """, (float(base_fare), float(fare_per_km), float(min_fare), route_id))
    connection.commit()
    connection.close()


def update_route_stop_distances(route_id, stop_data_list):
    """
    Update the cumulative distance and optional custom fare for each stop on a route.
    stop_data_list is a list of dicts: [{'stop_id': int, 'distance_from_origin': float, 'fare_from_origin': float|None}]
    """
    connection = get_connection()
    cursor = connection.cursor()
    max_dist = 0.0
    for item in stop_data_list:
        stop_id = item["stop_id"]
        dist = float(item.get("distance_from_origin", 0.0))
        custom_fare = item.get("fare_from_origin")
        if custom_fare is not None:
            custom_fare = float(custom_fare)
        if dist > max_dist:
            max_dist = dist
        cursor.execute("""
            UPDATE route_stops
            SET distance_from_origin = ?, fare_from_origin = ?
            WHERE route_id = ? AND stop_id = ?
        """, (dist, custom_fare, route_id, stop_id))

    # Also update route total distance if the final stop has a larger distance
    if max_dist > 0:
        cursor.execute("UPDATE routes SET distance = ? WHERE id = ?", (max_dist, route_id))

    connection.commit()
    connection.close()


def auto_distribute_route_stop_distances(route_id):
    """Interpolate stop distances evenly along the route based on total distance."""
    connection = get_connection()
    cursor = connection.cursor()
    route = cursor.execute("SELECT distance FROM routes WHERE id = ?", (route_id,)).fetchone()
    if not route:
        connection.close()
        return

    total_dist = float(route["distance"] or 0)
    stops = cursor.execute(
        "SELECT stop_id, stop_order FROM route_stops WHERE route_id = ? ORDER BY stop_order",
        (route_id,)
    ).fetchall()

    n = len(stops)
    if n > 0:
        for idx, row in enumerate(stops):
            dist = 0.0 if n <= 1 else round(idx * (total_dist / (n - 1)), 1)
            cursor.execute(
                "UPDATE route_stops SET distance_from_origin = ? WHERE route_id = ? AND stop_id = ?",
                (dist, route_id, row["stop_id"])
            )

    connection.commit()
    connection.close()


def calculate_ticket_fare(route_id, from_stop_identifier, to_stop_identifier):
    """
    Calculate the exact distance and ticket fare between two stops on a route.
    Accepts stop IDs (int) or stop names (str).
    Returns a dict with fare, distance, base_fare, fare_per_km, is_custom, and stop details.
    """
    connection = get_connection()
    route = connection.execute(
        "SELECT id, route_name, distance, base_fare, fare_per_km, min_fare FROM routes WHERE id = ?",
        (route_id,)
    ).fetchone()

    if not route:
        connection.close()
        return {
            "fare": 10.0,
            "distance": 0.0,
            "base_fare": 10.0,
            "fare_per_km": 2.5,
            "min_fare": 10.0,
            "is_custom": False,
            "from_stop": str(from_stop_identifier),
            "to_stop": str(to_stop_identifier)
        }

    base_fare = float(route["base_fare"] or 10.0)
    fare_per_km = float(route["fare_per_km"] or 2.5)
    min_fare = float(route["min_fare"] or 10.0)

    # Get all stops on the route
    route_stops = connection.execute("""
        SELECT
            stops.id AS stop_id,
            stops.stop_name,
            route_stops.stop_order,
            COALESCE(route_stops.distance_from_origin, 0.0) AS distance_from_origin,
            route_stops.fare_from_origin
        FROM route_stops
        JOIN stops ON stops.id = route_stops.stop_id
        WHERE route_stops.route_id = ?
        ORDER BY route_stops.stop_order
    """, (route_id,)).fetchall()

    from_row = None
    to_row = None

    for s in route_stops:
        if isinstance(from_stop_identifier, int) and s["stop_id"] == from_stop_identifier:
            from_row = s
        elif str(from_stop_identifier).strip().lower() == s["stop_name"].strip().lower():
            from_row = s

        if isinstance(to_stop_identifier, int) and s["stop_id"] == to_stop_identifier:
            to_row = s
        elif str(to_stop_identifier).strip().lower() == s["stop_name"].strip().lower():
            to_row = s

    if not from_row or not to_row:
        connection.close()
        return {
            "fare": base_fare,
            "distance": 0.0,
            "base_fare": base_fare,
            "fare_per_km": fare_per_km,
            "min_fare": min_fare,
            "is_custom": False,
            "from_stop": str(from_stop_identifier),
            "to_stop": str(to_stop_identifier)
        }

    # Check for direct custom override in stop_to_stop_fares
    override = connection.execute("""
        SELECT custom_fare, custom_distance
        FROM stop_to_stop_fares
        WHERE route_id = ? AND from_stop_id = ? AND to_stop_id = ?
    """, (route_id, from_row["stop_id"], to_row["stop_id"])).fetchone()

    connection.close()

    if override:
        custom_dist = float(override["custom_distance"]) if override["custom_distance"] is not None else abs(from_row["distance_from_origin"] - to_row["distance_from_origin"])
        return {
            "fare": round(float(override["custom_fare"]), 0),
            "distance": round(custom_dist, 1),
            "base_fare": base_fare,
            "fare_per_km": fare_per_km,
            "min_fare": min_fare,
            "is_custom": True,
            "from_stop": from_row["stop_name"],
            "to_stop": to_row["stop_name"]
        }

    # Distance calculation
    dist_diff = abs(float(to_row["distance_from_origin"]) - float(from_row["distance_from_origin"]))
    
    # If distance was 0 and indices differ, interpolate from total route distance
    if dist_diff == 0.0 and len(route_stops) > 1 and from_row["stop_order"] != to_row["stop_order"]:
        hops = abs(to_row["stop_order"] - from_row["stop_order"])
        total_hops = len(route_stops) - 1
        dist_diff = round((hops / total_hops) * float(route["distance"] or 10.0), 1)

    calculated_fare = base_fare + (dist_diff * fare_per_km)
    final_fare = max(min_fare, round(calculated_fare))

    return {
        "fare": final_fare,
        "distance": round(dist_diff, 1),
        "base_fare": base_fare,
        "fare_per_km": fare_per_km,
        "min_fare": min_fare,
        "is_custom": False,
        "from_stop": from_row["stop_name"],
        "to_stop": to_row["stop_name"]
    }


def get_route_fare_matrix(route_id):
    """
    Generate a full N x N stop-to-stop distance and fare matrix for a route.
    """
    stops = get_route_stops(route_id)
    if not stops:
        return {"stops": [], "matrix": []}

    stop_names = [s["stop_name"] for s in stops]
    matrix = []

    for s_from in stops:
        row = []
        for s_to in stops:
            if s_from["id"] == s_to["id"]:
                row.append({"fare": 0.0, "distance": 0.0, "same": True})
            else:
                f_data = calculate_ticket_fare(route_id, s_from["id"], s_to["id"])
                row.append({
                    "fare": f_data["fare"],
                    "distance": f_data["distance"],
                    "is_custom": f_data["is_custom"],
                    "same": False
                })
        matrix.append(row)

    return {
        "stops": stop_names,
        "stop_objects": [dict(s) for s in stops],
        "matrix": matrix
    }


def set_custom_stop_fare(route_id, from_stop_id, to_stop_id, custom_fare, custom_distance=None, notes=None):
    """Set or override a specific stop-to-stop ticket cost."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO stop_to_stop_fares (route_id, from_stop_id, to_stop_id, custom_fare, custom_distance, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(route_id, from_stop_id, to_stop_id) DO UPDATE SET
            custom_fare = excluded.custom_fare,
            custom_distance = excluded.custom_distance,
            notes = excluded.notes
    """, (
        route_id,
        from_stop_id,
        to_stop_id,
        float(custom_fare),
        float(custom_distance) if custom_distance is not None else None,
        notes or ""
    ))
    connection.commit()
    connection.close()


def get_custom_stop_fares(route_id=None):
    """Retrieve all custom override fares."""
    connection = get_connection()
    query = """
        SELECT
            sf.id,
            sf.route_id,
            r.route_name,
            sf.from_stop_id,
            s1.stop_name AS from_stop_name,
            sf.to_stop_id,
            s2.stop_name AS to_stop_name,
            sf.custom_fare,
            sf.custom_distance,
            sf.notes
        FROM stop_to_stop_fares sf
        JOIN routes r ON r.id = sf.route_id
        JOIN stops s1 ON s1.id = sf.from_stop_id
        JOIN stops s2 ON s2.id = sf.to_stop_id
    """
    params = []
    if route_id is not None:
        query += " WHERE sf.route_id = ?"
        params.append(route_id)
    query += " ORDER BY sf.id DESC"

    rows = connection.execute(query, params).fetchall()
    connection.close()
    return [dict(r) for r in rows]


def delete_custom_stop_fare(fare_id):
    """Remove a custom override fare."""
    connection = get_connection()
    connection.execute("DELETE FROM stop_to_stop_fares WHERE id = ?", (fare_id,))
    connection.commit()
    connection.close()


# ============================================================
# STOP FUNCTIONS
# ============================================================

def add_stop(stop_name, location=""):
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
    stop_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return stop_id


def stop_exists(stop_name, exclude_id=None):
    """Return whether a stop name is already registered."""
    connection = get_connection()
    query = "SELECT 1 FROM stops WHERE lower(stop_name) = lower(?)"
    parameters = [stop_name.strip()]
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
        ORDER BY stop_name
    """)
    stops = cursor.fetchall()
    connection.close()
    return stops


def delete_stop(stop_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM stop_to_stop_fares WHERE from_stop_id = ? OR to_stop_id = ?", (stop_id, stop_id))
    cursor.execute("DELETE FROM route_stops WHERE stop_id = ?", (stop_id,))
    cursor.execute("DELETE FROM stops WHERE id = ?", (stop_id,))
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

def bus_number_exists(bus_number, exclude_trip_id=None):
    """Return whether a bus number is already assigned to a trip."""
    connection = get_connection()
    query = "SELECT 1 FROM trips WHERE lower(bus_number) = lower(?)"
    params = [bus_number.strip()]
    if exclude_trip_id is not None:
        query += " AND id != ?"
        params.append(exclude_trip_id)
    exists = connection.execute(query, params).fetchone() is not None
    connection.close()
    return exists


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
            routes.destination,
            routes.base_fare,
            routes.fare_per_km
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
            routes.base_fare,
            routes.fare_per_km,
            routes.min_fare,
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
    """Return all routes and their ordered stop sequences with distances for BFS graph construction."""
    connection = get_connection()
    query = """
        SELECT
            routes.id AS route_id,
            routes.route_name,
            routes.source,
            routes.destination,
            routes.distance,
            routes.base_fare,
            routes.fare_per_km,
            stops.id AS stop_id,
            stops.stop_name,
            stops.location,
            route_stops.stop_order,
            COALESCE(route_stops.distance_from_origin, 0.0) AS distance_from_origin
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
    """Populate database with a realistic transport dataset with distances, stops, and separate fares."""
    import random
    from datetime import date, timedelta
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Clear existing data safely
    cursor.execute("DELETE FROM ridership")
    cursor.execute("DELETE FROM trips")
    cursor.execute("DELETE FROM stop_to_stop_fares")
    cursor.execute("DELETE FROM route_stops")
    cursor.execute("DELETE FROM overcrowding_alerts")
    cursor.execute("DELETE FROM fleet_rebalance_logs")
    cursor.execute("DELETE FROM routes")
    cursor.execute("DELETE FROM stops")
    
    # Reset sqlite sequences
    for tbl in ["routes", "stops", "trips", "ridership", "overcrowding_alerts", "fleet_rebalance_logs", "stop_to_stop_fares"]:
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (tbl,))
        except Exception:
            pass
        
    connection.commit()
    connection.close()
    
    # Defined routes with explicit stop distances and tailored base & per-km pricing
    sample_routes = [
        {
            "code": "101",
            "source": "Secunderabad",
            "destination": "Koti",
            "distance": 12.5,
            "base_fare": 10.0,
            "fare_per_km": 2.2,
            "min_fare": 10.0,
            "stops": ["Secunderabad", "Batas", "RTC X Roads", "Kachiguda", "Koti"],
            "stop_distances": [0.0, 3.2, 6.5, 9.8, 12.5]
        },
        {
            "code": "102",
            "source": "Hitech City",
            "destination": "Koti",
            "distance": 22.0,
            "base_fare": 12.0,
            "fare_per_km": 2.8,
            "min_fare": 12.0,
            "stops": ["Hitech City", "Madhapur", "Jubilee Hills", "Ameerpet", "Punjagutta", "Koti"],
            "stop_distances": [0.0, 3.5, 7.8, 13.2, 16.0, 22.0]
        },
        {
            "code": "103",
            "source": "Koti",
            "destination": "LB Nagar",
            "distance": 14.8,
            "base_fare": 10.0,
            "fare_per_km": 2.0,
            "min_fare": 10.0,
            "stops": ["Koti", "Malakpet", "Dilsukhnagar", "LB Nagar"],
            "stop_distances": [0.0, 4.0, 9.2, 14.8]
        },
        {
            "code": "104",
            "source": "Secunderabad",
            "destination": "Ameerpet",
            "distance": 9.2,
            "base_fare": 10.0,
            "fare_per_km": 2.5,
            "min_fare": 10.0,
            "stops": ["Secunderabad", "Begumpet", "Ameerpet"],
            "stop_distances": [0.0, 4.8, 9.2]
        },
        {
            "code": "105",
            "source": "Ameerpet",
            "destination": "LB Nagar",
            "distance": 25.0,
            "base_fare": 15.0,
            "fare_per_km": 2.4,
            "min_fare": 15.0,
            "stops": ["Ameerpet", "Punjagutta", "Koti", "Dilsukhnagar", "LB Nagar"],
            "stop_distances": [0.0, 2.8, 8.8, 18.0, 25.0]
        }
    ]
    
    route_ids = []
    for r in sample_routes:
        r_id = add_route(
            route_name=r["code"],
            source=r["source"],
            destination=r["destination"],
            distance=r["distance"],
            stop_names=r["stops"],
            base_fare=r["base_fare"],
            fare_per_km=r["fare_per_km"],
            min_fare=r["min_fare"],
            stop_distances=r["stop_distances"]
        )
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
            
    # Generate 30 days of historical ridership
    route_demand_profiles = {
        1: 60,
        2: 74,
        3: 42,
        4: 16,
        5: 18
    }

    for trip_id, r_id in created_trips:
        base_demand = route_demand_profiles.get(r_id, 35)
        for d in range(30, 0, -1):
            past_date = today - timedelta(days=d)
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