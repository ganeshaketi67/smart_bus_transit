SMART BUS TRANSPORT

Intelligent City Transit System

Problem Statement A city transport corporation lacks structured
route-stop-trip data to plan bus frequency.

# 1. Abstract

Smart Bus Transport is a database-backed city transit application
designed to organize routes, stops, trips and ridership data and convert
that information into useful operational decisions. The system provides
a passenger-facing experience for bus timings, route finding,
AI-assisted transit queries and overcrowding reporting, together with an
operator control center for route management, trip scheduling, ridership
logging, frequency planning and schedule-conflict detection.

The project uses SQLite for structured transit data, Streamlit for the
user interface, Breadth-First Search (BFS) for shortest stop-to-stop
navigation, object-oriented scheduling models for conflict analysis, and
Python analytics for ridership-based frequency planning. A regression
forecasting module is retained in the codebase as an academic Python/ML
component, even though the current operator navigation does not expose a
separate Demand Forecast tab.

# 2. Problem Statement

A city transport corporation lacks structured route-stop-trip data to
plan bus frequency.

In a city bus network, routes, intermediate stops, scheduled trips, bus
numbers and passenger loads are strongly connected. When these records
are not organized in a common system, operators find it difficult to
understand which routes are busy, where buses are overcrowded, whether a
vehicle has conflicting schedules, and how many trips should be operated
on each route.

# 3. Objectives

-   Maintain structured Route, Stop, Trip and Ridership records.

-   Allow passengers to view bus timings and intermediate stop
    sequences.

-   Find a minimum-hop path between bus stops using BFS.

-   Support direct routes and transfer-based journeys.

-   Record passenger ridership and use it for operational analysis.

-   Recommend route frequency using passenger demand and target bus
    capacity.

-   Detect overlapping bus assignments and timetable conflicts.

-   Allow passengers to report overcrowded buses for operator action.

-   Provide an optional AI transit assistant grounded in current
    database records.

-   Demonstrate syllabus concepts from DBMS, DMGT, ADSA, OOPJ and
    Python.

# 4. Scope of the System

## 4.1 Passenger Application

## 4.2 Operator Control Center

# 5. Technology Stack

# 6. System Architecture

The application follows a simple layered design:

Passenger / Operator UI ↓ Streamlit Application Layer ↓ Business Logic &
Algorithms (BFS • Frequency Planner • Conflict Detection • AI Assistant)
↓ SQLite Database (Routes • Stops • Route Stops • Trips • Ridership •
Overcrowding Alerts)

# 7. Database Design

The SQLite database is created automatically by the application.
Foreign-key support is enabled so related records can be managed
consistently.

## 7.1 Conceptual Relationships

A Route contains an ordered sequence of Stops. A Route can have many
Trips. A Trip can have Ridership records. Overcrowding Alerts can refer
to a route/bus/stop situation. These relationships provide the
structured route-stop-trip data required by the problem statement.

# 8. Route Network and BFS

The route network is represented as a graph. Each bus stop acts as a
node and each connection between consecutive stops acts as an edge. The
application builds an adjacency list from the ordered route-stop
records.

Breadth-First Search explores the graph level by level. It is suitable
for finding a minimum-hop path in an unweighted stop network. The route
finder also groups consecutive legs served by the same route so that it
can display transfer segments.

Example: Secunderabad → Paradise → Begumpet → Ameerpet. If the passenger
needs another route after Ameerpet, the itinerary can identify that
point as a transfer.

# 9. Ridership and Frequency Planning

Ridership records represent the number of passengers associated with
trips. The operator can use these records to compare route demand and
determine whether the current number of scheduled trips is sufficient.

The implemented frequency planner uses the formula:

Recommended Trips/Day = ceil(Average Daily Passengers ÷ Target Bus
Capacity)

The planner compares recommended trips with current scheduled trips and
marks a route as requiring additional trips, having a surplus, or being
approximately balanced. This directly supports the main project goal:
bus-frequency planning.

# 10. Ridership Forecasting Module

The project contains a Python forecasting module that can train Linear
Regression or Polynomial Regression on historical date-wise passenger
counts. It can calculate fitted historical values, an R² score, a
passenger trend slope and future passenger estimates.

The current operator sidebar intentionally does not expose a separate
Demand Forecast page. Forecasting can therefore be treated as an
academic/advanced analytics module or later integrated into Ridership
without adding another major navigation tab.

# 11. Scheduling and Conflict Detection

Trips contain a bus number, route and timing information. Before or
during scheduling, the system can identify cases where the same bus is
assigned to overlapping time periods. The project also includes
object-oriented Bus, Route, Trip and Scheduler models, supporting the
OOPJ component of the syllabus.

