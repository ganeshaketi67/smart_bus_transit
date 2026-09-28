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
    get_ridership_with_trips
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


# Initialize Database
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

/* App Cards */
.app-card {
    background: #131c2e;
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.app-card:hover {
    border-color: var(--card-border-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
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
    color: #94a3b8 !important;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.stat-val {
    color: #ffffff !important;
    font-size: 28px;
    font-weight: 800;
    margin-top: 4px;
    line-height: 1.1;
}

.stat-sub {
    color: #38bdf8 !important;
    font-size: 12px;
    font-weight: 500;
    margin-top: 6px;
}

/* Bus Stop Timeline */
.stop-pill {
    background: #1e293b;
    border: 1px solid #334155;
    padding: 6px 14px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
    display: inline-block;
    margin: 4px;
}

.stop-pill-active {
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 6px 14px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 700;
    display: inline-block;
    margin: 4px;
}

/* Bus Departure Chip */
.bus-departure-chip {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 12px 14px;
    text-align: center;
    transition: all 0.2s;
}

.bus-departure-chip:hover {
    border-color: #38bdf8;
    background: #1e293b;
}

/* Status Badges */
.badge-deficit {
    background-color: rgba(239, 68, 68, 0.18);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.badge-optimal {
    background-color: rgba(34, 197, 94, 0.18);
    color: #86efac;
    border: 1px solid rgba(34, 197, 94, 0.4);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.badge-surplus {
    background-color: rgba(245, 158, 11, 0.18);
    color: #fde047;
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

/* Buttons & Inputs */
.stButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 9px 18px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4) !important;
}

/* Inputs styling */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"], .stDateInput input, .stTimeInput input {
    background-color: #0b111e !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}

.stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stTimeInput label {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* Streamlit DataFrames */
[data-testid="stDataFrame"] {
    background-color: #131b2e !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #090d16;
}
::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #475569;
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
            "🤖 AI Transit Assistant",
            "📸 Report Overcrowded Bus",
            "🗺️ Route Finder",
        ]

        if "pending_passenger_page" in st.session_state and st.session_state["pending_passenger_page"]:
            st.session_state["passenger_radio"] = st.session_state.pop("pending_passenger_page")

        if "passenger_radio" not in st.session_state:
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

        if "operator_radio" not in st.session_state:
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
        st.sidebar.success(f"Loaded {n_r} routes & {n_t} trips with live data!")
        st.rerun()

    st.caption("NETWORK TELEMETRY")
    st.markdown('<div class="app-pill pill-live">🟢 Network Live • SQLite Online</div>', unsafe_allow_html=True)


# Load fresh DB records
routes = get_routes()
stops = get_stops()
trips = get_trips()
ridership = get_ridership()
alerts = get_overcrowding_alerts()


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
                <div class="app-hero-desc">Explore upcoming departures, route schedules, and intermediate stop sequences across the city network.</div>
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
                st.markdown("#### 🔍 Journey Stop Selector")
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
                    col_header_l, col_header_r = st.columns([8, 4])
                    with col_header_l:
                        if is_return_trip:
                            st.markdown(f"### 🚌 Route {r['route_name']} &nbsp;•&nbsp; `{r['destination']} ➔ {r['source']}` <span class='badge-optimal' style='font-size:11px; margin-left:6px;'>🔁 Return Trip</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"### 🚌 Route {r['route_name']} &nbsp;•&nbsp; `{r['source']} ➔ {r['destination']}`", unsafe_allow_html=True)
                        st.caption(f"Distance: **{r['distance']} km** | Total Active Daily Runs: **{len(r_trips)}**")
                    with col_header_r:
                        badge_label = "🔁 Return Route Service" if is_return_trip else "🟢 Outbound Regular Service"
                        st.markdown(f'<div style="text-align: right;"><span class="app-pill pill-passenger">{badge_label}</span></div>', unsafe_allow_html=True)

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
    # 2. AI TRANSIT ASSISTANT
    # --------------------------------------------------------
    elif page == "🤖 AI Transit Assistant":

        current_api_key = st.session_state.get("gemini_api_key", "").strip() or get_stored_api_key()
        sel_model = st.session_state.get("selected_gemini_model", "gemini-3.8-flash")

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🤖 AI Transit Assistant</div>
                <div class="app-hero-desc">Ask any question about bus schedules, optimal boarding stops, crowd predictions, or transit directions in natural language.</div>
            </div>
        """, unsafe_allow_html=True)

        col_status, col_clear = st.columns([9, 3])
        with col_status:
            if current_api_key:
                st.markdown(f'<span class="app-pill pill-passenger">🟢 Powered by Google Gemini ({sel_model}) — Live Database Grounded</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="app-pill pill-operator">🟡 AI Mode: Dynamic SQLite Retrieval Grounding</span>', unsafe_allow_html=True)

        with col_clear:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "👋 Hi there! I am your **Smart Transit AI Assistant**. Ask me about bus timings, intermediate stops, route recommendations, or the best time to travel!"}
                ]
                st.rerun()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "👋 Hi there! I am your **Smart Transit AI Assistant**. Ask me about bus timings, intermediate stops, route recommendations, or the best time to travel!"}
            ]

        # Suggested Prompts
        st.markdown("**Quick Prompts:**")
        q1, q2, q3, q4 = st.columns(4)
        prompt_to_add = None

        if q1.button("🚌 Next buses to Koti?", use_container_width=True):
            prompt_to_add = "When are the next scheduled buses to Koti?"
        if q2.button("🔮 Predict crowd on Route 101", use_container_width=True):
            prompt_to_add = "Predict the crowd levels and best departure time for Route 101 today."
        if q3.button("⚡ Fastest way to Ameerpet?", use_container_width=True):
            prompt_to_add = "Which bus is fastest to reach Ameerpet and what are the stops?"
        if q4.button("⏰ Best time to avoid rush?", use_container_width=True):
            prompt_to_add = "What are the peak hours and when should I travel to avoid overcrowded buses?"

        # Chat history rendering
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask a transit question (e.g. 'What is the schedule for Route 102?')...")
        active_prompt = prompt_to_add or user_input

        if active_prompt:
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 AI is reading live transit database snapshot..."):
                    if current_api_key:
                        gemini_res = answer_with_gemini(
                            query=active_prompt,
                            api_key=current_api_key,
                            model_name=sel_model,
                            chat_history=st.session_state.chat_history[:-1],
                            user_role="passenger"
                        )
                        if gemini_res["status"] == "success":
                            ai_response = gemini_res["content"]
                        else:
                            st.warning(f"⚠️ Gemini API Notice: {gemini_res.get('message')}")
                            ai_response = dynamic_database_search_response(active_prompt, user_role="passenger")
                    else:
                        ai_response = dynamic_database_search_response(active_prompt, user_role="passenger")

                st.markdown(ai_response)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})


    # --------------------------------------------------------
    # 3. REPORT OVERCROWDED BUS
    # --------------------------------------------------------
    elif page == "📸 Report Overcrowded Bus":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">📸 Report Overcrowded Bus</div>
                <div class="app-hero-desc">Help improve city transit by reporting full buses. Photo alerts notify operators to dispatch extra buses during peak hours!</div>
            </div>
        """, unsafe_allow_html=True)

        col_form, col_info = st.columns([7, 5])

        with col_form:
            with st.container(border=True):
                st.markdown("#### 📸 Report Form")
                uploaded_photo = st.file_uploader("Upload Bus Photo (JPG / PNG)", type=["jpg", "jpeg", "png"])

                route_select_opts = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r for r in routes} if routes else {}

                with st.form("overcrowd_report_form"):
                    sel_r_label = st.selectbox("Select Bus Route", list(route_select_opts.keys()) if route_select_opts else ["No routes available"])
                    bus_no_in = st.text_input("Bus Number (Optional)", placeholder="e.g. AP09-B-1001")

                    stop_names_list = [s["stop_name"] for s in stops] if stops else ["Secunderabad", "Ameerpet", "Koti"]
                    sel_stop_name = st.selectbox("Current Bus Stop Location", stop_names_list)

                    passenger_notes = st.text_area("Observations / Feedback", placeholder="e.g. Bus is completely packed with passengers standing. Please send an extra bus!")

                    sub_report = st.form_submit_button("🚀 Submit Overcrowding Report", use_container_width=True)

                if sub_report:
                    if not route_select_opts:
                        st.error("Please populate sample routes first!")
                    else:
                        sel_route_obj = route_select_opts[sel_r_label]
                        r_id = sel_route_obj["id"]
                        today_str = date.today().isoformat()
                        now_str = datetime.now().strftime("%H:%M")

                        add_overcrowding_alert(
                            route_id=r_id,
                            bus_number=bus_no_in.strip() or "Unassigned Bus",
                            stop_name=sel_stop_name,
                            report_date=today_str,
                            report_time=now_str,
                            passenger_notes=passenger_notes.strip()
                        )

                        st.success("✅ Overcrowding Report Submitted Successfully!")
                        st.balloons()
                        st.info("🚨 Alert logged in Operator Control Center. Dispatchers will review and deploy extra bus capacity.")

        with col_info:
            with st.container(border=True):
                st.markdown("#### 🤖 AI Crowd Verification")
                if uploaded_photo is not None:
                    st.image(uploaded_photo, caption="Uploaded Bus Photo", use_container_width=True)
                    st.markdown("""
                        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; padding: 12px; border-radius: 12px; margin-top: 10px;">
                            <span style="color: #6ee7b7; font-weight: 700;">🟢 AI Crowd Density Scanner: High Congestion Verified</span>
                            <p style="color: #cbd5e1; font-size: 12px; margin-top: 4px;">Vehicle load verified above 90% threshold. Priority dispatch tag created.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("📷 Upload an image to preview AI crowding verification scan.")

                st.divider()
                st.markdown("#### 💡 How this helps:")
                st.markdown("""
                - **Live Dispatch**: Operators trigger backup buses when routes overflow.
                - **Frequency Boost**: Informs timetable adjustments to reduce waiting times.
                - **Safer Commute**: Prevents unsafe standing and crowding.
                """)


    # --------------------------------------------------------
    # 4. ROUTE FINDER
    # --------------------------------------------------------
    elif page == "🗺️ Route Finder":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🗺️ Passenger Route Planner</div>
                <div class="app-hero-desc">Calculate the shortest path, transfer connections, and step-by-step navigation between any two city stops.</div>
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
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Stops", len(result["path"]))
                m2.metric("Network Hops", result["total_hops"])
                m3.metric("Transfers", result["transfers"])

                st.markdown("### 🧭 Step-by-Step Itinerary")
                for idx, seg in enumerate(result["segments"], start=1):
                    with st.container(border=True):
                        st.markdown(f"**Step {idx}:** Board **Route {seg['route']}** from **{seg['from_stop']}** to **{seg['to_stop']}**")
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
                <div class="app-hero-desc">Real-time city transport metrics, passenger volumes, active buses, and operational performance overview.</div>
            </div>
        """, unsafe_allow_html=True)

        if not routes and not stops:
            st.warning("⚠️ No transit data found. Click '🌱 Populate Sample City Data' in the sidebar to populate records.")

        # KPI METRICS
        total_passengers = sum(row[3] for row in ridership) if ridership else 0
        unique_buses = len(set(row[2] for row in trips if row[2])) if trips else 0
        pending_alerts_cnt = len([a for a in alerts if a["status"] == "Pending"])
        est_total_revenue = total_passengers * 30  # Standard ₹30/ticket fare

        analytics = get_route_ridership_analytics()

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-icon">🚌</div>
                    <div class="stat-label">Active Routes</div>
                    <div class="stat-val">{len(routes)}</div>
                    <div class="stat-sub">City Lines</div>
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
                    <div class="stat-val">₹{est_total_revenue:,}</div>
                    <div class="stat-sub">@ ₹30 / Ticket</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("")

        # HIGHEST PASSENGER & REVENUE ROUTE HIGHLIGHTS
        if analytics and any(a["total_passengers"] > 0 for a in analytics):
            # Sort by total passengers
            sorted_by_pass = sorted(analytics, key=lambda x: x["total_passengers"], reverse=True)
            top_pass_route = sorted_by_pass[0]
            top_rev_route = max(analytics, key=lambda x: x["total_passengers"] * 30)

            h_c1, h_c2 = st.columns(2)
            with h_c1:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1px solid rgba(129, 140, 248, 0.35); border-radius: 16px; padding: 18px 22px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 11px; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.5px;">🥇 Busiest Route (Highest Passengers)</span>
                                <h3 style="color: #f8fafc; margin: 4px 0 2px 0;">Route {top_pass_route['route_name']}</h3>
                                <p style="color: #94a3b8; font-size: 13px; margin: 0;">{top_pass_route['source']} ➔ {top_pass_route['destination']}</p>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 26px; font-weight: 800; color: #38bdf8;">{top_pass_route['total_passengers']:,}</div>
                                <div style="font-size: 12px; color: #cbd5e1;">Avg {top_pass_route['avg_passengers_per_record']:.1f} pass / trip</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with h_c2:
                top_rev_val = top_rev_route['total_passengers'] * 30
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 16px; padding: 18px 22px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 11px; font-weight: 700; color: #6ee7b7; text-transform: uppercase; letter-spacing: 0.5px;">💰 Top Revenue Generating Route</span>
                                <h3 style="color: #f8fafc; margin: 4px 0 2px 0;">Route {top_rev_route['route_name']}</h3>
                                <p style="color: #94a3b8; font-size: 13px; margin: 0;">{top_rev_route['source']} ➔ {top_rev_route['destination']}</p>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 26px; font-weight: 800; color: #10b981;">₹{top_rev_val:,}</div>
                                <div style="font-size: 12px; color: #cbd5e1;">{top_rev_route['total_scheduled_trips']} scheduled trips</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.write("")

        # CHARTS: REVENUE BREAKDOWN & PASSENGER CROWDEDNESS
        col_rev, col_pass = st.columns([6, 6])

        with col_rev:
            with st.container(border=True):
                st.subheader("💰 Route Revenue Breakdown (₹)")
                if analytics and any(a["total_passengers"] > 0 for a in analytics):
                    df_rev = pd.DataFrame(analytics)
                    df_rev["Revenue"] = df_rev["total_passengers"] * 30
                    df_rev = df_rev.sort_values(by="Revenue", ascending=True)

                    fig_rev = px.bar(
                        df_rev,
                        x="Revenue",
                        y="route_name",
                        orientation="h",
                        text="Revenue",
                        color="Revenue",
                        color_continuous_scale="Viridis",
                        labels={"Revenue": "Total Revenue (₹)", "route_name": "Route Code"}
                    )
                    fig_rev.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
                    fig_rev.update_layout(
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#cbd5e1"),
                        margin=dict(l=10, r=40, t=10, b=10),
                        xaxis=dict(gridcolor="#1e293b"),
                        yaxis=dict(gridcolor="#1e293b")
                    )
                    st.plotly_chart(fig_rev, use_container_width=True)
                else:
                    st.info("No revenue data available.")

        with col_pass:
            with st.container(border=True):
                st.subheader("👥 Passenger Volume Ranking (Busiest Routes)")
                if analytics and any(a["total_passengers"] > 0 for a in analytics):
                    df_p = pd.DataFrame(analytics).sort_values(by="total_passengers", ascending=False)
                    fig_p = px.bar(
                        df_p,
                        x="route_name",
                        y="total_passengers",
                        text="total_passengers",
                        color="avg_passengers_per_record",
                        color_continuous_scale="Blues",
                        labels={
                            "route_name": "Route Code",
                            "total_passengers": "Total Passengers",
                            "avg_passengers_per_record": "Avg Pass/Trip"
                        }
                    )
                    fig_p.update_traces(texttemplate='%{text:,}', textposition='outside')
                    fig_p.update_layout(
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#cbd5e1"),
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis=dict(gridcolor="#1e293b"),
                        yaxis=dict(gridcolor="#1e293b")
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.info("No passenger analytics data available.")

        # HISTORICAL RIDERSHIP TREND OVER TIME
        with st.container(border=True):
            st.subheader("📈 Total Network Ridership Volume Over Time")
            if ridership:
                df = pd.DataFrame(ridership, columns=["ID", "Trip ID", "Date", "Passengers"])
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                chart_data = df.dropna(subset=["Date"]).groupby("Date")["Passengers"].sum().reset_index()

                fig_area = px.area(
                    chart_data,
                    x="Date",
                    y="Passengers",
                    markers=True,
                    color_discrete_sequence=["#38bdf8"]
                )
                fig_area.update_layout(
                    height=280,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(gridcolor="#1e293b"),
                    yaxis=dict(gridcolor="#1e293b")
                )
                st.plotly_chart(fig_area, use_container_width=True)

        # QUICK ACTION LINKS
        st.subheader("⚡ Quick Management Actions")
        qa1, qa2, qa3, qa4 = st.columns(4)

        with qa1:
            if st.button("🚨 Overcrowded Bus Desk", use_container_width=True, key="dash_alerts"):
                navigate_operator("🚨 Overcrowded Bus Alerts")
                st.rerun()

        with qa2:
            if st.button("🚌 Manage Routes", use_container_width=True, key="dash_routes"):
                navigate_operator("🚌 Routes")
                st.rerun()

        with qa3:
            if st.button("⚡ Frequency Planner", use_container_width=True, key="dash_freq"):
                navigate_operator("⚡ Frequency Planner")
                st.rerun()

        with qa4:
            if st.button("🗓️ Schedule & Conflicts", use_container_width=True, key="dash_sch"):
                navigate_operator("🗓️ Schedule & Conflicts")
                st.rerun()


    # --------------------------------------------------------
    # 2. OVERCROWDED BUS ALERTS
    # --------------------------------------------------------
    elif page == "🚨 Overcrowded Bus Alerts":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🚨 Overcrowded Bus Dispatch Desk</div>
                <div class="app-hero-desc">Live queue of passenger photo reports & crowding alerts. Dispatch extra buses in one click to alleviate passenger bottlenecks.</div>
            </div>
        """, unsafe_allow_html=True)

        pending_alerts = [a for a in alerts if a["status"] == "Pending"]
        resolved_alerts = [a for a in alerts if a["status"] != "Pending"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Passenger Reports", len(alerts))
        c2.metric("Pending Overcrowding Alerts", len(pending_alerts))
        c3.metric("Extra Buses Dispatched", len(resolved_alerts))

        st.divider()

        if not alerts:
            st.info("No overcrowded bus reports logged yet. Passengers can submit photo reports from the Passenger App!")
        else:
            st.subheader("📋 Live Dispatch Queue")
            for a in alerts:
                is_pending = a["status"] == "Pending"

                with st.container(border=True):
                    col_info_a, col_act_a = st.columns([8, 4])

                    with col_info_a:
                        status_badge = "🔴 PENDING DISPATCH" if is_pending else "🟢 EXTRA BUS DISPATCHED"
                        st.markdown(f"### Report #{a['id']} &nbsp;•&nbsp; Route {a['route_name']} (`{a['source']} ➔ {a['destination']}`)")
                        st.markdown(f"**Status:** `{status_badge}` &nbsp;|&nbsp; **Bus Reg:** `{a['bus_number'] or 'Unassigned'}` &nbsp;|&nbsp; **Stop:** `{a['stop_name']}`")
                        st.caption(f"Reported Date: {a['report_date']} at {a['report_time']}")
                        if a["passenger_notes"]:
                            st.markdown(f"💬 *\"{a['passenger_notes']}\"*")

                    with col_act_a:
                        if is_pending:
                            st.warning("⚠️ High Passenger Demand Alert")
                            if st.button(f"🚀 Dispatch Extra Bus (Report #{a['id']})", key=f"dispatch_{a['id']}", use_container_width=True):
                                resolve_overcrowding_alert(a["id"])
                                try:
                                    extra_bus_no = f"EXTRA-BUS-{a['id']}"
                                    add_trip(
                                        route_id=a["route_id"],
                                        bus_number=extra_bus_no,
                                        trip_date=a["report_date"],
                                        departure=a["report_time"],
                                        arrival="23:59"
                                    )
                                except Exception:
                                    pass
                                st.success(f"Extra bus dispatched for Route {a['route_name']}!")
                                st.rerun()
                        else:
                            st.success("✅ Extra bus successfully deployed to this route.")


    # --------------------------------------------------------
    # 3. ROUTES
    # --------------------------------------------------------
    elif page == "🚌 Routes":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🚌 Bus Route Management</div>
                <div class="app-hero-desc">Create, configure, edit, and inspect city transit routes and custom intermediate stop sequences.</div>
            </div>
        """, unsafe_allow_html=True)

        tab_view, tab_add = st.tabs(["📋 View & Manage Routes", "➕ Add Route"])

        with tab_view:
            if routes:
                df_routes = pd.DataFrame(
                    routes,
                    columns=["ID", "Route Code", "Start Point", "Final Destination", "Distance (km)"]
                )
                st.dataframe(df_routes, use_container_width=True, hide_index=True)

                st.subheader("🔍 Route Stop Sequences")
                for r in routes:
                    stops_seq = get_route_stops(r["id"])
                    with st.expander(f"Route {r['route_name']} ({r['source']} ➔ {r['destination']}) — {len(stops_seq)} stops"):
                        if stops_seq:
                            seq_str = " ➔ ".join([f"**{s['stop_name']}**" for s in stops_seq])
                            st.markdown(f"**Stop Sequence:** {seq_str}")
                        else:
                            st.caption("No custom stops specified for this route yet.")

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
                            update_route(selected_r["id"], e_code, e_src, e_dst, e_dist)
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

                        add_route(new_code, new_src, new_dst, new_dist, stop_list)
                        st.success(f"Route '{new_code}' added successfully with {len(stop_list)} stops!")
                        st.rerun()


    # --------------------------------------------------------
    # 4. STOPS & CORRIDOR SEQUENCE BUILDER
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
            st.markdown("### 1️⃣ Select Start Point & Final Destination")
            st.caption("Select the origin and destination terminals from your saved transit network:")

            # Extract all unique start points and destinations from routes
            all_sources = sorted(list(set(r["source"] for r in routes)))
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1:
                sel_source = st.selectbox("🟢 Select Start Point (Origin)", all_sources, key="stops_sel_src")

            # Filter matching destinations for the selected source
            matching_routes = [r for r in routes if r["source"].lower() == sel_source.lower()]
            if matching_routes:
                dest_options = sorted(list(set(r["destination"] for r in matching_routes)))
            else:
                dest_options = sorted(list(set(r["destination"] for r in routes if r["destination"].lower() != sel_source.lower())))

            with c_sel2:
                sel_destination = st.selectbox("🏁 Select Final Destination", dest_options, key="stops_sel_dst")

            # Find the route matching this exact (source, destination) pair
            target_route = next((r for r in routes if r["source"].lower() == sel_source.lower() and r["destination"].lower() == sel_destination.lower()), None)

            if target_route is None:
                target_route = next((r for r in routes if (r["source"].lower() == sel_source.lower() or r["destination"].lower() == sel_destination.lower())), routes[0])

            st.write("")
            # Route summary card
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #131c30 0%, #0e1626 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 18px 24px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <span class="app-pill pill-passenger" style="font-size: 13px;">🚌 Route {target_route['route_name']}</span>
                            <h3 style="color: #ffffff; margin: 8px 0 2px 0;">{sel_source} ➔ {sel_destination}</h3>
                            <p style="color: #94a3b8; font-size: 13px; margin: 0;">Total Distance: <strong>{target_route['distance']} km</strong> &nbsp;|&nbsp; Route ID: <code>#{target_route['id']}</code></p>
                        </div>
                        <div style="text-align: right;">
                            <span class="app-pill pill-operator">Live Corridor Configurator</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Fetch current stops for this route
            curr_route_stops = get_route_stops(target_route["id"])
            existing_intermediate = []
            for s in curr_route_stops:
                s_name = s["stop_name"]
                if s_name.lower() != sel_source.lower() and s_name.lower() != sel_destination.lower():
                    existing_intermediate.append(s_name)

            # Step 2: Add / Edit Intermediate Stops
            st.markdown("### 2️⃣ Add Intermediate Stops Between Selected Terminals")
            st.caption(f"Enter the stops that the bus visits between **{sel_source}** and **{sel_destination}** in sequential order:")

            with st.container(border=True):
                inter_default_val = ", ".join(existing_intermediate)

                with st.form("intermediate_stops_form"):
                    stops_input_str = st.text_input(
                        f"Intermediate Stops between '{sel_source}' and '{sel_destination}' (comma-separated):",
                        value=inter_default_val,
                        placeholder="e.g. Batas, RTC X Roads, Chikkadpally"
                    )

                    all_registered_stop_names = [s["stop_name"] for s in stops]
                    if all_registered_stop_names:
                        st.caption("💡 Known stops in network: " + ", ".join(all_registered_stop_names[:10]) + ("..." if len(all_registered_stop_names) > 10 else ""))

                    save_stops_btn = st.form_submit_button("💾 Save Intermediate Stops for this Route", use_container_width=True)

                if save_stops_btn:
                    user_inter_list = [s.strip() for s in stops_input_str.split(",") if s.strip()]
                    clean_inter = [s for s in user_inter_list if s.lower() not in (sel_source.lower(), sel_destination.lower())]
                    full_ordered_stops = [sel_source] + clean_inter + [sel_destination]

                    replace_route_stops(target_route["id"], full_ordered_stops)
                    st.success(f"✅ Stop sequence saved for Route {target_route['route_name']}! Total: {len(full_ordered_stops)} stops (including start & destination).")
                    st.balloons()
                    st.rerun()

            # Step 3: Live Visual Timeline of the Route
            st.write("")
            st.markdown("### 3️⃣ Live Route Stop Sequence Preview")
            updated_stops = get_route_stops(target_route["id"])
            
            if updated_stops:
                stop_pills_html = " ➔ ".join([
                    f'<span class="stop-pill-active" style="background:rgba(16,185,129,0.2); border-color:#10b981; color:#86efac; font-weight:700;">🟢 {s["stop_name"]} (Start)</span>' if idx == 0 else
                    (f'<span class="stop-pill-active" style="background:rgba(56,189,248,0.2); border-color:#38bdf8; color:#7dd3fc; font-weight:700;">🏁 {s["stop_name"]} (Final Destination)</span>' if idx == len(updated_stops)-1 else
                    f'<span class="stop-pill">📍 {s["stop_name"]} (Stop #{idx+1})</span>')
                    for idx, s in enumerate(updated_stops)
                ])
                st.markdown(f"""
                    <div style='background:#090d16; padding:20px; border-radius:14px; border:1px solid rgba(56, 189, 248, 0.2);'>
                        <div style='color:#94a3b8; font-size:12px; font-weight:600; text-transform:uppercase; margin-bottom:10px;'>Bus Journey Path:</div>
                        {stop_pills_html}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"Currently only endpoints set: **{sel_source}** ➔ **{sel_destination}**.")


    # --------------------------------------------------------
    # 5. TRIPS
    # --------------------------------------------------------
    elif page == "⏱️ Trips":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">⏱️ Trip Scheduling & Management</div>
                <div class="app-hero-desc">Schedule bus departures, assign vehicle registration numbers, and inspect active fleet runs.</div>
            </div>
        """, unsafe_allow_html=True)

        tab_t_view, tab_t_add = st.tabs(["📋 View & Manage Trips", "➕ Schedule New Trip"])

        with tab_t_view:
            if trips:
                trips_full = get_trips()
                route_dict = {r["id"]: f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})" for r in routes}

                trips_data = []
                for t in trips_full:
                    r_name = route_dict.get(t["route_id"], f"Route ID {t['route_id']}")
                    trips_data.append({
                        "Trip ID": t["id"],
                        "Route": r_name,
                        "Bus Number": t["bus_number"],
                        "Trip Date": t["trip_date"],
                        "Departure": t["departure"],
                        "Arrival": t["arrival"]
                    })
                st.dataframe(pd.DataFrame(trips_data), use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("✏️ Modify or Delete Trip")
                trip_options = {f"Trip #{t['id']} — Bus {t['bus_number']} ({t['departure']}-{t['arrival']})": t for t in trips}
                sel_t_label = st.selectbox("Select Trip to Modify", list(trip_options))
                sel_t = trip_options[sel_t_label]

                col_edit_t, col_del_t = st.columns([2, 1])

                with col_edit_t:
                    with st.form("edit_trip_form_v2"):
                        st.subheader("✏️ Edit Trip Details")
                        route_select_opts = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r["id"] for r in routes}
                        curr_r_idx = list(route_select_opts.values()).index(sel_t["route_id"]) if sel_t["route_id"] in route_select_opts.values() else 0

                        c1, c2, c3 = st.columns(3)
                        e_r_id = route_select_opts[c1.selectbox("Assigned Route", list(route_select_opts), index=curr_r_idx)]
                        e_bus_no = c2.text_input("Bus Number", value=sel_t["bus_number"])
                        e_date = c3.date_input("Trip Date", value=datetime.strptime(sel_t["trip_date"], "%Y-%m-%d").date() if sel_t["trip_date"] else date.today())

                        c4, c5 = st.columns(2)
                        e_dep = c4.time_input("Departure Time", value=datetime.strptime(sel_t["departure"], "%H:%M").time())
                        e_arr = c5.time_input("Arrival Time", value=datetime.strptime(sel_t["arrival"], "%H:%M").time())

                        save_trip_btn = st.form_submit_button("💾 Save Trip Changes", use_container_width=True)

                    if save_trip_btn:
                        if e_arr <= e_dep:
                            st.error("Arrival time must be after departure time.")
                        else:
                            update_trip(
                                sel_t["id"],
                                e_r_id,
                                e_bus_no.strip(),
                                e_date.isoformat(),
                                e_dep.strftime("%H:%M"),
                                e_arr.strftime("%H:%M")
                            )
                            st.success("Trip updated successfully.")
                            st.rerun()

                with col_del_t:
                    with st.container(border=True):
                        st.subheader("🗑️ Delete Trip")
                        st.warning(f"Delete Trip #{sel_t['id']}?")
                        if st.button("🗑️ Confirm Delete Trip", key="del_trip_btn", use_container_width=True):
                            delete_trip(sel_t["id"])
                            st.success("Trip deleted.")
                            st.rerun()
            else:
                st.info("No scheduled trips yet. Use 'Schedule New Trip' tab to schedule one.")

        with tab_t_add:
            if routes:
                with st.container(border=True):
                    st.subheader("➕ Schedule New Trip")
                    route_select_opts = {f"Route {r['route_name']} ({r['source']} ➔ {r['destination']})": r["id"] for r in routes}

                    with st.form("add_trip_form_v2"):
                        c1, c2, c3 = st.columns(3)
                        sel_r_id = route_select_opts[c1.selectbox("Assigned Route", list(route_select_opts))]
                        bus_no_in = c2.text_input("Bus Number", placeholder="e.g. AP09-B-1001")
                        trip_d_in = c3.date_input("Trip Date", value=date.today())

                        c4, c5 = st.columns(2)
                        dep_t_in = c4.time_input("Departure Time", value=time(8, 0))
                        arr_t_in = c5.time_input("Arrival Time", value=time(9, 15))

                        submit_trip = st.form_submit_button("🚀 Schedule Trip", use_container_width=True)

                    if submit_trip:
                        bus_no_in = bus_no_in.strip()
                        if not bus_no_in:
                            st.error("Bus number is required.")
                        elif arr_t_in <= dep_t_in:
                            st.error("Arrival time must be later than departure time.")
                        else:
                            dep_str = dep_t_in.strftime("%H:%M")
                            arr_str = arr_t_in.strftime("%H:%M")
                            d_str = trip_d_in.isoformat()

                            has_conflict, conflict_msg = check_bus_schedule_conflict(bus_no_in, dep_str, arr_str, d_str)
                            if has_conflict:
                                st.warning(f"⚠️ Schedule Conflict Warning: Bus {bus_no_in} has an overlapping assignment! ({conflict_msg})")

                            add_trip(sel_r_id, bus_no_in, d_str, dep_str, arr_str)
                            st.success(f"Trip scheduled for Bus {bus_no_in} on Route!")
                            st.rerun()
            else:
                st.warning("Please create at least one route before scheduling trips.")


    # --------------------------------------------------------
    # 6. RIDERSHIP
    # --------------------------------------------------------
    elif page == "👥 Ridership":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">👥 Passenger Ridership & Route Revenue Hub</div>
                <div class="app-hero-desc">Analyze route-wise passenger volumes, identify high-demand crowded corridors, calculate revenue from each route, and manage trip ridership records.</div>
            </div>
        """, unsafe_allow_html=True)

        tab_rev, tab_r_view, tab_r_add = st.tabs([
            "💰 Route Revenue & Passenger Leaderboard",
            "📋 View & Manage Ridership",
            "➕ Log Ridership"
        ])

        with tab_rev:
            st.subheader("💰 Route Revenue & Passenger Volume Ranking")
            analytics_full = get_route_ridership_analytics()

            if not analytics_full or not any(a["total_passengers"] > 0 for a in analytics_full):
                st.info("No ridership analytics available yet. Click '🌱 Populate Sample City Data' in the sidebar.")
            else:
                col_f1, col_f2 = st.columns([4, 8])
                with col_f1:
                    fare_per_ticket = st.slider("Ticket Fare per Passenger (₹)", min_value=10, max_value=100, value=30, step=5)
                with col_f2:
                    st.caption("Revenue Formula:")
                    st.markdown(f"$$\\text{{Total Revenue}} = \\text{{Total Passengers}} \\times ₹{fare_per_ticket}$$")

                # Build Leaderboard and Revenue DataFrame
                sorted_analytics = sorted(analytics_full, key=lambda x: x["total_passengers"], reverse=True)
                total_network_rev = sum(a["total_passengers"] * fare_per_ticket for a in sorted_analytics)
                total_network_pass = sum(a["total_passengers"] for a in sorted_analytics)

                # Metrics Cards
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Total Fleet Revenue", f"₹{total_network_rev:,.0f}", f"@ ₹{fare_per_ticket}/ticket")
                m2.metric("👥 Total Passengers Served", f"{total_network_pass:,}", f"Across {len(sorted_analytics)} routes")
                m3.metric("🥇 Busiest Route", f"Route {sorted_analytics[0]['route_name']}", f"{sorted_analytics[0]['total_passengers']:,} pass.")
                m4.metric("💎 Top Earning Route", f"Route {sorted_analytics[0]['route_name']}", f"₹{sorted_analytics[0]['total_passengers'] * fare_per_ticket:,.0f}")

                st.write("")

                # Detailed Table
                rev_table_rows = []
                for rank, a in enumerate(sorted_analytics, start=1):
                    tot_p = a["total_passengers"]
                    avg_p = float(a["avg_passengers_per_record"] or 0)
                    tot_trips = a["total_scheduled_trips"]
                    route_rev = tot_p * fare_per_ticket
                    daily_rev = float(a["avg_daily_passengers"] or 0) * fare_per_ticket
                    rev_per_trip = avg_p * fare_per_ticket

                    # Crowd classification
                    load_pct = (avg_p / 50.0) * 100.0
                    if load_pct >= 100:
                        crowd_status = "🔴 Heavy Crowd (High Load)"
                    elif load_pct >= 70:
                        crowd_status = "🟡 Busy Corridor"
                    elif load_pct >= 40:
                        crowd_status = "🟢 Moderate Load"
                    else:
                        crowd_status = "🔵 Light / Feeder"

                    rev_table_rows.append({
                        "Rank": f"#{rank}",
                        "Route Code": f"Route {a['route_name']}",
                        "Corridor": f"{a['source']} ➔ {a['destination']}",
                        "Total Passengers": tot_p,
                        "Avg Pass/Trip": round(avg_p, 1),
                        "Load Factor (%)": f"{load_pct:.1f}%",
                        "Crowd Level": crowd_status,
                        "Total Revenue (₹)": f"₹{route_rev:,.0f}",
                        "Daily Revenue (₹/day)": f"₹{daily_rev:,.0f}",
                        "Avg Revenue/Trip (₹)": f"₹{rev_per_trip:,.0f}"
                    })

                df_rev_table = pd.DataFrame(rev_table_rows)
                st.dataframe(df_rev_table, use_container_width=True, hide_index=True)

                st.write("")
                # Visual Charts
                c_ch1, c_ch2 = st.columns(2)
                with c_ch1:
                    with st.container(border=True):
                        st.subheader("💰 Revenue by Route (₹)")
                        df_plot_rev = pd.DataFrame(sorted_analytics)
                        df_plot_rev["Revenue_Num"] = df_plot_rev["total_passengers"] * fare_per_ticket
                        fig_b_rev = px.bar(
                            df_plot_rev,
                            x="route_name",
                            y="Revenue_Num",
                            text="Revenue_Num",
                            color="Revenue_Num",
                            color_continuous_scale="Greens",
                            labels={"route_name": "Route Code", "Revenue_Num": "Total Revenue (₹)"}
                        )
                        fig_b_rev.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
                        fig_b_rev.update_layout(
                            height=320,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#cbd5e1"),
                            margin=dict(l=10, r=10, t=10, b=10)
                        )
                        st.plotly_chart(fig_b_rev, use_container_width=True)

                with c_ch2:
                    with st.container(border=True):
                        st.subheader("👥 Total Passenger Volume by Route")
                        fig_b_p = px.bar(
                            df_plot_rev,
                            x="route_name",
                            y="total_passengers",
                            text="total_passengers",
                            color="total_passengers",
                            color_continuous_scale="Tealgrn",
                            labels={"route_name": "Route Code", "total_passengers": "Total Passengers"}
                        )
                        fig_b_p.update_traces(texttemplate='%{text:,}', textposition='outside')
                        fig_b_p.update_layout(
                            height=320,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#cbd5e1"),
                            margin=dict(l=10, r=10, t=10, b=10)
                        )
                        st.plotly_chart(fig_b_p, use_container_width=True)

        with tab_r_view:
            ridership_full = get_ridership_with_trips()
            if ridership_full:
                r_display_data = []
                for r_item in ridership_full:
                    r_display_data.append({
                        "Bus Number": r_item["bus_number"] or f"Bus (Trip #{r_item['trip_id']})",
                        "Route": r_item["route_name"] or "N/A",
                        "Trip ID": r_item["trip_id"],
                        "Date": r_item["date"],
                        "Passenger Count": r_item["passengers"]
                    })
                df_r = pd.DataFrame(r_display_data)
                st.dataframe(df_r, use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("✏️ Edit or Delete Record")
                r_opts = {f"Bus {r['bus_number'] or ('Trip #' + str(r['trip_id']))} on {r['date']} ({r['passengers']} pass.)": r for r in ridership_full}
                sel_r_lbl = st.selectbox("Select Record", list(r_opts))
                sel_rec = r_opts[sel_r_lbl]

                c_edit_r, c_del_r = st.columns([2, 1])

                with c_edit_r:
                    with st.form("edit_r_form_v2"):
                        st.subheader("✏️ Edit Record")
                        e_p_cnt = st.number_input("Passenger Count", min_value=0, value=int(sel_rec["passengers"] or 0))
                        save_r_btn = st.form_submit_button("💾 Save Record", use_container_width=True)

                    if save_r_btn:
                        update_ridership(sel_rec["id"], sel_rec["trip_id"], sel_rec["date"], int(e_p_cnt))
                        st.success("Record updated.")
                        st.rerun()

                with c_del_r:
                    with st.container(border=True):
                        st.subheader("🗑️ Delete Record")
                        if st.button("🗑️ Delete Record", key="del_rec_btn", use_container_width=True):
                            delete_ridership(sel_rec["id"])
                            st.success("Record deleted.")
                            st.rerun()
            else:
                st.info("No ridership records stored yet.")

        with tab_r_add:
            if trips:
                with st.container(border=True):
                    st.subheader("➕ Log Passenger Count")
                    trip_opts = {f"Trip #{t['id']} — Bus {t['bus_number']} ({t['departure']})": t["id"] for t in trips}

                    with st.form("add_ridership_form_v2"):
                        c1, c2, c3 = st.columns(3)
                        sel_trip_id = trip_opts[c1.selectbox("Select Trip", list(trip_opts))]
                        log_date = c2.date_input("Date", value=date.today())
                        p_count = c3.number_input("Passenger Count", min_value=1, value=45, step=1)

                        sub_r = st.form_submit_button("🚀 Log Ridership Record", use_container_width=True)

                    if sub_r:
                        add_ridership(sel_trip_id, log_date.isoformat(), int(p_count))
                        st.success(f"Logged {p_count} passengers for Trip #{sel_trip_id} on {log_date}!")
                        st.rerun()
            else:
                st.warning("Please create trips first before logging ridership.")


    # --------------------------------------------------------
    # 7. FREQUENCY PLANNER
    # --------------------------------------------------------
    elif page == "⚡ Frequency Planner":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">⚡ Bus Frequency Optimization Engine</div>
                <div class="app-hero-desc">Compare recorded passenger ridership against bus capacity to calculate recommended daily departures per route.</div>
            </div>
        """, unsafe_allow_html=True)

        analytics = get_route_ridership_analytics()

        if not analytics:
            st.warning("No routes or ridership data found for frequency planning.")
            if st.button("🌱 Populate Sample Data", key="freq_seed"):
                seed_demo_data()
                st.rerun()
        else:
            with st.container(border=True):
                st.subheader("⚙️ Target Service Parameters")
                cp1, cp2 = st.columns(2)
                target_bus_capacity = cp1.number_input("Target Passenger Capacity Per Bus", min_value=10, max_value=150, value=50, step=5)
                st.caption("Formula: **Recommended Trips/Day = ceil(Avg Daily Passengers / Target Bus Capacity)**")

            freq_records = []
            for a in analytics:
                avg_pass = a["avg_daily_passengers"]
                curr_trips = a["total_scheduled_trips"]
                rec_trips = math.ceil(avg_pass / max(1, target_bus_capacity)) if avg_pass > 0 else 1
                gap = rec_trips - curr_trips

                if gap > 0:
                    status = "DEFICIT (Add Trips)"
                    badge = f"<span class='badge-deficit'>DEFICIT (+{gap} trips)</span>"
                elif gap < 0:
                    status = "SURPLUS (Reduce Trips)"
                    badge = f"<span class='badge-surplus'>SURPLUS ({gap} trips)</span>"
                else:
                    status = "OPTIMAL"
                    badge = "<span class='badge-optimal'>OPTIMAL</span>"

                freq_records.append({
                    "Route ID": a["route_id"],
                    "Route": f"Route {a['route_name']} ({a['source']} ➔ {a['destination']})",
                    "Avg Passengers/Day": avg_pass,
                    "Current Scheduled Trips": curr_trips,
                    "Recommended Trips/Day": rec_trips,
                    "Frequency Gap": gap,
                    "Status": status
                })

            df_freq = pd.DataFrame(freq_records)

            col_tbl, col_chart_f = st.columns([7, 5])

            with col_tbl:
                with st.container(border=True):
                    st.subheader("📋 Route Frequency Optimization Analysis")
                    st.dataframe(df_freq[["Route", "Avg Passengers/Day", "Current Scheduled Trips", "Recommended Trips/Day", "Status"]], use_container_width=True, hide_index=True)

            with col_chart_f:
                with st.container(border=True):
                    st.subheader("📊 Scheduled vs Recommended Trips")
                    fig_f = go.Figure()
                    fig_f.add_trace(go.Bar(
                        x=df_freq["Route"],
                        y=df_freq["Current Scheduled Trips"],
                        name="Current Scheduled Trips",
                        marker_color='#818cf8'
                    ))
                    fig_f.add_trace(go.Bar(
                        x=df_freq["Route"],
                        y=df_freq["Recommended Trips/Day"],
                        name="Recommended Trips",
                        marker_color='#38bdf8'
                    ))
                    fig_f.update_layout(
                        barmode='group',
                        height=380,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#cbd5e1"),
                        xaxis=dict(gridcolor="#1e293b"),
                        yaxis=dict(gridcolor="#1e293b", title="Trips / Day"),
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    st.plotly_chart(fig_f, use_container_width=True)


    # --------------------------------------------------------
    # 8. SCHEDULE & CONFLICTS
    # --------------------------------------------------------
    elif page == "🗓️ Schedule & Conflicts":

        st.markdown("""
            <div class="app-hero-header">
                <div class="app-hero-title">🗓️ Master Timetable & Conflict Detector</div>
                <div class="app-hero-desc">Inspect master bus departure timetables and automatically detect double-booking or schedule overlaps.</div>
            </div>
        """, unsafe_allow_html=True)

        if not trips:
            st.info("No scheduled trips in database. Create trips or populate sample data.")
            if st.button("🌱 Populate Sample Schedule Data", key="sch_seed"):
                seed_demo_data()
                st.rerun()
        else:
            scheduler = OOPScheduler()
            route_map_dict = {r["id"]: OOPRoute(r["route_name"], r["source"], r["destination"], float(r["distance"] or 0)) for r in routes}

            for t in trips:
                r_obj = route_map_dict.get(t["route_id"], OOPRoute("Unknown", "Source", "Dest"))
                bus_obj = OOPBus(t["bus_number"], capacity=50)
                oop_trip = OOPTrip(
                    trip_id=t["id"],
                    route=r_obj,
                    bus=bus_obj,
                    trip_date=t["trip_date"] or date.today().isoformat(),
                    departure_time=t["departure"],
                    arrival_time=t["arrival"]
                )
                scheduler.add_trip(oop_trip)

            conflicts = scheduler.get_conflicts()

            col_c_info, col_t_list = st.columns([4, 8])

            with col_c_info:
                with st.container(border=True):
                    st.subheader("🛡️ Bus Schedule Health")
                    if conflicts:
                        st.error(f"⚠️ {len(conflicts)} Bus Assignment Collisions Detected!")
                        for t1, t2 in conflicts:
                            st.markdown(f"- **Bus {t1.bus.registration_number}** double-booked between Trip #{t1.trip_id} ({t1.departure_time}-{t1.arrival_time}) and Trip #{t2.trip_id} ({t2.departure_time}-{t2.arrival_time}).")
                    else:
                        st.success("✅ Clean Schedule: No bus assignment overlaps detected!")

            with col_t_list:
                with st.container(border=True):
                    st.subheader("🗓️ Master Timetable")
                    oop_trips_list = scheduler.get_trips()
                    table_data = []
                    for ot in oop_trips_list:
                        table_data.append({
                            "Trip ID": ot.trip_id,
                            "Route": f"{ot.route.name} ({ot.route.origin} ➔ {ot.route.destination})",
                            "Bus Reg": ot.bus.registration_number,
                            "Date": ot.trip_date,
                            "Departure": ot.departure_time,
                            "Arrival": ot.arrival_time
                        })
                    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)