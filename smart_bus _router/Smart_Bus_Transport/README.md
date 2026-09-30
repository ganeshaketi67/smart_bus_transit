# Smart Bus Transport — Intelligent City Transit System

A modern, app-like smart transit platform for bus-route planning, scheduling, passenger navigation, and database-backed fleet operations.

## Project Layout

- `algorithms/` - Route and graph BFS algorithms
- `app/` - Streamlit modern app interface, passenger app, operator backend, and database access
- `assets/` - Static resources & styling
- `data/` - Datasets & network resources
- `database/` - SQLite database schema & migrations
- `oop_java/` - Domain model and timetable conflict detection

## Getting Started

Launch the application using the project virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app/main.py
```

The app uses SQLite database storage (`database/smart_transit.db`).

## Core Features & Architecture

### 📱 1. Passenger App Experience
- **⏱️ Bus Times & Stops**: Live city departure timetables, intermediate stop sequence timelines, and terminal routes.
- **🤖 AI Transit Assistant**: Real-time conversational AI grounded in live database records to answer schedule questions, route suggestions, and travel guidance.
- **📸 Report Overcrowded Bus**: Instant photo upload and crowd reporting allowing dispatchers to deploy backup buses.
- **🗺️ Route Finder**: BFS-powered shortest journey planner with transfer and step-by-step connection itineraries.

### 🏢 2. Operator Control Center
- **📊 Executive Dashboard**: Database-backed route, stop, trip, ridership, and fare-weighted revenue metrics from yesterday onward, with a manual refresh control.
- **🚨 Overcrowded Bus Alert Desk**: Queue of passenger photo reports with one-click extra bus deployment.
- **🚌 Routes & Stop Sequences**: Manage city lines, distances, and custom intermediate stop orders.
- **📍 Stops & ⏱️ Trips**: Manage bus stops and departure timetables, including editing a trip's route code, bus, date, and times.
- **👥 Ridership Logs**: Passenger totals and route averages use records from yesterday onward; daily averages include every calendar day in that period.
- **⚡ Frequency Planner**: Calculates recommended trips/day using formula:
  $$\text{Recommended Trips/Day} = \lceil \text{Avg Daily Passengers} / \text{Target Bus Capacity} \rceil$$
- **🗓️ Schedule & Conflicts**: OOP-based timetable collision and double-booking detection engine.