This feature helps prevent double-booking of a vehicle and improves
schedule reliability.

# 12. Overcrowding Alert Workflow

-   Passenger selects the relevant route and current stop.

-   Passenger submits an overcrowding report and may provide supporting
    information.

-   The report is stored in the database.

-   The operator opens the Overcrowded Bus Alert Desk.

-   Pending alerts can be reviewed and resolved/acted upon.

-   The alert information can support extra-bus deployment or future
    frequency adjustments.

# 13. AI Transit Assistant

The optional AI assistant builds a live text snapshot from the SQLite
database, including routes, stop sequences, trips, ridership analytics
and overcrowding alerts. When a Gemini API key is configured, the
snapshot is supplied as grounding context for passenger or operator
questions.

The core transit system does not depend on AI to store routes, find BFS
paths, schedule trips or calculate frequency. Therefore, the project
remains functional even if the AI API is unavailable.

# 14. Academic / Syllabus Mapping

# 15. Functional Requirements

-   The system shall allow operators to create, update and delete
    routes.

-   The system shall maintain ordered intermediate stops for routes.

-   The system shall allow trips to be scheduled with a bus number and
    times.

-   The system shall record trip-level ridership.

-   The system shall display passenger bus times and stop information.

-   The system shall find a path between valid stops.

-   The system shall calculate frequency recommendations from ridership
    data.

-   The system shall warn about bus schedule conflicts.

-   The system shall accept and manage overcrowding reports.

-   The system may provide AI-based transit assistance when configured.

# 16. Non-Functional Requirements

-   Usability: interface should be simple enough for passengers and
    transport operators.

-   Performance: normal database and route-search operations should
    respond quickly for a demonstration-scale city network.

-   Reliability: database records should persist between application
    sessions.

-   Maintainability: routes, algorithms, database logic and scheduling
    models are separated into modules.

-   Security: API keys should be stored outside source code and should
    never be committed to a public repository.

-   Portability: the Python application can run on a standard system
    with Python and the required packages.

# 17. Project Folder Structure

Smart_Bus_Transport/ ├── app/ │ ├── main.py │ ├── database.py │ ├──
ai_assistant.py │ └── ui.py ├── algorithms/ │ └── bfs.py ├──
forecasting/ │ └── ridership.py ├── oop_java/ │ ├── Bus.java │ ├──
Route.java │ ├── Trip.java │ ├── Scheduler.java │ └── scheduler.py ├──
database/ │ └── smart_transit.db ├── data/ ├── assets/ └── README.md

# 18. Installation and Execution

Recommended development setup:

1.  Open the Smart_Bus_Transport project folder.

2.  Create a virtual environment: python -m venv .venv

3.  Activate it on Windows PowerShell:
    ..venv`\Scripts`{=tex}`\Activate`{=tex}.ps1

4.  Install project dependencies from requirements.txt.

5.  Run the application: streamlit run app/main.py

6.  Open the local Streamlit URL shown in the terminal.

Note: SQLite is part of Python's standard library and does not require a
separate pip package.

# 19. Sample Demonstration Scenario

During a demonstration, the operator can create the route, add its stop
sequence, schedule AP09-B-1001, record passenger counts, inspect
frequency recommendations and use the Route Finder to search between
connected stops.

# 20. Advantages

-   Centralizes route-stop-trip information.

-   Makes bus-network connections easy to search.

-   Supports data-driven frequency planning.

-   Helps identify overcrowding and scheduling problems.

-   Provides separate passenger and operator experiences.

-   Demonstrates multiple academic subjects in one practical system.

# 21. Limitations

-   The current system is a prototype and does not use live GPS vehicle
    positions.

-   BFS optimizes number of stop hops, not real-time traffic or travel
    time.

-   Frequency recommendations are based on recorded ridership and a
    capacity formula rather than a full operations-research model.

-   AI responses require external Gemini configuration and should not be
    treated as authoritative when data is missing.

-   Regression forecasts depend strongly on the quantity and quality of
    historical ridership data.

# 22. Future Enhancements

-   Live GPS bus tracking and ETA prediction.

-   Traffic-aware route optimization using weighted shortest-path
    algorithms.

-   Integrate forecasting directly into the Ridership page.

-   Automatic dispatch recommendations after repeated overcrowding
    alerts.

-   Role-based login for passengers, dispatchers and administrators.

-   Mobile-first passenger interface and notifications.

-   Real TGSRTC/open transit feeds where legally and technically
    available.

# 23. Conclusion

Smart Bus Transport converts scattered transit information into a
structured and usable city-bus planning system. By combining relational
data management, graph-based route finding, object-oriented scheduling
and ridership analytics, the project addresses the original need for
structured route-stop-trip data and better bus-frequency planning. The
prototype is suitable for demonstrating both practical application
development and the mapped DBMS, DMGT, ADSA, OOPJ and Python concepts.

