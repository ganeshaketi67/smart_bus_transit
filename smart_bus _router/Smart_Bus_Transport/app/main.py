import sys
from pathlib import Path
from datetime import date, datetime, time
import math

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to python path
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from database import (
    create_database,
    get_routes,
    get_route_by_id,
    get_stops,
    get_trips,
    get_ridership,
    get_route_stops,
    replace_route_stops,
    bus_number_exists,
    route_exists,
    route_code_exists,
    add_route,
    delete_ridership,
    delete_trip,
    update_ridership,
    update_stop,
    update_trip,
    update_route,
    delete_route,
    route_has_trips,
    add_stop,
    delete_stop,
    add_trip,
    add_ridership,
    get_route_ridership_analytics,
    get_network_graph_data,
    check_bus_schedule_conflict,
    seed_demo_data,
    add_overcrowding_alert,
    get_overcrowding_alerts,
    resolve_overcrowding_alert,
    get_ridership_with_trips,
    get_trips_with_routes,
    calculate_ticket_fare,
    get_route_fare_matrix,
    update_route_fare_pricing,
    update_route_stop_distances,
    auto_distribute_route_stop_distances,
    set_custom_stop_fare,
    get_custom_stop_fares,
    delete_custom_stop_fare
)
from algorithms.bfs import build_graph_from_db, find_detailed_path
from oop_java.scheduler import Bus as OOPBus, Route as OOPRoute, Trip as OOPTrip, Scheduler as OOPScheduler
from ai_assistant import (
    answer_with_gemini,
    dynamic_database_search_response,
    get_stored_api_key,
    save_api_key,
    get_available_gemini_models,
    build_live_transit_context
)


# Initialize Database & Auto-migrations
create_database()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Transit — Intelligent City Bus Router",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ULTRA-MODERN APP-LIKE DESIGN SYSTEM (CSS)
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --primary: #38bdf8;
    --primary-glow: rgba(56, 189, 248, 0.25);
    --secondary: #818cf8;
    --accent: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --bg-dark: #090d16;
    --card-bg: #131b2e;
    --card-border: rgba(255, 255, 255, 0.08);
    --card-border-hover: rgba(56, 189, 248, 0.35);
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
}

.stApp {
    background-color: var(--bg-dark);
    background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(129, 140, 248, 0.06) 0px, transparent 50%);
    color: var(--text-main);
}

.block-container {
    max-width: 1400px;
    padding-top: 1.2rem;
    padding-bottom: 2.5rem;
}

/* Sidebar App Header */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}

