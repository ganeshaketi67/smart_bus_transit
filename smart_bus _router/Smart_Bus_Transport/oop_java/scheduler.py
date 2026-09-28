"""
Object-Oriented Scheduling Model matching OOPJ specifications.
Provides Bus, Route, Trip, and Scheduler classes for transport scheduling and collision detection.
"""

from typing import List, Optional, Tuple


class Bus:
    def __init__(self, registration_number: str, capacity: int = 50):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero")
        self.registration_number = registration_number
        self.capacity = capacity

    def __repr__(self):
        return f"<Bus {self.registration_number} ({self.capacity} seats)>"


class Route:
    def __init__(self, name: str, origin: str, destination: str, distance: float = 0.0):
        self.name = name
        self.origin = origin
        self.destination = destination
        self.distance = distance

    def __repr__(self):
        return f"<Route {self.name}: {self.origin} -> {self.destination}>"


class Trip:
    def __init__(
        self,
        trip_id: int,
        route: Route,
        bus: Bus,
        trip_date: str,
        departure_time: str,
        arrival_time: str
    ):
        self.trip_id = trip_id
        self.route = route
        self.bus = bus
        self.trip_date = trip_date
        self.departure_time = departure_time
        self.arrival_time = arrival_time

    def is_overlapping(self, other: "Trip") -> bool:
        """Check if this trip overlaps with another trip for the same bus on the same date."""
        if self.bus.registration_number.lower() != other.bus.registration_number.lower():
            return False
        if self.trip_date != other.trip_date:
            return False
        # Overlap check
        return not (self.arrival_time <= other.departure_time or self.departure_time >= other.arrival_time)

    def __repr__(self):
        return f"<Trip #{self.trip_id} Bus {self.bus.registration_number} {self.departure_time}-{self.arrival_time}>"


class Scheduler:
    def __init__(self):
        self._trips: List[Trip] = []

    def add_trip(self, trip: Trip) -> Tuple[bool, str]:
        """Add trip after checking for bus schedule collisions."""
        for existing in self._trips:
            if existing.trip_id != trip.trip_id and trip.is_overlapping(existing):
                return False, f"Schedule conflict with Trip #{existing.trip_id} ({existing.departure_time} - {existing.arrival_time})"
        self._trips.append(trip)
        return True, "Trip scheduled successfully"

    def get_trips(self) -> List[Trip]:
        return list(self._trips)

    def get_conflicts(self) -> List[Tuple[Trip, Trip]]:
        """Return all conflicting pairs of trips in the schedule."""
        conflicts = []
        n = len(self._trips)
        for i in range(n):
            for j in range(i + 1, n):
                t1 = self._trips[i]
                t2 = self._trips[j]
                if t1.is_overlapping(t2):
                    conflicts.append((t1, t2))
        return conflicts