# 24. Viva Quick Summary

One-line explanation: Smart Bus Transport is a Streamlit and SQLite
based city-bus management system that stores routes, stops, trips and
ridership, uses BFS for route finding, checks scheduling conflicts and
recommends bus frequency from passenger demand.

# Appendix: Project Tables

| Project Domain \| Smart Public Transportation \|

| --- \| --- \|

| Application \| Streamlit + SQLite \|

| Core Algorithms \| Graph / Breadth-First Search (BFS) \|

| Analytics \| Ridership Analysis & Frequency Planning \|

| Academic Mapping \| DBMS • DMGT • ADSA • OOPJ • Python \|

| Module \| Purpose \|

| --- \| --- \|

| Bus Times & Stops \| Shows available routes, stop sequences and
  scheduled departures. \|

| AI Transit Assistant \| Answers route, stop, schedule and transit
  questions using live database context when Gemini is configured. \|

| Report Overcrowded Bus \| Allows a passenger to submit an overcrowding
  report with route, stop and supporting information. \|

| Route Finder \| Uses the bus-stop graph and BFS to find a shortest
  stop path and transfer itinerary. \|

| Module \| Purpose \|

| --- \| --- \|

| Dashboard \| Displays operational KPIs, ridership information and
  quick actions. \|

| Overcrowded Bus Alerts \| Shows passenger reports and supports
  dispatch/resolve workflow. \|

| Routes \| Creates and manages source-to-destination routes and
  intermediate stops. \|

| Stops \| Builds and updates intermediate stop corridors. \|

| Trips \| Schedules buses with registration numbers, departure and
  arrival times. \|

| Ridership \| Stores passenger counts for scheduled trips. \|

| Frequency Planner \| Calculates recommended trips per day from average
  passengers and target bus capacity. \|

| Schedule & Conflicts \| Checks for overlapping bus assignments using
  scheduling objects. \|

| Technology \| Use \|

| --- \| --- \|

| Python \| Main application logic, analytics and algorithms. \|

| Streamlit \| Web-based app/dashboard interface. \|

| SQLite \| Persistent relational database. \|

| Pandas \| Tabular data manipulation and reporting. \|

| Plotly \| Interactive charts and dashboard visualizations. \|

| scikit-learn \| Linear/Polynomial regression in the forecasting
  module. \|

| BFS / collections.deque \| Shortest-path search through the stop
  network. \|

| Java OOP \| Bus, Route, Trip and Scheduler domain models for syllabus
  mapping. \|

| Google Gemini (optional) \| Conversational transit assistant when an
  API key/package is available. \|

| Table \| Main Purpose \|

| --- \| --- \|

| routes \| Stores route identity, route name/code, source, destination
  and distance. \|

| stops \| Stores registered bus-stop names. \|

| route_stops \| Connects routes to ordered stop sequences. \|

| trips \| Stores scheduled bus runs, bus number, route,
  departure/arrival and trip date. \|

| ridership \| Stores passenger counts associated with trips. \|

| overcrowding_alerts \| Stores crowd reports and their operational
  status. \|

| Subject \| Project Mapping \|

| --- \| --- \|

| DBMS U1 \| ER-style modeling of Route, Stop, Trip, Ridership and
  related entities. \|

| DBMS U2 \| Relational storage and SQL-based retrieval/analytics. \|

| DMGT U2 \| Relations between routes, stops and connected stop pairs.
  \|

| ADSA U2 \| Transit network represented as a graph. \|

| BFS \| Minimum-hop route search between stops. \|

| OOPJ \| Bus, Route, Trip and Scheduler classes; scheduling logic. \|

| Python \| Streamlit application, analytics, BFS integration and
  regression forecasting. \|

| Field \| Demo Value \|

| --- \| --- \|

| Route Code \| 101 \|

| Bus Number \| AP09-B-1001 \|

| Origin \| Secunderabad \|

| Intermediate Stops \| Paradise → Begumpet → Ameerpet → Punjagutta \|

| Destination \| Mehdipatnam \|

| Question \| Short Answer \|

| --- \| --- \|

| Why DBMS? \| To store and retrieve structured route, stop, trip and
  ridership data. \|

| Why BFS? \| To find a minimum-hop path between connected bus stops. \|

| Why ridership? \| It measures passenger demand and supports frequency
  decisions. \|

| Why Frequency Planner? \| To compare current trips with trips required
  for passenger demand. \|

| Why OOP? \| To model Bus, Route, Trip and Scheduler as reusable
  objects. \|

| Why Python? \| For the Streamlit app, algorithms, analytics and
  optional regression forecasting. \|