/* App Hero Banner */
.app-hero-header {
    background: linear-gradient(135deg, #131d33 0%, #0c1424 100%);
    border: 1px solid rgba(56, 189, 248, 0.18);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.app-hero-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
}

.app-hero-title {
    font-size: 28px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #ffffff, #e0f2fe, #bae6fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 12px;
}

.app-hero-desc {
    color: #94a3b8 !important;
    margin-top: 6px;
    font-size: 14px;
    font-weight: 400;
    max-width: 850px;
}

/* App Pill Badges */
.app-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.pill-passenger {
    background: rgba(16, 185, 129, 0.15);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.pill-operator {
    background: rgba(56, 189, 248, 0.15);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

.pill-fare {
    background: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.pill-live {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
    animation: pulseGlow 2s infinite;
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
    100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

/* Stat / KPI Cards */
.stat-card {
    background: linear-gradient(145deg, #131c30 0%, #0e1626 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-3px);
    border-color: rgba(56, 189, 248, 0.4);
}

.stat-icon {
    font-size: 26px;
    margin-bottom: 8px;
}

.stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #94a3b8;
    font-weight: 700;
}

.stat-val {
    font-size: 26px;
    font-weight: 800;
    color: #f8fafc;
    margin: 4px 0;
}

.stat-sub {
    font-size: 11px;
    color: #38bdf8;
    font-weight: 600;
}

/* Digital Boarding Pass / Ticket */
.ticket-pass-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 2px dashed rgba(56, 189, 248, 0.4);
    border-radius: 20px;
    padding: 24px;
    position: relative;
    box-shadow: 0 12px 36px rgba(0,0,0,0.5);
    margin: 15px 0;
}

.ticket-pass-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 12px;
    margin-bottom: 16px;
}

.ticket-fare-highlight {
    font-size: 32px;
    font-weight: 800;
    color: #38bdf8;
    text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
}

.ticket-qr-mock {
    width: 90px;
    height: 90px;
    background: #ffffff;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* Stop Sequence Timeline & Pills */
.stop-pill {
    display: inline-block;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px;
    font-size: 13px;
    color: #e2e8f0;
}

.stop-pill-active {
    display: inline-block;
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px;
    font-size: 13px;
    font-weight: 700;
    border: 1px solid transparent;
}

.bus-departure-chip {
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    margin-top: 6px;
}

.badge-optimal {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# APP SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 16px 0; text-align: center;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: linear-gradient(135deg, #0284c7, #6366f1); border-radius: 16px; box-shadow: 0 8px 20px rgba(2, 132, 199, 0.35); font-size: 28px; margin-bottom: 8px;">
                🚌
            </div>
            <h2 style="color: #f8fafc; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.3px;">Smart Transit</h2>
            <p style="color: #38bdf8; font-size: 12px; margin: 2px 0 0 0; font-weight: 600;">Next-Gen City Bus Network</p>
        </div>
    """, unsafe_allow_html=True)

    st.caption("SELECT INTERFACE")
    app_mode = st.radio(
        "Interface Mode",
        ["📱 Passenger App", "🏢 Operator Backend"],
        key="app_mode_radio",
        label_visibility="collapsed"
    )

    st.divider()

    if app_mode == "📱 Passenger App":
        st.markdown('<div class="app-pill pill-passenger">📱 PASSENGER APP</div>', unsafe_allow_html=True)
        st.caption("NAVIGATION")

        PASSENGER_OPTIONS = [
            "⏱️ Bus Times & Stops",
            "🎟️ Ticket Fare & Pass Calculator",
            "🤖 AI Transit Assistant",
            "📸 Report Overcrowded Bus",
            "🗺️ Route Finder",
        ]

        if "pending_passenger_page" in st.session_state and st.session_state["pending_passenger_page"]:
            st.session_state["passenger_radio"] = st.session_state.pop("pending_passenger_page")

        if "passenger_radio" not in st.session_state or st.session_state["passenger_radio"] not in PASSENGER_OPTIONS:
            st.session_state["passenger_radio"] = "⏱️ Bus Times & Stops"

        def navigate_passenger(page_name):
            st.session_state["pending_passenger_page"] = page_name

        page = st.radio(
            "Passenger Menu",
            PASSENGER_OPTIONS,
            key="passenger_radio",
            label_visibility="collapsed"
        )
    else:
        st.markdown('<div class="app-pill pill-operator">🏢 OPERATOR CONTROL</div>', unsafe_allow_html=True)
        st.caption("OPERATIONS MENU")

        OPERATOR_OPTIONS = [
            "📊 Dashboard",
            "💰 Fare & Distance Pricing Manager",
            "🚨 Overcrowded Bus Alerts",
            "🚌 Routes",
            "📍 Stops",
            "⏱️ Trips",
            "👥 Ridership",
            "⚡ Frequency Planner",
            "🗓️ Schedule & Conflicts",
        ]

        if "pending_operator_page" in st.session_state and st.session_state["pending_operator_page"]:
            st.session_state["operator_radio"] = st.session_state.pop("pending_operator_page")

        if "operator_radio" not in st.session_state or st.session_state["operator_radio"] not in OPERATOR_OPTIONS:
            st.session_state["operator_radio"] = "📊 Dashboard"

        def navigate_operator(page_name):
            st.session_state["pending_operator_page"] = page_name

        page = st.radio(
            "Operator Menu",
            OPERATOR_OPTIONS,
            key="operator_radio",
            label_visibility="collapsed"
        )

    # API Key & Model silent loading
    saved_key = get_stored_api_key()
    if "gemini_api_key" not in st.session_state:
        st.session_state["gemini_api_key"] = saved_key
    if "selected_gemini_model" not in st.session_state:
        st.session_state["selected_gemini_model"] = "gemini-3.8-flash"

    st.caption("SYSTEM UTILITIES")
    if st.button("🌱 Populate Sample City Data", use_container_width=True):
        n_r, n_t = seed_demo_data()
        st.sidebar.success(f"Loaded {n_r} routes & {n_t} trips with live data & distance-based fares!")
        st.rerun()

    st.caption("NETWORK TELEMETRY")
    st.markdown('<div class="app-pill pill-live">🟢 Network Live • SQLite Online</div>', unsafe_allow_html=True)


# Load fresh DB records
routes = [dict(route) for route in get_routes()]
stops = get_stops()
trips = get_trips()
ridership = get_ridership()
alerts = get_overcrowding_alerts()


def _get_route_schedule_rows(route_id):
    return [{
        "Bus Number": trip["bus_number"],
        "Trip Date": trip["trip_date"] or "Not set",
        "Departure": trip["departure"],
        "Arrival": trip["arrival"],
    } for trip in trips if trip["route_id"] == route_id]


# ============================================================
# PASSENGER APP SECTION
# ============================================================

if app_mode == "📱 Passenger App":

    # --------------------------------------------------------
    # 1. BUS TIMES & STOPS
    # --------------------------------------------------------
    if page == "⏱️ Bus Times & Stops":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">⏱️ City Bus Timetables & Stops</div>
                <div class="app-hero-desc">Explore upcoming departures, route schedules, intermediate stop sequences, and distance-based ticket fares.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes:
            st.info("No transit routes loaded yet. Click '🌱 Populate Sample City Data' in the sidebar to load city bus data!")
        else:
            all_stops_list = sorted(list(set([s["stop_name"] for s in stops] + [r["source"] for r in routes] + [r["destination"] for r in routes])))
            if "psg_origin" not in st.session_state or st.session_state["psg_origin"] not in all_stops_list:
                st.session_state["psg_origin"] = all_stops_list[0]
            if "psg_dest" not in st.session_state or st.session_state["psg_dest"] not in all_stops_list:
                st.session_state["psg_dest"] = all_stops_list[min(len(all_stops_list)-1, 1)] if len(all_stops_list) > 1 else all_stops_list[0]

            with st.container(border=True):
                st.markdown("#### 🔍 Journey Stop & Fare Selector")
                c_src, c_swap, c_dst = st.columns([5, 2, 5])
                with c_src:
                    sel_origin = c_src.selectbox("Boarding Location (Origin)", all_stops_list, index=all_stops_list.index(st.session_state["psg_origin"]))
                    st.session_state["psg_origin"] = sel_origin
                with c_swap:
                    st.write("")
                    st.write("")
                    if st.button("⇄ Swap", use_container_width=True, key="swap_btn_times"):
                        st.session_state["psg_origin"], st.session_state["psg_dest"] = st.session_state["psg_dest"], st.session_state["psg_origin"]
                        st.rerun()
                with c_dst:
                    sel_dest = c_dst.selectbox("Arrival Location (Destination)", all_stops_list, index=all_stops_list.index(st.session_state["psg_dest"]))
                    st.session_state["psg_dest"] = sel_dest

            st.write("")
            st.markdown("### 🚌 Available Bus Routes & Departures")

            # Filter matching routes
            matching_routes = []
            for r in routes:
                r_stops = [s["stop_name"].lower() for s in get_route_stops(r["id"])]
                if not r_stops:
                    r_stops = [r["source"].lower(), r["destination"].lower()]

                if sel_origin.lower() in r_stops and sel_dest.lower() in r_stops:
                    matching_routes.append(r)

            if not matching_routes:
                st.info(f"Showing all routes. (No single direct route covers **{sel_origin}** ➔ **{sel_dest}**. Check **🗺️ Route Finder** for connecting transfers).")
                display_routes = routes
            else:
                display_routes = matching_routes

            for r in display_routes:
                stops_seq = get_route_stops(r["id"])
                r_trips = [t for t in trips if t["route_id"] == r["id"]]

                # Calculate distance and fare for this specific route between selected stops
                fare_calc = calculate_ticket_fare(r["id"], sel_origin, sel_dest)

                # Detect if passenger query is in the return / reverse direction
                seq_names = [s["stop_name"] for s in stops_seq] if stops_seq else [r["source"], r["destination"]]
                seq_lower = [name.lower() for name in seq_names]

                is_return_trip = False
                if sel_origin.lower() in seq_lower and sel_dest.lower() in seq_lower:
                    orig_idx = seq_lower.index(sel_origin.lower())
                    dest_idx = seq_lower.index(sel_dest.lower())
                    if orig_idx > dest_idx:
                        is_return_trip = True
                        seq_names = seq_names[::-1]  # Reverse for return trip

                with st.container(border=True):
                    col_header_l, col_header_r = st.columns([7, 5])
                    with col_header_l:
                        if is_return_trip:
                            st.markdown(f"### 🚌 Route {r['route_name']} &nbsp;•&nbsp; `{r['destination']} ➔ {r['source']}` <span class='badge-optimal' style='font-size:11px; margin-left:6px;'>🔁 Return Trip</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"### 🚌 Route {r['route_name']} &nbsp;•&nbsp; `{r['source']} ➔ {r['destination']}`", unsafe_allow_html=True)
                        st.caption(f"Route Total: **{r['distance']} km** | Active Daily Runs: **{len(r_trips)}**")

                    with col_header_r:
                        st.markdown(f"""
                            <div style="text-align: right;">
                                <span class="app-pill pill-fare" style="font-size:13px; font-weight:800;">
                                    🏷️ Ticket Fare: ₹{fare_calc['fare']} ({fare_calc['distance']} km)
                                </span>
                            </div>
                        """, unsafe_allow_html=True)

                    # Stop Sequence (rendered in travel direction)
                    if seq_names:
                        pill_html = " ➔ ".join([
                            f'<span class="stop-pill-active" style="background:rgba(16,185,129,0.2); border-color:#10b981; color:#86efac;">🟢 {name} (Boarding)</span>' if name.lower() == sel_origin.lower() else
                            (f'<span class="stop-pill-active" style="background:rgba(56,189,248,0.2); border-color:#38bdf8; color:#7dd3fc;">🏁 {name} (Destination)</span>' if name.lower() == sel_dest.lower() else
                            f'<span class="stop-pill">📍 {name}</span>')
                            for name in seq_names
                        ])
                        direction_label = "Return Journey Stop Flow" if is_return_trip else "Outbound Stop Flow"
                        st.markdown(f"<div style='margin: 10px 0;'><strong>📍 Route {direction_label}:</strong><br>{pill_html}</div>", unsafe_allow_html=True)

                    # Scheduled departures
                    if r_trips:
                        st.markdown("**Upcoming Scheduled Bus Runs:**")
                        t_cols = st.columns(min(len(r_trips), 4))
                        for idx, t_item in enumerate(r_trips[:4]):
                            with t_cols[idx]:
                                is_first = idx == 0
                                st.markdown(f"""
                                    <div class="bus-departure-chip">
                                        <div style="color: #38bdf8; font-weight: 700; font-size: 15px;">🚌 {t_item['bus_number']}</div>
                                        <div style="color: #ffffff; font-size: 14px; font-weight: 700; margin: 4px 0;">Dep: {t_item['departure']}</div>
                                        <div style="color: #94a3b8; font-size: 12px;">Arr: {t_item['arrival']}</div>
                                        {"<span class='badge-optimal' style='font-size:10px; margin-top:4px; display:inline-block;'>⚡ NEXT BUS</span>" if is_first else ""}
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.caption("No upcoming bus runs scheduled for today on this route.")


    # --------------------------------------------------------
    # 2. TICKET FARE & PASS CALCULATOR (NEW DEDICATED PASSENGER TOOL)
    # --------------------------------------------------------
    elif page == "🎟️ Ticket Fare & Pass Calculator":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🎟️ Distance-Based Fare & Digital Ticket Generator</div>
                <div class="app-hero-desc">Calculate the exact ticket cost between any boarding and alighting stop on each route based on traversed distance, and generate a digital boarding pass.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes:
            st.info("No transit routes loaded yet. Click '🌱 Populate Sample City Data' in the sidebar.")
        else:
            col_calc_left, col_calc_right = st.columns([6, 6])

            with col_calc_left:
                with st.container(border=True):
                    st.markdown("### 🚌 Select Route & Journey Stops")
                    
                    route_choices = {f"Route {r['route_name']}: {r['source']} ➔ {r['destination']} ({r['distance']} km)": r for r in routes}
                    sel_r_label = st.selectbox("Select Transit Line", list(route_choices.keys()))
                    chosen_route = route_choices[sel_r_label]

                    # Get stops for this route
                    r_stops_data = get_route_stops(chosen_route["id"])
                    if not r_stops_data:
                        r_stops_list = [chosen_route["source"], chosen_route["destination"]]
                    else:
                        r_stops_list = [s["stop_name"] for s in r_stops_data]

                    c_b1, c_b2 = st.columns(2)
                    with c_b1:
                        board_stop = st.selectbox("🟢 Boarding Stop", r_stops_list, index=0)
                    with c_b2:
                        alight_stop = st.selectbox("🏁 Alighting Stop", r_stops_list, index=min(len(r_stops_list)-1, len(r_stops_list)-1))

                    st.markdown("---")
                    st.markdown("#### 👥 Passenger & Concession Options")
                    c_p1, c_p2 = st.columns(2)
                    with c_p1:
                        passenger_type = st.selectbox(
                            "Passenger Category",
                            ["Standard Adult (100%)", "Student Pass (50% Off)", "Senior Citizen (30% Off)", "Child / Minor (50% Off)"]
                        )
                    with c_p2:
                        passenger_count = st.number_input("Number of Tickets", min_value=1, max_value=10, value=1)

                    # Compute Fare
                    fare_res = calculate_ticket_fare(chosen_route["id"], board_stop, alight_stop)
                    base_fare_unit = fare_res["fare"]
                    
                    discount_rate = 1.0
                    if "Student" in passenger_type or "Child" in passenger_type:
                        discount_rate = 0.5
                    elif "Senior" in passenger_type:
                        discount_rate = 0.7

                    unit_fare_final = max(float(chosen_route.get("min_fare", 10.0)), round(base_fare_unit * discount_rate))
                    total_fare_payable = unit_fare_final * passenger_count

                    st.markdown("---")
                    st.markdown("#### 📊 Ticket Cost Formula Breakdown")
                    st.markdown(f"""
                        - **Distance Between Stops:** `{fare_res['distance']} km`
                        - **Route Pricing Rule:** Base Fare `₹{fare_res['base_fare']}` + `₹{fare_res['fare_per_km']}/km`
                        - **Calculated Unit Ticket Cost:** `₹{unit_fare_final}` per passenger
                        - **Total Payable ({passenger_count} Passenger{'s' if passenger_count > 1 else ''}):** <span style="font-size:22px; font-weight:800; color:#38bdf8;">₹{total_fare_payable:,.0f}</span>
                    """, unsafe_allow_html=True)

            with col_calc_right:
                # Digital Ticket Pass Widget
                with st.container(border=True):
                    st.markdown("### 🎫 Digital QR Transit Pass")
                    st.caption("Live simulated electronic ticket with distance and fare stamp:")

                    ticket_id = f"TKT-HYD-{chosen_route['route_name']}-{abs(hash(board_stop + alight_stop + str(datetime.now().minute))) % 100000:05d}"
                    now_str = datetime.now().strftime("%d %b %Y • %H:%M:%S")

                    # Find upcoming trip for this route
                    route_trips = [t for t in trips if t["route_id"] == chosen_route["id"]]
                    next_bus = route_trips[0]["bus_number"] if route_trips else "AP09-B-1001"
                    next_dep = route_trips[0]["departure"] if route_trips else "Next Available"

                    st.markdown(f"""
                        <div class="ticket-pass-container">
                            <div class="ticket-pass-header">
                                <div>
                                    <div style="color: #38bdf8; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Smart City Transit • Electronic Ticket</div>
                                    <div style="color: #ffffff; font-size: 18px; font-weight: 800;">Route {chosen_route['route_name']}</div>
                                </div>
                                <div class="ticket-qr-mock">
                                    <div style="font-size: 32px;">📱</div>
                                    <div style="font-size: 8px; color: #0f172a; font-weight: 800;">SCAN PASS</div>
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                                <div>
                                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">From (Boarding)</div>
                                    <div style="color: #10b981; font-size: 16px; font-weight: 700;">🟢 {board_stop}</div>
                                </div>
                                <div>
                                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">To (Alighting)</div>
                                    <div style="color: #38bdf8; font-size: 16px; font-weight: 700;">🏁 {alight_stop}</div>
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px; margin-bottom: 16px;">
                                <div>
                                    <div style="color: #94a3b8; font-size: 10px; text-transform: uppercase;">Distance</div>
                                    <div style="color: #f8fafc; font-size: 14px; font-weight: 700;">{fare_res['distance']} km</div>
                                </div>
                                <div>
                                    <div style="color: #94a3b8; font-size: 10px; text-transform: uppercase;">Assigned Bus</div>
                                    <div style="color: #f8fafc; font-size: 14px; font-weight: 700;">{next_bus}</div>
                                </div>
                                <div>
                                    <div style="color: #94a3b8; font-size: 10px; text-transform: uppercase;">Dep Time</div>
                                    <div style="color: #f8fafc; font-size: 14px; font-weight: 700;">{next_dep}</div>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 2px dashed rgba(255,255,255,0.15); padding-top: 14px;">
                                <div>
                                    <div style="color: #94a3b8; font-size: 11px;">Total Fare ({passenger_count} Pax)</div>
                                    <div class="ticket-fare-highlight">₹{total_fare_payable:,.0f}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: #94a3b8; font-size: 10px;">Ticket No: <code>{ticket_id}</code></div>
                                    <div style="color: #94a3b8; font-size: 10px;">Issued: {now_str}</div>
                                    <span class="badge-optimal" style="margin-top: 4px; display: inline-block;">VALID PASS</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    if st.button("📥 Download / Save Digital Ticket", use_container_width=True):
                        st.success(f"Ticket #{ticket_id} booked successfully! Present this pass upon boarding.")

            # Route Stops & Distance Matrix Table
            st.write("")
            with st.container(border=True):
                st.markdown(f"### 📍 Route {chosen_route['route_name']} Stop Distance & Fare Schedule")
                st.caption(f"Pricing: Base Fare = ₹{chosen_route.get('base_fare', 10.0)} | Per-Km Rate = ₹{chosen_route.get('fare_per_km', 2.5)}/km")

                if r_stops_data:
                    sched_list = []
                    for s in r_stops_data:
                        d_origin = float(s["distance_from_origin"] or 0.0)
                        fare_from_start = max(float(chosen_route.get("min_fare", 10.0)), round(float(chosen_route.get("base_fare", 10.0)) + (d_origin * float(chosen_route.get("fare_per_km", 2.5)))))
                        sched_list.append({
                            "Stop Order": s["stop_order"],
                            "Stop Name": s["stop_name"],
                            "Cumulative Distance from Origin (km)": f"{d_origin} km",
                            "Ticket Fare from Start (₹)": f"₹{fare_from_start}" if s["stop_order"] > 1 else "Origin Terminal (₹0)"
                        })
                    st.dataframe(pd.DataFrame(sched_list), use_container_width=True, hide_index=True)


    # --------------------------------------------------------
    # 3. AI TRANSIT ASSISTANT
    # --------------------------------------------------------
    elif page == "🤖 AI Transit Assistant":

        current_api_key = st.session_state.get("gemini_api_key", "").strip() or get_stored_api_key()
        sel_model = st.session_state.get("selected_gemini_model", "gemini-3.8-flash")

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🤖 AI Transit & Fare Assistant</div>
                <div class="app-hero-desc">Ask any question about ticket prices, stop-to-stop distances, bus schedules, or optimal travel routes in natural language.</div>
            </div>
        """, unsafe_allow_html=True)

        col_status, col_clear = st.columns([9, 3])
        with col_status:
            if current_api_key:
                st.markdown(f'<span class="app-pill pill-passenger">🟢 Powered by Google Gemini ({sel_model}) — Grounded in Live Fares & Stops</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="app-pill pill-operator">🟡 AI Mode: Dynamic SQLite Retrieval & Fare Grounding</span>', unsafe_allow_html=True)

        with col_clear:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "👋 Hi there! I am your **Smart Transit AI Assistant**. Ask me about ticket fares based on distance, bus timings, intermediate stops, or journey directions!"}
                ]
                st.rerun()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "👋 Hi there! I am your **Smart Transit AI Assistant**. Ask me about ticket fares based on distance, bus timings, intermediate stops, or journey directions!"}
            ]

        # Suggested Prompts
        st.markdown("**Quick Prompts:**")
        q1, q2, q3, q4 = st.columns(4)
        prompt_to_add = None

        if q1.button("🎟️ Ticket cost Secunderabad to Koti?", use_container_width=True):
            prompt_to_add = "How much is the ticket fare from Secunderabad to Koti and what is the distance?"
        if q2.button("🚌 Next buses to Ameerpet?", use_container_width=True):
            prompt_to_add = "When are the next scheduled buses to Ameerpet?"
        if q3.button("💰 Fare rules on Route 102?", use_container_width=True):
            prompt_to_add = "What is the fare structure and per-km pricing for Route 102?"
        if q4.button("⚡ Fastest route across city?", use_container_width=True):
            prompt_to_add = "Which bus is fastest to reach LB Nagar from Ameerpet?"

        # Chat history rendering
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask a transit or fare question (e.g. 'How much does a ticket cost for 10 km?')...")
        active_prompt = prompt_to_add or user_input

        if active_prompt:
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 AI is reading live transit and fare records..."):
                    if current_api_key:
                        gemini_res = answer_with_gemini(
                            query=active_prompt,
                            api_key=current_api_key,
                            model_name=sel_model,
                            chat_history=st.session_state.chat_history,
                            user_role="passenger"
                        )
                        if gemini_res["success"]:
                            ai_reply = gemini_res["response"]
                        else:
                            fallback_reply = dynamic_database_search_response(active_prompt)
                            ai_reply = f"{fallback_reply}\n\n*(Note: Gemini API notice: {gemini_res.get('message')})*"
                    else:
                        ai_reply = dynamic_database_search_response(active_prompt)

                    st.markdown(ai_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})


    # --------------------------------------------------------
    # 4. REPORT OVERCROWDED BUS
    # --------------------------------------------------------
    elif page == "📸 Report Overcrowded Bus":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">📸 Passenger Crowd Reporting Station</div>
                <div class="app-hero-desc">Report overcrowded buses or standing-room conditions in real time so transit operators can deploy relief backup buses immediately.</div>
            </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("### 📝 Submit Real-Time Crowd Report")
            with st.form("overcrowd_form", clear_on_submit=True):
                c_oc1, c_oc2 = st.columns(2)
                with c_oc1:
                    route_dict = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r["id"] for r in routes}
                    sel_route_label = st.selectbox("Affected Route", list(route_dict.keys()) if route_dict else ["No routes available"])
                    sel_route_id = route_dict.get(sel_route_label)

                    bus_num_input = st.text_input("Bus Registration Number", placeholder="e.g. AP09-B-1002")

                with c_oc2:
                    all_stop_names = [s["stop_name"] for s in stops] if stops else ["Secunderabad", "Koti", "Ameerpet"]
                    stop_rep_name = st.selectbox("Current Stop Location", all_stop_names)
                    crowd_notes = st.text_area("Passenger Observations", placeholder="Severe overcrowding, passengers unable to board at stop, doors jammed...")

                uploaded_photo = st.file_uploader("Upload Bus Photo (Optional)", type=["jpg", "png", "jpeg"])

                submit_report = st.form_submit_button("🚨 Submit Crowd Report & Request Backup Bus", use_container_width=True)

            if submit_report:
                if not sel_route_id:
                    st.error("Please select an active route.")
                elif not bus_num_input.strip():
                    st.error("Please enter the bus number.")
                else:
                    today_str = date.today().isoformat()
                    time_str = datetime.now().strftime("%H:%M")
                    add_overcrowding_alert(
                        route_id=sel_route_id,
                        bus_number=bus_num_input.strip(),
                        stop_name=stop_rep_name,
                        report_date=today_str,
                        report_time=time_str,
                        passenger_notes=crowd_notes.strip()
                    )
                    st.success("🚨 Alert dispatched to Operator Control Center! Extra relief bus deployment is being reviewed.")
                    st.balloons()


    # --------------------------------------------------------
    # 5. ROUTE FINDER
    # --------------------------------------------------------
    elif page == "🗺️ Route Finder":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🗺️ Passenger Route Planner & Transfer Navigator</div>
                <div class="app-hero-desc">Calculate the shortest path, multi-line transfer connections, hop-by-hop distances, and total journey ticket fares between any two stops.</div>
            </div>
        """, unsafe_allow_html=True)

        network_rows = get_network_graph_data()

        if not network_rows:
            st.warning("No connected routes found. Click '🌱 Populate Sample City Data' in the sidebar.")
        else:
            graph, route_map = build_graph_from_db(network_rows)
            all_stop_names = sorted(list(graph.keys()))

            if "rf_origin" not in st.session_state or st.session_state["rf_origin"] not in all_stop_names:
                st.session_state["rf_origin"] = all_stop_names[0]
            if "rf_dest" not in st.session_state or st.session_state["rf_dest"] not in all_stop_names:
                st.session_state["rf_dest"] = all_stop_names[min(len(all_stop_names)-1, 1)] if len(all_stop_names) > 1 else all_stop_names[0]

            with st.container(border=True):
                st.markdown("#### 🧭 Find Best Transit Route & Transfers")
                c_src, c_swap, c_dst = st.columns([5, 2, 5])
                with c_src:
                    origin_stop = c_src.selectbox("Origin Stop", all_stop_names, index=all_stop_names.index(st.session_state["rf_origin"]))
                    st.session_state["rf_origin"] = origin_stop
                with c_swap:
                    st.write("")
                    st.write("")
                    if st.button("⇄ Swap", use_container_width=True, key="swap_btn_rf"):
                        st.session_state["rf_origin"], st.session_state["rf_dest"] = st.session_state["rf_dest"], st.session_state["rf_origin"]
                        st.rerun()
                with c_dst:
                    dest_stop = c_dst.selectbox("Destination Stop", all_stop_names, index=all_stop_names.index(st.session_state["rf_dest"]))
                    st.session_state["rf_dest"] = dest_stop

            result = find_detailed_path(graph, route_map, origin_stop, dest_stop)

            if result["found"]:
                # Calculate total fare and distances across all segments
                total_journey_fare = 0
                total_journey_dist = 0.0

                segment_fare_details = []
                for seg in result["segments"]:
                    # Find matching route in DB
                    seg_r = next((r for r in routes if str(r["route_name"]).strip() == str(seg["route"]).strip()), None)
                    if seg_r:
                        f_info = calculate_ticket_fare(seg_r["id"], seg["from_stop"], seg["to_stop"])
                    else:
                        f_info = {"fare": 15.0, "distance": 5.0, "base_fare": 10.0, "fare_per_km": 2.5}

                    total_journey_fare += f_info["fare"]
                    total_journey_dist += f_info["distance"]
                    segment_fare_details.append(f_info)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Stops", len(result["path"]))
                m2.metric("Network Transfers", f"{result['transfers']} transfer{'s' if result['transfers'] != 1 else ''}")
                m3.metric("Total Distance", f"{total_journey_dist:.1f} km")
                m4.metric("Total Journey Fare", f"₹{total_journey_fare:,.0f}", f"Across {len(result['segments'])} segment(s)")

                st.markdown("### 🧭 Step-by-Step Itinerary & Leg Fares")
                for idx, seg in enumerate(result["segments"], start=1):
                    f_det = segment_fare_details[idx - 1]
                    with st.container(border=True):
                        c_it1, c_it2 = st.columns([8, 4])
                        with c_it1:
                            st.markdown(f"**Leg {idx}:** Board **Route {seg['route']}** from **{seg['from_stop']}** ➔ **{seg['to_stop']}**")
                            st.caption(f"Segment Distance: **{f_det['distance']} km**")
                        with c_it2:
                            st.markdown(f"""
                                <div style="text-align: right;">
                                    <span class="app-pill pill-fare">Ticket: ₹{f_det['fare']}</span>
                                </div>
                            """, unsafe_allow_html=True)
            else:
                st.error(f"No direct or connected transit route found between '{origin_stop}' and '{dest_stop}'.")


# ============================================================
# OPERATOR BACKEND SECTION
# ============================================================

else:

    # --------------------------------------------------------
    # 1. DASHBOARD
    # --------------------------------------------------------
    if page == "📊 Dashboard":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">📊 Executive Fleet Dashboard</div>
                <div class="app-hero-desc">Real-time city transport metrics, passenger volumes, active buses, and distance-weighted operational revenue.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes and not stops:
            st.warning("⚠️ No transit data found. Click '🌱 Populate Sample City Data' in the sidebar to populate records.")

        # KPI METRICS
        analytics = get_route_ridership_analytics()
        total_passengers = sum(row[3] for row in ridership) if ridership else 0
        unique_buses = len(set(row[2] for row in trips if row[2])) if trips else 0
        pending_alerts_cnt = len([a for a in alerts if a["status"] == "Pending"])

        # Compute accurate revenue based on each route's distance and fare rates
        total_dynamic_revenue = 0
        if analytics:
            for a in analytics:
                tot_p = a.get("total_passengers", 0)
                b_fare = float(a.get("base_fare") or 10.0)
                f_rate = float(a.get("fare_per_km") or 2.5)
                dist_val = float(a.get("distance") or 10.0)
                avg_route_fare = max(10.0, round(b_fare + (dist_val * 0.7 * f_rate)))
                total_dynamic_revenue += (tot_p * avg_route_fare)
        else:
            total_dynamic_revenue = total_passengers * 25

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">🚌</div>
                    <div class="stat-label">Active Routes</div>
                    <div class="stat-val">{len(routes)}</div>
                    <div class="stat-sub">City Corridors</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">📍</div>
                    <div class="stat-label">Bus Stops</div>
                    <div class="stat-val">{len(stops)}</div>
                    <div class="stat-sub">Network Stations</div>
                </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-label">Daily Trips</div>
                    <div class="stat-val">{len(trips)}</div>
                    <div class="stat-sub">Scheduled Runs</div>
                </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">🚍</div>
                    <div class="stat-label">Active Fleet</div>
                    <div class="stat-val">{unique_buses}</div>
                    <div class="stat-sub">Buses Deployed</div>
                </div>
            """, unsafe_allow_html=True)

        with c5:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-label">Total Riders</div>
                    <div class="stat-val">{total_passengers:,}</div>
                    <div class="stat-sub">{pending_alerts_cnt} Alert(s) Pending</div>
                </div>
            """, unsafe_allow_html=True)

        with c6:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">💰</div>
                    <div class="stat-label">Total Revenue</div>
                    <div class="stat-val">₹{total_dynamic_revenue:,.0f}</div>
                    <div class="stat-sub">Distance-Weighted Fares</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("")

        # HIGHEST PASSENGER & REVENUE ROUTE HIGHLIGHTS
        if analytics and any(a["total_passengers"] > 0 for a in analytics):
            sorted_by_pass = sorted(analytics, key=lambda x: x["total_passengers"], reverse=True)
            top_pass_route = sorted_by_pass[0]
            
            # Compute route revenues
            for a in analytics:
                b_fare = float(a.get("base_fare") or 10.0)
                f_rate = float(a.get("fare_per_km") or 2.5)
                dist_val = float(a.get("distance") or 10.0)
                a["computed_avg_fare"] = max(10.0, round(b_fare + (dist_val * 0.7 * f_rate)))
                a["computed_revenue"] = a["total_passengers"] * a["computed_avg_fare"]

            top_rev_route = max(analytics, key=lambda x: x["computed_revenue"])

            h_c1, h_c2 = st.columns(2)
            with h_c1:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 18px 24px;">
                        <span class="app-pill pill-passenger">👑 HIGHEST RIDERSHIP CORRIDOR</span>
                        <h3 style="color: #ffffff; margin: 8px 0 4px 0;">Route {top_pass_route['route_name']} ({top_pass_route['source']} ➔ {top_pass_route['destination']})</h3>
                        <p style="color: #94a3b8; font-size: 13px; margin: 0;">Total Passengers: <strong style="color: #38bdf8;">{top_pass_route['total_passengers']:,}</strong> | Daily Avg: <strong style="color: #38bdf8;">{top_pass_route['avg_daily_passengers']}</strong> riders/day</p>
                    </div>
                """, unsafe_allow_html=True)
            with h_c2:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 18px 24px;">
                        <span class="app-pill pill-passenger" style="background: rgba(16,185,129,0.2); color: #6ee7b7; border-color: rgba(16,185,129,0.4);">💎 TOP EARNING ROUTE</span>
                        <h3 style="color: #ffffff; margin: 8px 0 4px 0;">Route {top_rev_route['route_name']} ({top_rev_route['source']} ➔ {top_rev_route['destination']})</h3>
                        <p style="color: #94a3b8; font-size: 13px; margin: 0;">Estimated Revenue: <strong style="color: #34d399;">₹{top_rev_route['computed_revenue']:,.0f}</strong> | Distance: <strong style="color: #34d399;">{top_rev_route['distance']} km</strong></p>
                    </div>
                """, unsafe_allow_html=True)

        st.write("")
        st.markdown("### 📈 City Route Performance & Distance-Based Revenue")
        if analytics:
            df_analytics = pd.DataFrame(analytics)
            df_analytics["Route Display"] = "Route " + df_analytics["route_name"].astype(str) + " (" + df_analytics["source"] + " ➔ " + df_analytics["destination"] + ")"
            
            fig_p = px.bar(
                df_analytics,
                x="Route Display",
                y="total_passengers",
                color="computed_revenue",
                title="Passenger Volume & Revenue by Route (Colored by Distance-Based Revenue)",
                labels={"total_passengers": "Total Passengers", "computed_revenue": "Revenue (₹)"},
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            fig_p.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=40))
            st.plotly_chart(fig_p, use_container_width=True)


    # --------------------------------------------------------
    # 2. FARE & DISTANCE PRICING MANAGER (NEW OPERATOR TOOL)
    # --------------------------------------------------------
    elif page == "💰 Fare & Distance Pricing Manager":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">💰 Fare & Distance Pricing Manager</div>
                <div class="app-hero-desc">Set up and manage separate ticket costs according to distance for each route, configure individual stop cumulative distances, and define custom stop-to-stop fare overrides.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes:
            st.info("No routes available yet. Click '🌱 Populate Sample City Data' in the sidebar to load routes!")
        else:
            tab_fare_routes, tab_stop_dist, tab_matrix = st.tabs([
                "🎛️ Route Pricing & Base Rates",
                "📏 Stop Distances & Fares Along Route",
                "🗺️ Stop-to-Stop Fare Matrix & Custom Overrides"
            ])

            # TAB 1: Route Pricing & Base Rates
            with tab_fare_routes:
                st.markdown("### 🎛️ Configure Base & Per-Kilometer Fares for Each Route")
                st.caption("Each route can have its own Base Boarding Fare (₹), Per-Km Rate (₹/km), and Minimum Fare cap:")

                # Overview table
                routes_fare_overview = []
                for r in routes:
                    b_f = float(r.get("base_fare") if r.get("base_fare") is not None else 10.0)
                    f_km = float(r.get("fare_per_km") if r.get("fare_per_km") is not None else 2.5)
                    min_f = float(r.get("min_fare") if r.get("min_fare") is not None else 10.0)
                    dist = float(r.get("distance") or 0.0)
                    end_to_end_fare = max(min_f, round(b_f + (dist * f_km)))
                    
                    routes_fare_overview.append({
                        "Route ID": r["id"],
                        "Route Code": r["route_name"],
                        "Origin": r["source"],
                        "Destination": r["destination"],
                        "Total Distance": f"{dist} km",
                        "Base Boarding Fare": f"₹{b_f:.1f}",
                        "Rate / km": f"₹{f_km:.2f}/km",
                        "Minimum Fare": f"₹{min_f:.1f}",
                        "End-to-End Ticket Cost": f"₹{end_to_end_fare}"
                    })

                st.dataframe(pd.DataFrame(routes_fare_overview), use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("✏️ Edit Route Fare Pricing Parameters")

                route_sel_dict = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r for r in routes}
                sel_edit_label = st.selectbox("Select Route to Configure", list(route_sel_dict.keys()), key="fare_sel_route")
                sel_r_obj = route_sel_dict[sel_edit_label]

                with st.form("edit_route_fare_form"):
                    f_c1, f_c2, f_c3 = st.columns(3)
                    with f_c1:
                        new_base_fare = st.number_input(
                            "Base Boarding Fare (₹)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(sel_r_obj.get("base_fare") if sel_r_obj.get("base_fare") is not None else 10.0),
                            step=1.0,
                            help="Initial boarding charge before distance calculation."
                        )
                    with f_c2:
                        new_per_km = st.number_input(
                            "Per-Kilometer Rate (₹ / km)",
                            min_value=0.1,
                            max_value=20.0,
                            value=float(sel_r_obj.get("fare_per_km") if sel_r_obj.get("fare_per_km") is not None else 2.5),
                            step=0.1,
                            help="Fare added per kilometer travelled."
                        )
                    with f_c3:
                        new_min_fare = st.number_input(
                            "Minimum Fare (₹)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(sel_r_obj.get("min_fare") if sel_r_obj.get("min_fare") is not None else 10.0),
                            step=1.0,
                            help="Floor price for any ticket on this route."
                        )

                    st.markdown("**Quick Preset Pricing Packages:**")
                    q_p1, q_p2, q_p3 = st.columns(3)
                    with q_p1:
                        st.caption("⚡ **Express Bus Rate**: Base ₹15 + ₹3.0/km")
                    with q_p2:
                        st.caption("🚌 **Standard City Rate**: Base ₹10 + ₹2.2/km")
                    with q_p3:
                        st.caption("🪙 **Economy Local Rate**: Base ₹8 + ₹1.8/km")

                    save_fare_btn = st.form_submit_button("💾 Save Route Fare Rates", use_container_width=True)

                if save_fare_btn:
                    update_route_fare_pricing(sel_r_obj["id"], new_base_fare, new_per_km, new_min_fare)
                    st.success(f"Fare rates for Route {sel_r_obj['route_name']} updated successfully!")
                    st.rerun()

            # TAB 2: Stop Distances Along Route
            with tab_stop_dist:
                st.markdown("### 📏 Stop-by-Stop Distance & Sequence Editor")
                st.caption("Specify the exact cumulative distance from the origin for each stop along the route. Ticket costs will be computed according to these precise distances.")

                r_dist_dict = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r for r in routes}
                sel_dist_label = st.selectbox("Select Route Corridor", list(r_dist_dict.keys()), key="dist_sel_route")
                sel_dist_r = r_dist_dict[sel_dist_label]

                curr_stops_seq = get_route_stops(sel_dist_r["id"])

                c_act1, c_act2 = st.columns([8, 4])
                with c_act2:
                    if st.button("⚡ Auto-Distribute Distances Evenly", use_container_width=True, help="Evenly distribute distances based on total route km"):
                        auto_distribute_route_stop_distances(sel_dist_r["id"])
                        st.success("Stop distances auto-interpolated across total route distance!")
                        st.rerun()

                if not curr_stops_seq:
                    st.warning(f"No intermediate stops registered for Route {sel_dist_r['route_name']}. Please add stops in the **📍 Stops** tab first.")
                else:
                    with st.form("save_stop_distances_form"):
                        st.markdown(f"**Stops along Route {sel_dist_r['route_name']} (Total Route Distance: {sel_dist_r['distance']} km)**")
                        
                        stop_edit_inputs = []
                        prev_dist = 0.0
                        
                        for idx, s_item in enumerate(curr_stops_seq):
                            col_s_name, col_s_dist, col_s_fare = st.columns([5, 4, 3])
                            with col_s_name:
                                is_terminal = idx == 0 or idx == len(curr_stops_seq) - 1
                                tag = " (Start Origin)" if idx == 0 else (" (Final Terminal)" if idx == len(curr_stops_seq) - 1 else "")
                                st.write(f"**#{s_item['stop_order']} {s_item['stop_name']}**{tag}")
                            
                            with col_s_dist:
                                val_d = float(s_item["distance_from_origin"] or 0.0)
                                if idx == 0:
                                    val_d = 0.0
                                elif idx == len(curr_stops_seq) - 1 and val_d == 0.0:
                                    val_d = float(sel_dist_r["distance"] or 10.0)
                                
                                new_dist_input = st.number_input(
                                    f"Cumulative km from Origin",
                                    min_value=0.0,
                                    max_value=200.0,
                                    value=val_d,
                                    step=0.5,
                                    key=f"stop_dist_in_{s_item['id']}"
                                )
                                stop_edit_inputs.append({"stop_id": s_item["id"], "distance_from_origin": new_dist_input})

                            with col_s_fare:
                                b_fare = float(sel_dist_r.get("base_fare") or 10.0)
                                f_per_km = float(sel_dist_r.get("fare_per_km") or 2.5)
                                min_f = float(sel_dist_r.get("min_fare") or 10.0)
                                calc_fare_from_origin = max(min_f, round(b_fare + (val_d * f_per_km)))
                                if idx == 0:
                                    st.write("₹0 (Origin)")
                                else:
                                    st.write(f"Fare: **₹{calc_fare_from_origin}**")

                        save_stop_dist_btn = st.form_submit_button("💾 Save Stop Distances & Update Route Fares", use_container_width=True)

                    if save_stop_dist_btn:
                        update_route_stop_distances(sel_dist_r["id"], stop_edit_inputs)
                        st.success("Stop distances and ticket fare matrices updated successfully!")
                        st.rerun()

            # TAB 3: Stop-to-Stop Fare Matrix & Custom Overrides
            with tab_matrix:
                st.markdown("### 🗺️ Full Stop-to-Stop Distance & Fare Matrix")
                st.caption("View and inspect the ticket cost and distance between every possible boarding and alighting stop on this route:")

                r_mat_dict = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r for r in routes}
                sel_mat_label = st.selectbox("Select Route for Fare Matrix", list(r_mat_dict.keys()), key="mat_sel_route")
                sel_mat_r = r_mat_dict[sel_mat_label]

                mat_data = get_route_fare_matrix(sel_mat_r["id"])

                if not mat_data["stops"]:
                    st.info("No stops found on this route.")
                else:
                    # Build DataFrame
                    matrix_grid = []
                    for row_idx, from_stop in enumerate(mat_data["stops"]):
                        row_dict = {"Boarding Stop (From)": from_stop}
                        for col_idx, to_stop in enumerate(mat_data["stops"]):
                            cell = mat_data["matrix"][row_idx][col_idx]
                            if cell["same"]:
                                row_dict[to_stop] = "—"
                            else:
                                custom_star = " ⭐" if cell.get("is_custom") else ""
                                row_dict[to_stop] = f"₹{cell['fare']:.0f} ({cell['distance']}km){custom_star}"
                        matrix_grid.append(row_dict)

                    df_matrix = pd.DataFrame(matrix_grid)
                    st.dataframe(df_matrix, use_container_width=True, hide_index=True)
                    st.caption("*(Format: `₹TicketFare (Distance)`. ⭐ indicates manual custom price override)*")

                st.divider()
                st.subheader("🎯 Set Specific Custom Fare Override")
                st.caption("If you wish to set a fixed flat fare or promotional pricing for a specific stop pair that differs from the default distance formula, define it here:")

                if mat_data["stops"] and len(mat_data["stops"]) >= 2:
                    with st.form("custom_override_form"):
                        c_ov1, c_ov2, c_ov3, c_ov4 = st.columns(4)
                        stop_id_map = {s["stop_name"]: s["id"] for s in mat_data["stop_objects"]}
                        with c_ov1:
                            ov_from = st.selectbox("From Stop", mat_data["stops"], index=0)
                        with c_ov2:
                            ov_to = st.selectbox("To Stop", mat_data["stops"], index=len(mat_data["stops"])-1)
                        with c_ov3:
                            ov_fare = st.number_input("Custom Ticket Fare (₹)", min_value=1.0, max_value=500.0, value=25.0, step=1.0)
                        with c_ov4:
                            ov_notes = st.text_input("Pricing Note", placeholder="e.g. Express Flat Fare")

                        submit_override = st.form_submit_button("⚡ Save Custom Fare Override", use_container_width=True)

                    if submit_override:
                        if ov_from == ov_to:
                            st.error("Boarding and alighting stops must be different.")
                        else:
                            from_id = stop_id_map[ov_from]
                            to_id = stop_id_map[ov_to]
                            set_custom_stop_fare(sel_mat_r["id"], from_id, to_id, ov_fare, notes=ov_notes)
                            st.success(f"Custom fare of ₹{ov_fare} set for {ov_from} ➔ {ov_to} on Route {sel_mat_r['route_name']}!")
                            st.rerun()

                    # Display existing custom overrides
                    custom_fares_list = get_custom_stop_fares(sel_mat_r["id"])
                    if custom_fares_list:
                        st.write("")
                        st.markdown("#### 📋 Active Custom Fare Overrides for this Route:")
                        for cf in custom_fares_list:
                            c_f_l, c_f_r = st.columns([9, 3])
                            with c_f_l:
                                st.markdown(f"• **{cf['from_stop_name']} ➔ {cf['to_stop_name']}:** <span style='color:#38bdf8; font-weight:700;'>₹{cf['custom_fare']}</span> &nbsp; *(Note: {cf.get('notes') or 'Manual Override'})*", unsafe_allow_html=True)
                            with c_f_r:
                                if st.button(f"🗑️ Delete Override", key=f"del_cf_{cf['id']}", use_container_width=True):
                                    delete_custom_stop_fare(cf["id"])
                                    st.success("Override removed.")
                                    st.rerun()


    # --------------------------------------------------------
    # 3. OVERCROWDED BUS ALERTS
    # --------------------------------------------------------
    elif page == "🚨 Overcrowded Bus Alerts":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🚨 Overcrowded Bus Alerts & Extra Bus Dispatch</div>
                <div class="app-hero-desc">Monitor live crowd reports from passengers and deploy backup buses with a single click to restore network balance.</div>
            </div>
        """, unsafe_allow_html=True)

        pending_alerts = [a for a in alerts if a["status"] == "Pending"]
        resolved_alerts = [a for a in alerts if a["status"] != "Pending"]

        st.markdown(f"### 📋 Pending Reports Queue ({len(pending_alerts)})")
        if not pending_alerts:
            st.success("🟢 No pending overcrowding reports! Fleet operations are running smoothly.")
        else:
            for al in pending_alerts:
                with st.container(border=True):
                    c_a1, c_a2 = st.columns([9, 3])
                    with c_a1:
                        st.markdown(f"#### 🚌 Bus **{al['bus_number']}** on **Route {al['route_name']}** (`{al['source']} ➔ {al['destination']}`)")
                        st.markdown(f"📍 **Reported Stop:** `{al['stop_name']}` &nbsp;|&nbsp; ⏰ **Time:** `{al['report_date']} {al['report_time']}`")
                        if al.get("passenger_notes"):
                            st.caption(f"Passenger Notes: *\"{al['passenger_notes']}\"*")
                    with c_a2:
                        if st.button("🚀 Dispatch Extra Bus", key=f"dispatch_{al['id']}", use_container_width=True):
                            resolve_overcrowding_alert(al["id"])
                            st.success(f"Extra bus dispatched for Route {al['route_name']}!")
                            st.rerun()

        if resolved_alerts:
            st.write("")
            with st.expander(f"📜 Dispatched & Resolved Reports History ({len(resolved_alerts)})"):
                for r_al in resolved_alerts:
                    st.markdown(f"• **Bus {r_al['bus_number']}** on **Route {r_al['route_name']}** at `{r_al['stop_name']}` — <span class='badge-optimal'>Extra Bus Dispatched</span>", unsafe_allow_html=True)


    # --------------------------------------------------------
    # 4. ROUTES
    # --------------------------------------------------------
    elif page == "🚌 Routes":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🚌 Bus Route Management</div>
                <div class="app-hero-desc">Create, configure, edit, and inspect transit routes, custom stop sequences, and distance-based ticket fare rules.</div>
            </div>
        """, unsafe_allow_html=True)

        tab_view, tab_add = st.tabs(["📋 View & Manage Routes", "➕ Add Route"])

        with tab_view:
            if routes:
                df_routes = pd.DataFrame([{
                    "ID": route["id"],
                    "Route Code": route["route_name"],
                    "Start Point": route["source"],
                    "Final Destination": route["destination"],
                    "Distance (km)": route["distance"],
                    "Base Fare (₹)": route["base_fare"],
                    "Fare/km (₹)": route["fare_per_km"],
                    "Min Fare (₹)": route["min_fare"],
                } for route in routes])
                st.dataframe(df_routes, use_container_width=True, hide_index=True)

                st.subheader("🔍 Route Stop Sequences")
                for r in routes:
                    stops_seq = get_route_stops(r["id"])
                    route_schedule = _get_route_schedule_rows(r["id"])
                    with st.expander(f"Route {r['route_name']} ({r['source']} ➔ {r['destination']}) — {len(stops_seq)} stops (Fare: ₹{r.get('base_fare', 10)}+₹{r.get('fare_per_km', 2.5)}/km)"):
                        if stops_seq:
                            seq_str = " ➔ ".join([f"**{s['stop_name']}** ({s.get('distance_from_origin', 0.0)}km)" for s in stops_seq])
                            st.markdown(f"**Stop Sequence & Cumulative Distances:** {seq_str}")
                        else:
                            st.caption("No custom stops specified for this route yet.")

                        st.markdown("**Scheduled Trips**")
                        if route_schedule:
                            st.dataframe(pd.DataFrame(route_schedule), use_container_width=True, hide_index=True)
                            st.caption("Times show departure from the route origin and arrival at its destination.")
                        else:
                            st.caption("No trips are scheduled for this route.")

                st.divider()
                st.subheader("✏️ Edit or Delete Route")
                route_options = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r for r in routes}
                selected_label = st.selectbox("Select Route to Modify", list(route_options))
                selected_r = route_options[selected_label]

                col_edit_f, col_del_f = st.columns([2, 1])

                with col_edit_f:
                    with st.form("edit_route_form_v2"):
                        st.subheader("✏️ Edit Route Details")
                        ec1, ec2, ec3, ec4 = st.columns(4)
                        e_code = ec1.text_input("Route Code", value=selected_r["route_name"])
                        e_src = ec2.text_input("Start Point", value=selected_r["source"])
                        e_dst = ec3.text_input("Final Destination", value=selected_r["destination"])
                        e_dist = ec4.number_input("Distance (km)", min_value=0.0, value=float(selected_r["distance"] or 0))

                        ec_f1, ec_f2, ec_f3 = st.columns(3)
                        e_base_fare = ec_f1.number_input("Base Fare (₹)", min_value=0.0, value=float(selected_r.get("base_fare") or 10.0))
                        e_fare_km = ec_f2.number_input("Fare per km (₹/km)", min_value=0.1, value=float(selected_r.get("fare_per_km") or 2.5), step=0.1)
                        e_min_fare = ec_f3.number_input("Min Fare (₹)", min_value=0.0, value=float(selected_r.get("min_fare") or 10.0))

                        save_btn = st.form_submit_button("💾 Save Route Changes", use_container_width=True)

                    if save_btn:
                        e_code = e_code.strip()
                        e_src = e_src.strip()
                        e_dst = e_dst.strip()

                        if not e_code or not e_src or not e_dst:
                            st.error("Route code, start point, and final destination are required.")
                        elif route_code_exists(e_code, exclude_id=selected_r["id"]):
                            st.error(f"Route code '{e_code}' is already used by another route.")
                        else:
                            update_route(selected_r["id"], e_code, e_src, e_dst, e_dist, base_fare=e_base_fare, fare_per_km=e_fare_km, min_fare=e_min_fare)
                            st.success("Route updated successfully.")
                            st.rerun()

                with col_del_f:
                    with st.container(border=True):
                        st.subheader("🗑️ Delete Route")
                        st.warning(f"Delete Route {selected_r['route_name']}?")
                        if st.button("🗑️ Confirm Delete", key="del_route_btn", use_container_width=True):
                            if route_has_trips(selected_r["id"]):
                                st.error("Cannot delete route because trips are assigned to it.")
                            else:
                                delete_route(selected_r["id"])
                                st.success("Route deleted.")
                                st.rerun()
            else:
                st.info("No routes available. Use the 'Add Route' tab to create your first route.")

        with tab_add:
            with st.container(border=True):
                st.subheader("➕ Create New Route")
                with st.form("add_route_form_v2"):
                    c1, c2, c3, c4 = st.columns(4)
                    new_code = c1.text_input("Route Code", placeholder="e.g. 101")
                    new_src = c2.text_input("Start Point", placeholder="e.g. Secunderabad")
                    new_dst = c3.text_input("Final Destination", placeholder="e.g. Koti")
                    new_dist = c4.number_input("Distance (km)", min_value=0.0, step=0.5, value=10.0)

                    cf1, cf2, cf3 = st.columns(3)
                    new_b_fare = cf1.number_input("Base Fare (₹)", min_value=0.0, value=10.0, step=1.0)
                    new_f_rate = cf2.number_input("Fare per km (₹/km)", min_value=0.1, value=2.5, step=0.1)
                    new_m_fare = cf3.number_input("Min Fare (₹)", min_value=0.0, value=10.0, step=1.0)

                    st.caption("Intermediate Stops (Comma-separated, optional)")
                    stops_input = st.text_input("Stops", placeholder="Secunderabad, Batas, RTC X Roads, Koti")

                    submitted = st.form_submit_button("🚀 Add Route", use_container_width=True)

                if submitted:
                    new_code = new_code.strip()
                    new_src = new_src.strip()
                    new_dst = new_dst.strip()

                    if not new_code or not new_src or not new_dst:
                        st.error("Route code, start point, and final destination are required.")
                    elif route_code_exists(new_code):
                        st.error(f"Route code '{new_code}' is already assigned.")
                    elif new_src.casefold() == new_dst.casefold():
                        st.error("Start point and final destination must be different.")
                    else:
                        stop_list = [s.strip() for s in stops_input.split(",") if s.strip()]
                        if not stop_list:
                            stop_list = [new_src, new_dst]
                        if stop_list[0].casefold() != new_src.casefold():
                            stop_list.insert(0, new_src)
                        if stop_list[-1].casefold() != new_dst.casefold():
                            stop_list.append(new_dst)

                        add_route(new_code, new_src, new_dst, new_dist, stop_list, base_fare=new_b_fare, fare_per_km=new_f_rate, min_fare=new_m_fare)
                        st.success(f"Route '{new_code}' added successfully with {len(stop_list)} stops!")
                        st.rerun()


    # --------------------------------------------------------
    # 5. STOPS
    # --------------------------------------------------------
    elif page == "📍 Stops":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">📍 Intermediate Stops & Route Corridor Builder</div>
                <div class="app-hero-desc">Select your Start Point and Final Destination from saved routes, then add and manage the intermediate stops between them.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes:
            st.info("⚠️ No routes found in the database. Please create routes first in the **🚌 Routes** tab or click **'🌱 Populate Sample City Data'** in the sidebar.")
        else:
            all_sources = sorted(list(set(r["source"] for r in routes)))
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1:
                sel_source = st.selectbox("🟢 Select Start Point (Origin)", all_sources, key="stops_sel_src")

            matching_routes = [r for r in routes if r["source"].lower() == sel_source.lower()]
            if matching_routes:
                dest_options = sorted(list(set(r["destination"] for r in matching_routes)))
            else:
                dest_options = sorted(list(set(r["destination"] for r in routes if r["destination"].lower() != sel_source.lower())))

            with c_sel2:
                sel_destination = st.selectbox("🏁 Select Final Destination", dest_options, key="stops_sel_dst")

            target_route = next((r for r in routes if r["source"].lower() == sel_source.lower() and r["destination"].lower() == sel_destination.lower()), None)

            if target_route is None:
                target_route = next((r for r in routes if (r["source"].lower() == sel_source.lower() or r["destination"].lower() == sel_destination.lower())), routes[0])

            st.write("")
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #131c30 0%, #0e1626 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 18px 24px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <span class="app-pill pill-passenger" style="font-size: 13px;">🚌 Route {target_route['route_name']}</span>
                            <h3 style="color: #ffffff; margin: 8px 0 2px 0;">{sel_source} ➔ {sel_destination}</h3>
                            <p style="color: #94a3b8; font-size: 13px; margin: 0;">Total Distance: <strong>{target_route['distance']} km</strong> &nbsp;|&nbsp; Base Fare: <strong>₹{target_route.get('base_fare', 10)}</strong> + <strong>₹{target_route.get('fare_per_km', 2.5)}/km</strong></p>
                        </div>
                        <div style="text-align: right;">
                            <span class="app-pill pill-operator">Corridor Configurator</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            curr_route_stops = get_route_stops(target_route["id"])
            route_schedule = _get_route_schedule_rows(target_route["id"])
            st.subheader(f"🕒 Scheduled Trips for Route {target_route['route_name']}")
            if route_schedule:
                st.dataframe(pd.DataFrame(route_schedule), use_container_width=True, hide_index=True)
                st.caption("Times show departure from the route origin and arrival at its destination; intermediate-stop times are not stored.")
            else:
                st.info("No trips are scheduled for this route.")

            existing_intermediate = []
            for s in curr_route_stops:
                s_name = s["stop_name"]
                if s_name.lower() != sel_source.lower() and s_name.lower() != sel_destination.lower():
                    existing_intermediate.append(s_name)

            col_curr, col_manage = st.columns([5, 7])

            with col_curr:
                with st.container(border=True):
                    st.markdown("#### 🛣️ Current Route Stop Order")
                    if curr_route_stops:
                        for s_item in curr_route_stops:
                            s_name = s_item["stop_name"]
                            s_ord = s_item["stop_order"]
                            s_dist = s_item.get("distance_from_origin", 0.0)
                            is_start = s_name.lower() == sel_source.lower()
                            is_end = s_name.lower() == sel_destination.lower()

                            if is_start:
                                icon = "🟢"
                                badge = "Start Point (0 km)"
                                bg_color = "rgba(16, 185, 129, 0.15)"
                                border_color = "rgba(16, 185, 129, 0.4)"
                            elif is_end:
                                icon = "🏁"
                                badge = f"Final Destination ({s_dist} km)"
                                bg_color = "rgba(56, 189, 248, 0.15)"
                                border_color = "rgba(56, 189, 248, 0.4)"
                            else:
                                icon = f"📍 Stop #{s_ord}"
                                badge = f"Intermediate ({s_dist} km)"
                                bg_color = "rgba(255, 255, 255, 0.04)"
                                border_color = "rgba(255, 255, 255, 0.08)"

                            st.markdown(f"""
                                <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-weight: 700; color: #f8fafc;">{icon} {s_name}</span>
                                    </div>
                                    <span style="font-size: 11px; color: #94a3b8; font-weight: 600;">{badge}</span>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No intermediate stops configured yet.")

            with col_manage:
                with st.container(border=True):
                    st.markdown("#### ➕ Add / Update Intermediate Stops")
                    st.caption(f"Enter the intermediate stops between **{sel_source}** and **{sel_destination}** in order (comma-separated):")

                    default_val = ", ".join(existing_intermediate)
                    inter_input = st.text_area(
                        "Intermediate Stops",
                        value=default_val,
                        placeholder="e.g. Batas, RTC X Roads, Kachiguda",
                        help="Enter stops in the sequence the bus will visit them.",
                        height=100
                    )

                    if st.button("💾 Save Stops & Distances for Route", use_container_width=True):
                        raw_items = [s.strip() for s in inter_input.split(",") if s.strip()]
                        final_stop_seq = [sel_source] + raw_items + [sel_destination]
                        
                        replace_route_stops(target_route["id"], final_stop_seq)
                        st.success(f"Route {target_route['route_name']} updated with {len(final_stop_seq)} stops!")
                        st.rerun()


    # --------------------------------------------------------
    # 6. TRIPS
    # --------------------------------------------------------
    elif page == "⏱️ Trips":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">⏱️ Fleet Timetables & Trip Scheduling</div>
                <div class="app-hero-desc">Schedule daily runs, assign bus fleets, configure timetable departures, and prevent bus collisions.</div>
            </div>
        """, unsafe_allow_html=True)

        trips_with_r = get_trips_with_routes()

        tab_view_t, tab_add_t = st.tabs(["📋 View Scheduled Trips", "➕ Schedule New Trip"])

        with tab_view_t:
            if trips_with_r:
                df_trips = pd.DataFrame([{
                    "ID": trip["id"],
                    "Route Code": trip["route_name"],
                    "Bus Number": trip["bus_number"],
                    "Start Point": trip["source"],
                    "Final Destination": trip["destination"],
                    "Trip Date": trip["trip_date"],
                    "Departure": trip["departure"],
                    "Arrival": trip["arrival"],
                } for trip in trips_with_r])
                st.dataframe(df_trips, use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("✏️ Edit Scheduled Trip")
                trip_edit_options = {
                    f"Trip #{trip['id']} (Bus {trip['bus_number']} on Route {trip['route_name']} • {trip['departure']}-{trip['arrival']})": trip
                    for trip in trips_with_r
                }
                selected_trip_label = st.selectbox(
                    "Select Trip to Edit",
                    list(trip_edit_options),
                    key="edit_scheduled_trip_select",
                )
                selected_trip_to_edit = trip_edit_options[selected_trip_label]

                route_edit_options = {
                    f"Route {route['route_name']} ({route['source']} ➔ {route['destination']}) — ID {route['id']}": route
                    for route in routes
                }
                route_edit_labels = list(route_edit_options)
                current_route_index = next(
                    (
                        index
                        for index, label in enumerate(route_edit_labels)
                        if route_edit_options[label]["id"] == selected_trip_to_edit["route_id"]
                    ),
                    0,
                )

                with st.form(f"edit_trip_form_{selected_trip_to_edit['id']}"):
                    e_trip_route_label = st.selectbox(
                        "Route Code",
                        route_edit_labels or ["No routes available"],
                        index=current_route_index,
                        key=f"edit_trip_route_{selected_trip_to_edit['id']}",
                    )
                    e_trip_route_id = route_edit_options[e_trip_route_label]["id"] if route_edit_labels else None

                    e_trip_c1, e_trip_c2, e_trip_c3 = st.columns(3)
                    e_trip_bus = e_trip_c1.text_input(
                        "Bus Number",
                        value=selected_trip_to_edit["bus_number"] or "",
                        key=f"edit_trip_bus_{selected_trip_to_edit['id']}",
                    )
                    e_trip_date = e_trip_c2.date_input(
                        "Trip Date",
                        value=date.fromisoformat(str(selected_trip_to_edit["trip_date"] or date.today().isoformat())),
                        key=f"edit_trip_date_{selected_trip_to_edit['id']}",
                    )
                    e_trip_departure = e_trip_c3.time_input(
                        "Departure Time",
                        value=time.fromisoformat(str(selected_trip_to_edit["departure"] or "09:00")),
                        key=f"edit_trip_departure_{selected_trip_to_edit['id']}",
                    )
                    e_trip_arrival = st.time_input(
                        "Arrival Time",
                        value=time.fromisoformat(str(selected_trip_to_edit["arrival"] or "10:15")),
                        key=f"edit_trip_arrival_{selected_trip_to_edit['id']}",
                    )
                    save_trip_changes = st.form_submit_button(
                        "💾 Save Trip Changes",
                        width="stretch",
                    )

                if save_trip_changes:
                    e_trip_bus = e_trip_bus.strip()
                    if e_trip_route_id is None:
                        st.error("Please select a route.")
                    elif not e_trip_bus:
                        st.error("Bus number is required.")
                    elif e_trip_departure >= e_trip_arrival:
                        st.error("Departure time must be before arrival time.")
                    elif bus_number_exists(e_trip_bus, exclude_trip_id=selected_trip_to_edit["id"]):
                        st.error(f"Bus number '{e_trip_bus}' is already assigned to another trip.")
                    else:
                        departure_str = e_trip_departure.strftime("%H:%M")
                        arrival_str = e_trip_arrival.strftime("%H:%M")
                        trip_date_str = e_trip_date.isoformat()
                        has_conflict, conflict_message = check_bus_schedule_conflict(
                            e_trip_bus,
                            departure_str,
                            arrival_str,
                            trip_date_str,
                            exclude_trip_id=selected_trip_to_edit["id"],
                        )
                        if has_conflict:
                            st.error(f"Cannot update trip: Bus {e_trip_bus} has a {conflict_message}")
                        else:
                            update_trip(
                                selected_trip_to_edit["id"],
                                e_trip_route_id,
                                e_trip_bus,
                                trip_date_str,
                                departure_str,
                                arrival_str,
                            )
                            st.success("Scheduled trip updated successfully.")
                            st.rerun()

                st.divider()
                st.subheader("🗑️ Delete Scheduled Trip")
                trip_del_map = {f"Trip #{t['id']} (Bus {t['bus_number']} on Route {t['route_name']} • {t['departure']}-{t['arrival']})": t["id"] for t in trips_with_r}
                sel_del_label = st.selectbox("Select Trip to Remove", list(trip_del_map.keys()))
                sel_del_id = trip_del_map[sel_del_label]

                if st.button("🗑️ Delete Trip", use_container_width=True):
                    delete_trip(sel_del_id)
                    st.success("Trip removed.")
                    st.rerun()
            else:
                st.info("No trips scheduled. Use the 'Schedule New Trip' tab.")

        with tab_add_t:
            with st.container(border=True):
                st.subheader("➕ Schedule New Trip")
                with st.form("add_trip_form"):
                    r_choice_map = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r["id"] for r in routes}
                    t_r_label = st.selectbox("Select Route", list(r_choice_map.keys()) if r_choice_map else ["No routes"])
                    t_r_id = r_choice_map.get(t_r_label)

                    t_c1, t_c2, t_c3 = st.columns(3)
                    t_bus = t_c1.text_input("Bus Number", placeholder="e.g. AP09-B-1009")
                    t_date = t_c2.date_input("Trip Date", value=date.today())
                    t_dep = t_c3.time_input("Departure Time", value=time(9, 0))

                    t_arr_dep, t_arr_spacer = st.columns([1, 2])
                    t_arr = t_arr_dep.time_input("Arrival Time", value=time(10, 15))

                    t_submit = st.form_submit_button("🚀 Schedule Trip", use_container_width=True)

                if t_submit:
                    t_bus = t_bus.strip()
                    existing_bus_trip = next(
                        (
                            trip
                            for trip in trips_with_r
                            if str(trip.get("bus_number") or "").strip().casefold() == t_bus.casefold()
                        ),
                        None,
                    )
                    if not t_r_id:
                        st.error("Please select a route.")
                    elif not t_bus:
                        st.error("Bus number is required.")
                    elif existing_bus_trip:
                        st.error(
                            f"Conflict: Bus {t_bus} is already assigned to Trip #{existing_bus_trip['id']} "
                            f"on Route {existing_bus_trip.get('route_name') or 'Unknown'} "
                            f"({existing_bus_trip.get('trip_date') or 'date not set'}, "
                            f"{existing_bus_trip.get('departure')}–{existing_bus_trip.get('arrival')}). "
                            "Each bus number can only be assigned to one scheduled trip."
                        )
                    elif t_dep >= t_arr:
                        st.error("Departure time must be before arrival time.")
                    else:
                        dep_str = t_dep.strftime("%H:%M")
                        arr_str = t_arr.strftime("%H:%M")
                        date_str = t_date.isoformat()

                        has_conflict, conf_msg = check_bus_schedule_conflict(t_bus, dep_str, arr_str, date_str)
                        if has_conflict:
                            st.error(f"Cannot schedule trip: Bus {t_bus} has a {conf_msg}")
                        else:
                            try:
                                add_trip(t_r_id, t_bus, date_str, dep_str, arr_str)
                            except ValueError as error:
                                st.error(f"Cannot schedule trip: {error}")
                            else:
                                st.success(f"Trip scheduled for Bus {t_bus} on Route!")
                                st.rerun()


    # --------------------------------------------------------
    # 7. RIDERSHIP
    # --------------------------------------------------------
    elif page == "👥 Ridership":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">👥 Passenger Ridership & Revenue Analytics</div>
                <div class="app-hero-desc">Track historical passenger volume records, load factors, and distance-weighted ticket revenue.</div>
            </div>
        """, unsafe_allow_html=True)

        riders_with_t = get_ridership_with_trips()
        trips_with_r = get_trips_with_routes()
        analytics = get_route_ridership_analytics()

        if analytics:
            st.markdown("### 📊 Route Ridership & Revenue Summary")
            df_a = pd.DataFrame(analytics)
            
            # Add revenue calculation
            df_a["Avg Fare (₹)"] = df_a.apply(lambda row: max(10.0, round(float(row.get("base_fare") or 10.0) + (float(row.get("distance") or 10.0) * 0.7 * float(row.get("fare_per_km") or 2.5)))), axis=1)
            df_a["Total Revenue (₹)"] = df_a["total_passengers"] * df_a["Avg Fare (₹)"]
            
            display_cols = ["route_name", "source", "destination", "distance", "total_scheduled_trips", "total_passengers", "avg_daily_passengers", "Avg Fare (₹)", "Total Revenue (₹)"]
            st.dataframe(df_a[display_cols].rename(columns={
                "route_name": "Route",
                "source": "Origin",
                "destination": "Destination",
                "distance": "Distance (km)",
                "total_scheduled_trips": "Trips",
                "total_passengers": "Total Riders",
                "avg_daily_passengers": "Avg Daily Riders"
            }), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("➕ Log Passenger Count")
        with st.form("add_ridership_form"):
            t_choice_map = {f"Trip #{t['id']} (Bus {t['bus_number']} on Route {t['route_name']} • {t['departure']})": t["id"] for t in trips_with_r} if trips_with_r else {}
            sel_t_label = st.selectbox("Select Scheduled Trip", list(t_choice_map.keys()) if t_choice_map else ["No trips"])
            sel_t_id = t_choice_map.get(sel_t_label)

            rc1, rc2 = st.columns(2)
            r_date = rc1.date_input("Date", value=date.today())
            r_pass = rc2.number_input("Passenger Count", min_value=1, max_value=200, value=45)

            r_sub = st.form_submit_button("💾 Record Ridership", use_container_width=True)

        if r_sub:
            if not sel_t_id:
                st.error("Please select a trip.")
            else:
                add_ridership(sel_t_id, r_date.isoformat(), int(r_pass))
                st.success("Ridership record added.")
                st.rerun()


    # --------------------------------------------------------
    # 8. FREQUENCY PLANNER
    # --------------------------------------------------------
    elif page == "⚡ Frequency Planner":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">⚡ Route Frequency & Fleet Rebalancing Engine</div>
                <div class="app-hero-desc">Calculate optimal trip frequency per route to avoid overcrowding while reducing fuel consumption.</div>
            </div>
        """, unsafe_allow_html=True)

        analytics = get_route_ridership_analytics()

        if not analytics or not any(a["total_passengers"] > 0 for a in analytics):
            st.info("No ridership analytics available yet. Click '🌱 Populate Sample City Data' in the sidebar.")
        else:
            bus_cap = st.slider("Target Bus Passenger Capacity (Seats)", min_value=30, max_value=80, value=50, step=5)
            
            st.markdown("### 📊 Recommended Trips / Day Calculation")
            st.markdown(f"$$\\text{{Recommended Trips/Day}} = \\left\\lceil \\frac{{\\text{{Avg Daily Passengers}}}}{{{bus_cap}}} \\right\\rceil$$")

            plan_rows = []
            for a in analytics:
                avg_daily = float(a.get("avg_daily_passengers") or 0)
                current_trips = int(a.get("total_scheduled_trips") or 1)
                rec_trips = math.ceil(avg_daily / bus_cap) if avg_daily > 0 else current_trips
                delta = rec_trips - current_trips
                
                status = "🟢 Optimal" if delta == 0 else ("🔴 Need +" + str(delta) + " extra trips" if delta > 0 else "🟡 Can reduce " + str(abs(delta)) + " idle trips")

                plan_rows.append({
                    "Route": f"Route {a['route_name']}",
                    "Corridor": f"{a['source']} ➔ {a['destination']}",
                    "Avg Daily Passengers": avg_daily,
                    "Current Scheduled Trips": current_trips,
                    "Recommended Trips": rec_trips,
                    "Fleet Adjustment Status": status
                })

            st.dataframe(pd.DataFrame(plan_rows), use_container_width=True, hide_index=True)


    # --------------------------------------------------------
    # 9. SCHEDULE & CONFLICTS
    # --------------------------------------------------------
    elif page == "🗓️ Schedule & Conflicts":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🗓️ OOP Schedule Collision Detection Engine</div>
                <div class="app-hero-desc">Detect double-bookings or overlapping departure windows where the same bus is assigned to conflicting trips.</div>
            </div>
        """, unsafe_allow_html=True)

        all_trips_data = get_trips_with_routes()

        if not all_trips_data:
            st.info("No trips scheduled to evaluate.")
        else:
            scheduler = OOPScheduler()
            for t_row in all_trips_data:
                b_obj = OOPBus(registration_number=t_row["bus_number"], capacity=50)
                r_obj = OOPRoute(
                    name=t_row["route_name"],
                    origin=t_row["source"],
                    destination=t_row["destination"],
                    distance=float(t_row.get("distance") or 0),
                    base_fare=float(t_row.get("base_fare") or 10.0),
                    fare_per_km=float(t_row.get("fare_per_km") or 2.5)
                )
                trip_obj = OOPTrip(
                    trip_id=t_row["id"],
                    route=r_obj,
                    bus=b_obj,
                    trip_date=t_row["trip_date"] or date.today().isoformat(),
                    departure_time=t_row["departure"],
                    arrival_time=t_row["arrival"]
                )
                scheduler.add_trip(trip_obj)

            conflicts = scheduler.get_conflicts()

            if not conflicts:
                st.success("🟢 No schedule conflicts detected! All bus fleets and timetables are collision-free.")
            else:
                st.error(f"⚠️ Found {len(conflicts)} Schedule Conflict(s):")
                for c_pair in conflicts:
                    t1, t2 = c_pair
                    with st.container(border=True):
                        st.markdown(f"**Collision on Bus `{t1.bus.registration_number}` (Date: {t1.trip_date}):**")
                        st.markdown(f"• **Trip #{t1.trip_id}**: Route {t1.route.name} ({t1.departure_time} - {t1.arrival_time})")
                        st.markdown(f"• **Trip #{t2.trip_id}**: Route {t2.route.name} ({t2.departure_time} - {t2.arrival_time})")